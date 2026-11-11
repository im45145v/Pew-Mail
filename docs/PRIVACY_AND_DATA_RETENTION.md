# Pew Mail - Privacy and Data Retention

This document outlines the privacy practices and data retention policies implemented in Pew Mail to protect user data and ensure compliance with privacy regulations.

## Overview

Pew Mail is committed to protecting user privacy and maintaining strict data retention policies. This document describes how user data is collected, processed, stored, and eventually deleted in accordance with privacy best practices and regulatory requirements.

## Data Collection and Usage

### Personal Data Collected

1. **Account Information**
   - Email address (required for account creation)
   - Name (optional)
   - Password (hashed and securely stored)
   - Profile information (optional)

2. **Organization Data**
   - Organization name
   - Organization members
   - Role assignments
   - Billing information (if applicable)

3. **Email Content Data**
   - Email templates
   - Email drafts
   - Email subjects
   - Email body content
   - Email attachments
   - Email metadata (send dates, recipients, etc.)

4. **Contact Data**
   - Contact names
   - Contact email addresses
   - Contact metadata (tags, groups, etc.)
   - Personalization data

5. **Usage Data**
   - Feature usage statistics
   - API access logs
   - Session data
   - Device information

6. **Integration Data**
   - Google account information (OAuth tokens, encrypted)
   - Email provider credentials (encrypted)
   - Third-party API keys (encrypted)

### Data Usage Purposes

1. **Service Provision**
   - Email creation and delivery
   - Template management
   - Contact management
   - Analytics and reporting

2. **Account Management**
   - Authentication and authorization
   - Password reset
   - Account recovery

3. **Communication**
   - Service notifications
   - Marketing communications (with consent)
   - Support responses

4. **Improvement**
   - Product development
   - Bug fixing
   - Performance optimization

5. **Legal Compliance**
   - Tax reporting
   - Audit requirements
   - Regulatory compliance

## Data Protection Measures

### Encryption

```python
# Data encryption at rest
from cryptography.fernet import Fernet
from app.core.config import settings
import base64
import hashlib

class DataEncryption:
    def __init__(self):
        # Derive encryption key from secret key
        key = settings.SECRET_KEY.encode()
        self.key = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
        self.cipher_suite = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return None
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return None
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()

# Usage for sensitive data
token_encryption = DataEncryption()
encrypted_token = token_encryption.encrypt("sensitive_token_value")
```

### Secure Data Storage

```python
# Database model with encrypted fields
from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class UserData(BaseModel):
    __tablename__ = "user_data"
    
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    # Public data stored in plain text
    email = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    
    # Sensitive data encrypted at rest
    encrypted_phone = Column(Text, nullable=True)
    encrypted_address = Column(Text, nullable=True)
    
    # OAuth tokens encrypted
    encrypted_oauth_token = Column(Text, nullable=True)
```

### Data Minimization

```python
# Data minimization in API responses
from pydantic import BaseModel
from typing import Optional

class PublicUserResponse(BaseModel):
    """Minimal user data for public responses"""
    id: str
    email: str
    name: Optional[str]
    # No sensitive fields included

class PrivateUserResponse(BaseModel):
    """Extended user data for authorized responses"""
    id: str
    email: str
    name: Optional[str]
    created_at: str
    last_login: Optional[str]
    # Only necessary private fields
```

## Privacy Controls

### User Consent Management

