import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.services.contacts.contact_service import ContactService, ContactServiceError
from app.models.contact import Contact, ContactGroup, ContactGroupMembership, ContactImport
from app.models.organization import Organization

class TestContactService(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.db_mock = MagicMock(spec=Session)
        self.service = ContactService(self.db_mock)
        
        # Sample data
        self.organization_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        
    def test_normalize_email(self):
        """Test email normalization"""
        self.assertEqual(self.service.normalize_email("  TEST@EXAMPLE.COM  "), "test@example.com")
        self.assertEqual(self.service.normalize_email(""), "")
        self.assertEqual(self.service.normalize_email(None), "")
        
    @patch('app.services.contacts.contact_service.ContactService.check_duplicate_email')
    def test_create_contact_success(self, mock_check_duplicate):
        """Test successful contact creation"""
        mock_check_duplicate.return_value = None
        
        # Mock the database add/commit/refresh
        mock_contact = MagicMock(spec=Contact)
        mock_contact.id = str(uuid.uuid4())
        mock_contact.first_name = "John"
        mock_contact.last_name = "Doe"
        mock_contact.email = "john.doe@example.com"
        
        self.db_mock.add.return_value = None
        self.db_mock.commit.return_value = None
        self.db_mock.refresh.return_value = None
        
        # Mock the query result
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contact
        self.db_mock.query.return_value = mock_query
        
        # Test contact creation
        result = self.service.create_contact(
            organization_id=self.organization_id,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result.first_name, "John")
        self.assertEqual(result.email, "john.doe@example.com")
        
    @patch('app.services.contacts.contact_service.ContactService.check_duplicate_email')
    def test_create_contact_duplicate(self, mock_check_duplicate):
        """Test contact creation with duplicate email"""
        # Mock that a duplicate exists
        mock_check_duplicate.return_value = MagicMock(spec=Contact)
        
        # Expect ContactServiceError
        with self.assertRaises(ContactServiceError):
            self.service.create_contact(
                organization_id=self.organization_id,
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com"
            )
            
    def test_check_duplicate_email(self):
        """Test duplicate email checking"""
        # Mock query result for existing contact
        mock_contact = MagicMock(spec=Contact)
        mock_contact.email = "john.doe@example.com"
        mock_contact.organization_id = self.organization_id
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_contact
        self.db_mock.query.return_value = mock_query
        
        # Test duplicate check
        result = self.service.check_duplicate_email("john.doe@example.com", self.organization_id)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result.email, "john.doe@example.com")
        
    def test_update_contact_not_found(self):
        """Test updating a non-existent contact"""
        # Mock query result as None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db_mock.query.return_value = mock_query
        
        # Expect ContactServiceError
        with self.assertRaises(ContactServiceError):
            self.service.update_contact(
                contact_id=str(uuid.uuid4()),
                first_name="Updated Name"
            )
            
    def test_delete_contact_not_found(self):
        """Test deleting a non-existent contact"""
        # Mock query result as None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db_mock.query.return_value = mock_query
        
        # Test deletion
        result = self.service.delete_contact(str(uuid.uuid4()))
        
        # Assertions
        self.assertFalse(result)
        
    def test_create_contact_group_success(self):
        """Test successful contact group creation"""
        # Mock the database operations
        mock_group = MagicMock(spec=ContactGroup)
        mock_group.id = str(uuid.uuid4())
        mock_group.name = "Test Group"
        mock_group.organization_id = self.organization_id
        
        self.db_mock.add.return_value = None
        self.db_mock.commit.return_value = None
        self.db_mock.refresh.return_value = None
        
        # Mock the query result
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_group
        self.db_mock.query.return_value = mock_query
        
        # Test group creation
        result = self.service.create_contact_group(
            organization_id=self.organization_id,
            name="Test Group"
        )
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "Test Group")
        
    def test_parse_csv_data(self):
        """Test CSV parsing"""
        csv_content = "first_name,last_name,email\nJohn,Doe,john@example.com\nJane,Smith,jane@example.com"
        result = self.service.parse_csv_data(csv_content)
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['first_name'], 'John')
        self.assertEqual(result[1]['email'], 'jane@example.com')

if __name__ == '__main__':
    unittest.main()