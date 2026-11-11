from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.email.test import TestSend, TestDeliveryStatus, TestRecipient
from app.models.email.staging import StagingSnapshot
from app.models.email.audit import EmailAuditEvent
from app.models.user import User
import logging
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TestDeliveryProvider:
    """Abstract base class for test delivery providers"""
    
    def send_test_email(
        self,
        staging_snapshot: StagingSnapshot,
        recipients: List[str],
        sender_email: str,
        sender_name: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Send a test email
        
        Args:
            staging_snapshot: The staging snapshot to send
            recipients: List of recipient email addresses
            sender_email: Sender email address
            sender_name: Optional sender name
            
        Returns:
            Dictionary with delivery results
        """
        raise NotImplementedError("Subclasses must implement send_test_email")

class MockTestDeliveryProvider(TestDeliveryProvider):
    """Mock provider for testing"""
    
    def send_test_email(
        self,
        staging_snapshot: StagingSnapshot,
        recipients: List[str],
        sender_email: str,
        sender_name: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Mock implementation that simulates sending a test email
        
        Args:
            staging_snapshot: The staging snapshot to send
            recipients: List of recipient email addresses
            sender_email: Sender email address
            sender_name: Optional sender name
            
        Returns:
            Dictionary with delivery results
        """
        # Simulate successful delivery
        return {
            "status": TestDeliveryStatus.ACCEPTED,
            "message_id": f"mock-{uuid.uuid4()}",
            "provider_response": "Email accepted by mock provider",
            "error_message": None
        }

class MailpitTestDeliveryProvider(TestDeliveryProvider):
    """Provider for local Mailpit testing"""
    
    def __init__(self, mailpit_url: str = "http://localhost:8025"):
        self.mailpit_url = mailpit_url
        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("requests library is required for Mailpit provider")
    
    def send_test_email(
        self,
        staging_snapshot: StagingSnapshot,
        recipients: List[str],
        sender_email: str,
        sender_name: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Send test email via Mailpit
        
        Args:
            staging_snapshot: The staging snapshot to send
            recipients: List of recipient email addresses
            sender_email: Sender email address
            sender_name: Optional sender name
            
        Returns:
            Dictionary with delivery results
        """
        try:
            # Prepare email data
            sender = f"{sender_name} <{sender_email}>" if sender_name else sender_email
            
            email_data = {
                "From": sender,
                "To": ", ".join(recipients),
                "Subject": f"[TEST] {staging_snapshot.subject}",
                "HTML": staging_snapshot.html_snapshot,
                "Text": "This is a test email. Please view in HTML."  # Simplified text version
            }
            
            # Send to Mailpit
            response = self.requests.post(
                f"{self.mailpit_url}/api/v1/send",
                json=email_data
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": TestDeliveryStatus.ACCEPTED,
                    "message_id": result.get("id", f"mailpit-{uuid.uuid4()}"),
                    "provider_response": f"Email sent to Mailpit with ID {result.get('id', 'unknown')}",
                    "error_message": None
                }
            else:
                return {
                    "status": TestDeliveryStatus.FAILED,
                    "message_id": None,
                    "provider_response": f"Mailpit API returned status {response.status_code}",
                    "error_message": f"Failed to send to Mailpit: {response.text}"
                }
        except Exception as e:
            logger.error(f"Error sending email via Mailpit: {str(e)}")
            return {
                "status": TestDeliveryStatus.FAILED,
                "message_id": None,
                "provider_response": "Exception occurred",
                "error_message": str(e)
            }

class TestDeliveryService:
    """Service for delivering test emails"""
    
    def __init__(self, db: Session, provider: TestDeliveryProvider = None):
        self.db = db
        self.provider = provider or MockTestDeliveryProvider()
    
    def send_test_email(
        self,
        staging_snapshot_id: str,
        recipient_emails: List[str],
        sender_id: str
    ) -> TestSend:
        """
        Send a test email for a staging snapshot
        
        Args:
            staging_snapshot_id: ID of the staging snapshot
            recipient_emails: List of recipient email addresses
            sender_id: ID of the user sending the test email
            
        Returns:
            TestSend record
        """
        # Get the staging snapshot
        staging_snapshot = self.db.query(StagingSnapshot).filter(
            StagingSnapshot.id == staging_snapshot_id
        ).first()
        
        if not staging_snapshot:
            raise ValueError(f"Staging snapshot with ID {staging_snapshot_id} not found")
        
        # Get the sender
        sender = self.db.query(User).filter(User.id == sender_id).first()
        if not sender:
            raise ValueError(f"User with ID {sender_id} not found")
        
        # Validate recipient emails
        if not recipient_emails:
            raise ValueError("At least one recipient email is required")
        
        # Validate email format (simple validation)
        for email in recipient_emails:
            if "@" not in email or "." not in email.split("@")[1]:
                raise ValueError(f"Invalid email format: {email}")
        
        # Check for duplicate sends within last 5 minutes
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        duplicate_send = self.db.query(TestSend).filter(
            and_(
                TestSend.staging_snapshot_id == staging_snapshot_id,
                TestSend.sender_id == sender_id,
                TestSend.created_at >= five_minutes_ago
            )
        ).first()
        
        if duplicate_send:
            raise ValueError("Duplicate test send detected within last 5 minutes")
        
        # Create test send record
        test_send = TestSend(
            staging_snapshot_id=staging_snapshot_id,
            recipients=recipient_emails,
            sender_id=sender_id,
            sender_email=sender.email,
            subject=f"[TEST] {staging_snapshot.subject}"
        )
        self.db.add(test_send)
        self.db.flush()  # Flush to get the ID
        
        # Record audit event
        audit_event = EmailAuditEvent(
            entity_type="test_send",
            entity_id=test_send.id,
            action="requested",
            actor_id=sender_id,
            description=f"Requested test send to {len(recipient_emails)} recipients"
        )
        self.db.add(audit_event)
        
        # Commit the request
        self.db.commit()
        
        try:
            # Send the email using the provider
            result = self.provider.send_test_email(
                staging_snapshot,
                recipient_emails,
                sender.email,
                getattr(sender, 'name', None)
            )
            
            # Update test send record with results
            test_send.delivery_status = result["status"]
            test_send.provider_response = result["provider_response"]
            test_send.error_message = result["error_message"]
            test_send.message_id = result["message_id"]
            
            # Record audit event
            audit_action = "delivered" if result["status"] == TestDeliveryStatus.ACCEPTED else "failed"
            audit_event = EmailAuditEvent(
                entity_type="test_send",
                entity_id=test_send.id,
                action=audit_action,
                actor_id=sender_id,
                description=f"Test send {audit_action}: {result['provider_response']}"
            )
            self.db.add(audit_event)
            
            # Commit the results
            self.db.commit()
            self.db.refresh(test_send)
            
            return test_send
            
        except Exception as e:
            logger.error(f"Error sending test email: {str(e)}")
            
            # Update test send record with error
            test_send.delivery_status = TestDeliveryStatus.FAILED
            test_send.error_message = str(e)
            
            # Record audit event
            audit_event = EmailAuditEvent(
                entity_type="test_send",
                entity_id=test_send.id,
                action="failed",
                actor_id=sender_id,
                description=f"Test send failed with error: {str(e)}"
            )
            self.db.add(audit_event)
            
            # Commit the error
            self.db.commit()
            self.db.refresh(test_send)
            
            raise
    
    def get_test_sends(self, staging_snapshot_id: str) -> List[TestSend]:
        """
        Get all test sends for a staging snapshot
        
        Args:
            staging_snapshot_id: ID of the staging snapshot
            
        Returns:
            List of test sends
        """
        return self.db.query(TestSend).filter(
            TestSend.staging_snapshot_id == staging_snapshot_id
        ).order_by(TestSend.created_at.desc()).all()
    
    def get_test_recipients(self, organization_id: str) -> List[TestRecipient]:
        """
        Get all test recipients for an organization
        
        Args:
            organization_id: ID of the organization
            
        Returns:
            List of test recipients
        """
        return self.db.query(TestRecipient).filter(
            and_(
                TestRecipient.organization_id == organization_id,
                TestRecipient.is_active == True
            )
        ).all()
    
    def add_test_recipient(
        self,
        organization_id: str,
        email: str,
        name: Optional[str] = None
    ) -> TestRecipient:
        """
        Add a test recipient
        
        Args:
            organization_id: ID of the organization
            email: Email address
            name: Optional name
            
        Returns:
            Created test recipient
        """
        # Validate email format
        if "@" not in email or "." not in email.split("@")[1]:
            raise ValueError(f"Invalid email format: {email}")
        
        # Check if recipient already exists
        existing = self.db.query(TestRecipient).filter(
            and_(
                TestRecipient.organization_id == organization_id,
                TestRecipient.email == email
            )
        ).first()
        
        if existing:
            if not existing.is_active:
                # Reactivate if previously deactivated
                existing.is_active = True
                existing.name = name
                self.db.add(existing)
                self.db.commit()
                self.db.refresh(existing)
                return existing
            else:
                raise ValueError(f"Test recipient {email} already exists")
        
        # Create new test recipient
        test_recipient = TestRecipient(
            organization_id=organization_id,
            email=email,
            name=name
        )
        self.db.add(test_recipient)
        self.db.commit()
        self.db.refresh(test_recipient)
        
        return test_recipient
    
    def remove_test_recipient(self, recipient_id: str) -> None:
        """
        Remove a test recipient (soft delete)
        
        Args:
            recipient_id: ID of the test recipient
        """
        recipient = self.db.query(TestRecipient).filter(TestRecipient.id == recipient_id).first()
        if recipient:
            recipient.is_active = False
            self.db.add(recipient)
            self.db.commit()