```python
from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class ConsentType(str, Enum):
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    THIRD_PARTY_SHARING = "third_party_sharing"

class UserConsent(BaseModel):
    __tablename__ = "user_consents"
    
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    consent_type = Column(String, nullable=False, index=True)
    granted = Column(Boolean, default=False, nullable=False)
    granted_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    consent_version = Column(String, nullable=False)

class ConsentService:
    def grant_consent(self, user_id: str, consent_type: ConsentType):
        """Grant user consent for a specific purpose"""
        consent = UserConsent(
            user_id=user_id,
            consent_type=consent_type,
            granted=True,
            granted_at=datetime.utcnow(),
            consent_version=CURRENT_CONSENT_VERSION
        )
        self.db.add(consent)
        self.db.commit()
    
    def revoke_consent(self, user_id: str, consent_type: ConsentType):
        """Revoke user consent for a specific purpose"""
        consent = self.db.query(UserConsent).filter(
            UserConsent.user_id == user_id,
            UserConsent.consent_type == consent_type
        ).first()
        
        if consent:
            consent.granted = False
            consent.revoked_at = datetime.utcnow()
            self.db.commit()
    
    def check_consent(self, user_id: str, consent_type: ConsentType) -> bool:
        """Check if user has granted consent for a specific purpose"""
        consent = self.db.query(UserConsent).filter(
            UserConsent.user_id == user_id,
            UserConsent.consent_type == consent_type,
            UserConsent.granted == True
        ).first()
        
        return consent is not None
```

### Data Access Controls

```python
# Organization-level data isolation
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

def check_organization_access(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: str = None
):
    """Check if user has access to organization data"""
    if not organization_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    # Verify user is member of organization
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == current_user.id,
        OrganizationMembership.organization_id == organization_id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied to organization")
    
    return membership

# Usage in API endpoints
@router.get("/emails")
async def get_emails(
    organization_id: str,
    membership: OrganizationMembership = Depends(check_organization_access)
):
    """Get emails for organization with access control"""
    # Only return emails belonging to the organization
    emails = db.query(Email).filter(
        Email.organization_id == organization_id
    ).all()
    
    return emails
```

## Data Retention Policies

### Retention Periods

| Data Type | Retention Period | Reason |
|-----------|------------------|---------|
| Account Data | Until account deletion | Service functionality |
| Email Content | 7 years | Legal/compliance requirements |
| Usage Logs | 2 years | Analytics and debugging |
| Audit Logs | 7 years | Compliance and security |
| Billing Records | 7 years | Tax and audit requirements |
| Temporary Files | 30 days | Operational efficiency |
| Deleted Data | 90 days then permanent deletion | Recovery window |

### Automated Retention Management

```python
from datetime import datetime, timedelta
from sqlalchemy import and_

class DataRetentionService:
    def __init__(self, db_session):
        self.db = db_session
    
    def cleanup_expired_data(self):
        """Remove data that has exceeded retention periods"""
        now = datetime.utcnow()
        
        # Clean up old temporary files (30 days)
        old_temp_files = self.db.query(TempFile).filter(
            TempFile.created_at < (now - timedelta(days=30))
        )
        for file in old_temp_files:
            self.delete_file(file.storage_path)
        old_temp_files.delete()
        
        # Clean up old usage logs (2 years)
        old_logs = self.db.query(UsageLog).filter(
            UsageLog.timestamp < (now - timedelta(days=730))
        )
        old_logs.delete()
        
        # Process soft-deleted records (90 days)
        expired_deletions = self.db.query(SoftDeletable).filter(
            and_(
                SoftDeletable.deleted_at.isnot(None),
                SoftDeletable.deleted_at < (now - timedelta(days=90))
            )
        )
        expired_deletions.delete()
        
        self.db.commit()
    
    def schedule_retention_cleanup(self):
        """Schedule regular retention cleanup"""
        import asyncio
        import time
        
        async def cleanup_loop():
            while True:
                try:
                    self.cleanup_expired_data()
                    await asyncio.sleep(86400)  # Run daily
                except Exception as e:
                    logger.error("Retention cleanup failed", error=str(e))
                    await asyncio.sleep(3600)  # Wait 1 hour before retry
        
        asyncio.create_task(cleanup_loop())
```

### Soft Delete Pattern

