import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
import uuid

from app.services.contacts.personalization_service import PersonalizationService, PersonalizationServiceError
from app.models.contact import Contact
from app.models.email.staging import StagingSnapshot

class TestPersonalizationService(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.db_mock = MagicMock(spec=Session)
        self.service = PersonalizationService(self.db_mock)
        
    def test_escape_html(self):
        """Test HTML escaping"""
        self.assertEqual(self.service.escape_html("<script>alert('test')</script>"), 
                        "&lt;script&gt;alert(&#x27;test&#x27;)&lt;/script&gt;")
        self.assertEqual(self.service.escape_html("Normal text"), "Normal text")
        self.assertEqual(self.service.escape_html(None), "")
        
    def test_parse_template_variable(self):
        """Test template variable parsing"""
        # Test simple variable
        var_name, default_val = self.service.parse_template_variable("{{first_name}}")
        self.assertEqual(var_name, "first_name")
        self.assertEqual(default_val, "")
        
        # Test variable with default
        var_name, default_val = self.service.parse_template_variable("{{first_name | default: \"there\"}}")
        self.assertEqual(var_name, "first_name")
        self.assertEqual(default_val, "there")
        
        # Test variable with spaces
        var_name, default_val = self.service.parse_template_variable("{{  last_name  |  default:  \"user\"  }}")
        self.assertEqual(var_name, "last_name")
        self.assertEqual(default_val, "user")
        
    def test_extract_template_variables(self):
        """Test extracting template variables from content"""
        html_content = "<p>Hello {{first_name}},</p><p>Welcome to {{event_name | default: \"our event\"}}!</p>"
        variables = self.service.extract_template_variables(html_content)
        
        # Should find both variables
        self.assertEqual(len(variables), 2)
        self.assertIn("{{first_name}}", variables)
        self.assertIn("{{event_name | default: \"our event\"}}", variables)
        
    def test_resolve_personalization_variables(self):
        """Test resolving personalization variables for a contact"""
        # Create a mock contact
        mock_contact = MagicMock(spec=Contact)
        mock_contact.first_name = "John"
        mock_contact.last_name = "Doe"
        mock_contact.email = "john@example.com"
        mock_contact.organization = "Acme Corp"
        mock_contact.job_title = "Developer"
        mock_contact.phone_number = "+1234567890"
        mock_contact.full_name = "John Doe"
        mock_contact.custom_fields = {"department": "Engineering", "employee_id": "12345"}
        
        template_variables = [
            "{{first_name}}",
            "{{last_name}}", 
            "{{organization}}",
            "{{department}}",  # Custom field
            "{{missing_field | default: \"N/A\"}}",  # With default
            "{{another_missing}}"  # Without default
        ]
        
        resolved = self.service.resolve_personalization_variables(mock_contact, template_variables)
        
        # Check resolved values
        self.assertEqual(resolved["first_name"], "John")
        self.assertEqual(resolved["last_name"], "Doe")
        self.assertEqual(resolved["organization"], "Acme Corp")
        self.assertEqual(resolved["department"], "Engineering")
        self.assertEqual(resolved["missing_field"], "N/A")  # Default value
        self.assertEqual(resolved["another_missing"], "")  # Empty string for missing without default
        
    def test_personalize_html_content(self):
        """Test personalizing HTML content"""
        html_content = "<p>Hello {{first_name}},</p><p>Welcome to {{event_name | default: \"our event\"}}!</p>"
        personalization_vars = {
            "first_name": "John",
            "event_name": "Our Conference"
        }
        
        personalized = self.service.personalize_html_content(html_content, personalization_vars)
        
        # Should replace variables
        self.assertIn("Hello John,", personalized)
        self.assertIn("Welcome to Our Conference!", personalized)
        
    def test_create_recipient_snapshot_not_found(self):
        """Test creating recipient snapshot with invalid staging snapshot"""
        # Mock query to return None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db_mock.query.return_value = mock_query
        
        # Expect PersonalizationServiceError
        with self.assertRaises(PersonalizationServiceError):
            self.service.create_recipient_snapshot(
                staging_snapshot_id=str(uuid.uuid4()),
                contact=MagicMock(spec=Contact)
            )

if __name__ == '__main__':
    unittest.main()