```python
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID

class SoftDeletableMixin:
    """Mixin for soft delete functionality"""
    deleted_at = Column(DateTime, nullable=True, index=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)

class UserService:
    def delete_user(self, user_id: str, deleted_by_user_id: str):
        """Soft delete a user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundError()
        
        # Soft delete the user
        user.deleted_at = datetime.utcnow()
        user.deleted_by = deleted_by_user_id
        
        # Soft delete related data
        self.soft_delete_user_data(user_id, deleted_by_user_id)
        
        self.db.commit()
    
    def soft_delete_user_data(self, user_id: str, deleted_by_user_id: str):
        """Soft delete all data associated with a user"""
        # Delete organization memberships
        memberships = self.db.query(OrganizationMembership).filter(
            OrganizationMembership.user_id == user_id
        )
        for membership in memberships:
            membership.deleted_at = datetime.utcnow()
            membership.deleted_by = deleted_by_user_id
        
        # Mark user's emails for deletion
        emails = self.db.query(Email).filter(Email.user_id == user_id)
        for email in emails:
            email.deleted_at = datetime.utcnow()
            email.deleted_by = deleted_by_user_id
    
    def permanently_delete_expired_data(self):
        """Permanently delete data that has been soft deleted for 90+ days"""
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        expired_users = self.db.query(User).filter(
            and_(
                User.deleted_at.isnot(None),
                User.deleted_at < cutoff_date
            )
        )
        
        for user in expired_users:
            self.permanently_delete_user_data(user.id)
            self.db.delete(user)
        
        self.db.commit()
```

## Data Subject Rights

### Right to Access

```python
class DataExportService:
    def generate_data_export(self, user_id: str) -> str:
        """Generate a comprehensive data export for a user"""
        export_data = {
            "user_profile": self.get_user_profile(user_id),
            "organizations": self.get_user_organizations(user_id),
            "emails": self.get_user_emails(user_id),
            "contacts": self.get_user_contacts(user_id),
            "usage_history": self.get_usage_history(user_id),
            "consents": self.get_user_consents(user_id),
            "audit_logs": self.get_audit_logs(user_id)
        }
        
        # Generate export file
        export_filename = f"user_data_export_{user_id}_{int(datetime.utcnow().timestamp())}.json"
        export_path = f"/tmp/exports/{export_filename}"
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return export_path
    
    def get_user_profile(self, user_id: str) -> dict:
        """Get user profile data"""
        user = self.db.query(User).filter(User.id == user_id).first()
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "created_at": user.created_at,
            "last_login": user.last_login
        }
```

### Right to Rectification

```python
class UserProfileService:
    def update_user_profile(self, user_id: str, update_data: dict):
        """Update user profile with rectification"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundError()
        
        # Log the update for audit purposes
        audit_log = AuditLog(
            user_id=user_id,
            action="profile_update",
            details=f"Updated fields: {list(update_data.keys())}",
            timestamp=datetime.utcnow()
        )
        self.db.add(audit_log)
        
        # Update user data
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
```

### Right to Erasure (Right to be Forgotten)

```python
class DataDeletionService:
    def request_account_deletion(self, user_id: str) -> str:
        """Initiate account deletion process"""
        # Create deletion request
        deletion_request = AccountDeletionRequest(
            user_id=user_id,
            requested_at=datetime.utcnow(),
            status="pending_confirmation"
        )
        self.db.add(deletion_request)
        self.db.commit()
        
        # Send confirmation email
        self.send_deletion_confirmation_email(user_id)
        
        return deletion_request.id
    
    def confirm_account_deletion(self, deletion_request_id: str, confirmation_token: str):
        """Confirm and execute account deletion"""
        request = self.db.query(AccountDeletionRequest).filter(
            AccountDeletionRequest.id == deletion_request_id
        ).first()
        
        if not request or not self.verify_token(request.user_id, confirmation_token):
            raise InvalidTokenError()
        
        # Execute immediate deletions
        self.immediate_deletions(request.user_id)
        
        # Schedule permanent deletion
        self.schedule_permanent_deletion(request.user_id)
        
        # Update request status
        request.status = "completed"
        request.completed_at = datetime.utcnow()
        self.db.commit()
    
    def immediate_deletions(self, user_id: str):
        """Perform immediate data deletions"""
        # Remove from mailing lists
        self.remove_from_marketing_lists(user_id)
        
        # Cancel subscriptions
        self.cancel_billing_subscriptions(user_id)
        
        # Remove from third-party services
        self.notify_third_parties_of_deletion(user_id)
        
        # Soft delete user account
        user = self.db.query(User).filter(User.id == user_id).first()
        user.deleted_at = datetime.utcnow()
        user.email = f"deleted_{user_id}@deleted.pewmail.com"  # Prevent email conflicts
        
        self.db.commit()
    
    def schedule_permanent_deletion(self, user_id: str):
        """Schedule permanent deletion after retention period"""
        # This would be handled by the retention service
        pass
```

## Third-Party Data Sharing

### Data Processing Agreements

```python
class ThirdPartyDataService:
    def __init__(self):
        self.third_parties = {
            "stripe": {
                "purpose": "Payment processing",
                "data_shared": ["billing_email", "payment_method"],
                "dpa_signed": True,
                "dpa_date": "2026-01-15"
            },
            "google": {
                "purpose": "Email sending",
                "data_shared": ["email_content", "recipient_list"],
                "dpa_signed": True,
                "dpa_date": "2026-01-15"
            }
        }
    
    def share_data_with_third_party(self, user_id: str, third_party: str, data: dict):
        """Share data with third party services"""
        # Check if user has consented to this sharing
        if not self.user_has_consent_for_third_party(user_id, third_party):
            raise ConsentRequiredError(f"Consent required for {third_party}")
        
        # Check if DPA is in place
        if not self.third_parties[third_party].get("dpa_signed", False):
            raise AgreementRequiredError(f"DPA required for {third_party}")
        
        # Share data (implementation depends on third party)
        # ...
```

## Compliance Framework

### GDPR Compliance

```python
class GDPRComplianceService:
    def __init__(self, db_session):
        self.db = db_session
    
    def check_gdpr_compliance(self, user_id: str) -> dict:
        """Check GDPR compliance status for a user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"compliant": False, "issues": ["User not found"]}
        
        issues = []
        
        # Check consent management
        required_consents = [ConsentType.MARKETING, ConsentType.ANALYTICS]
        for consent_type in required_consents:
            if not self.has_consent(user_id, consent_type):
                issues.append(f"Missing consent for {consent_type}")
        
        # Check data retention
        if self.has_expired_data(user_id):
            issues.append("Expired data found")
        
        # Check right to access fulfillment
        if not self.can_fulfill_data_access(user_id):
            issues.append("Cannot fulfill data access request")
        
        return {
            "compliant": len(issues) == 0,
            "issues": issues
        }
    
    def generate_privacy_notice(self) -> str:
        """Generate GDPR-compliant privacy notice"""
        notice = """
        Pew Mail Privacy Notice
        
        1. Data Controller: [Company Name]
        2. Purpose of Processing: Email marketing platform services
        3. Legal Basis: Contract performance, legitimate interests, consent
        4. Data Recipients: Service providers (payment processors, email providers)
        5. Data Transfers: United States (adequacy decision or SCCs)
        6. Retention Periods: As outlined in our Data Retention Policy
        7. Rights: Access, rectification, erasure, restriction, objection, data portability
        8. Complaints: Supervisory authority contact information
        9. Contact: privacy@[company].com
        """
        return notice
```

### Data Processing Records

```python
class DataProcessingRecord(BaseModel):
    __tablename__ = "data_processing_records"
    
    processing_activity = Column(String, nullable=False)
    purpose = Column(String, nullable=False)
    legal_basis = Column(String, nullable=False)
    data_categories = Column(String, nullable=False)  # JSON array
    data_subjects = Column(String, nullable=False)    # JSON array
    recipients = Column(String, nullable=False)       # JSON array
    transfer_mechanism = Column(String, nullable=True)
    retention_period = Column(String, nullable=False)
    security_measures = Column(String, nullable=False)
    responsible_party = Column(String, nullable=False)
    last_reviewed = Column(DateTime, default=datetime.utcnow)
```

## Cookie Policy

### Cookie Management

```python
from fastapi import Response
from datetime import datetime, timedelta

class CookiePolicyService:
    def set_consent_cookies(self, response: Response, consent_preferences: dict):
        """Set consent preference cookies"""
        # Essential cookies (always set)
        response.set_cookie(
            key="cookie_consent",
            value="true",
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=31536000  # 1 year
        )
        
        # Preference cookies (based on consent)
        if consent_preferences.get("analytics", False):
            response.set_cookie(
                key="analytics_consent",
                value="true",
                httponly=True,
                secure=True,
                samesite="strict",
                expires=datetime.utcnow() + timedelta(days=365)
            )
        
        if consent_preferences.get("marketing", False):
            response.set_cookie(
                key="marketing_consent",
                value="true",
                httponly=True,
                secure=True,
                samesite="strict",
                expires=datetime.utcnow() + timedelta(days=365)
            )
    
    def get_cookie_policy(self) -> dict:
        """Return cookie policy information"""
        return {
            "cookies": [
                {
                    "name": "session",
                    "purpose": "Maintain user session",
                    "essential": True,
                    "duration": "Session"
                },
                {
                    "name": "cookie_consent",
                    "purpose": "Store cookie preferences",
                    "essential": True,
                    "duration": "1 year"
                },
                {
                    "name": "analytics_consent",
                    "purpose": "Analytics tracking preference",
                    "essential": False,
                    "duration": "1 year"
                },
                {
                    "name": "marketing_consent",
                    "purpose": "Marketing preference",
                    "essential": False,
                    "duration": "1 year"
                }
            ]
        }
```

## Incident Response

### Data Breach Procedures

```python
class IncidentResponseService:
    def report_data_breach(self, breach_details: dict):
        """Report and respond to a data breach"""
        # Log the incident
        incident = SecurityIncident(
            incident_type="data_breach",
            details=breach_details,
            reported_at=datetime.utcnow(),
            status="investigating"
        )
        self.db.add(incident)
        self.db.commit()
        
        # Notify security team
        self.notify_security_team(incident.id)
        
        # Assess impact
        affected_users = self.assess_breach_impact(breach_details)
        
        # Notify affected users (if required)
        if self.requires_user_notification(breach_details):
            for user_id in affected_users:
                self.notify_affected_user(user_id, breach_details)
        
        # Notify authorities (if required)
        if self.requires_authority_notification(breach_details):
            self.notify_regulatory_authorities(breach_details)
        
        # Update incident status
        incident.status = "responding"
        incident.updated_at = datetime.utcnow()
        self.db.commit()
    
    def assess_breach_impact(self, breach_details: dict) -> list:
        """Assess which users are affected by a breach"""
        # Implementation depends on breach type
        # Return list of affected user IDs
        pass
    
    def notify_affected_user(self, user_id: str, breach_details: dict):
        """Notify user of data breach"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            # Send breach notification email
            self.send_breach_notification_email(user.email, breach_details)
```

## Conclusion

This privacy and data retention policy ensures that Pew Mail handles user data responsibly and in compliance with applicable privacy regulations. The implementation includes technical and organizational measures to protect user privacy throughout the data lifecycle.

Key components:
1. Comprehensive data protection measures
2. Clear data retention and deletion policies
3. User privacy rights implementation
4. Third-party data sharing controls
5. Regulatory compliance frameworks
6. Incident response procedures

Implementation best practices:
1. Regular privacy impact assessments
2. Staff training on privacy practices
3. Annual policy review and updates
4. Monitoring of regulatory changes
5. User education on privacy controls
6. Documentation of all data processing activities

The system is designed to be adaptable to evolving privacy requirements while maintaining a strong commitment to user privacy and data protection.