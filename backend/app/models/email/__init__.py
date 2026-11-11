"""
Email models package
"""

from .email import Email, EmailStatus
from .template import EmailTemplate, TemplateCategory, TemplateScope
from .template_version import EmailTemplateVersion
from .component import ReusableComponent, ReusableComponentVersion
from .design_token import DesignTokenSet
from .approval import Approval, ApprovalStatus, ReviewComment
from .asset import EmailAsset
from .audit import EmailAuditEvent
from .google_account import GoogleAccount, GoogleAccountStatus, GoogleDraft, GoogleSendHistory
from .staging import StagingSnapshot, StagingSnapshotStatus
from .test import TestRecipient, TestSend
from .validation import ValidationRun, ValidationResult, ValidationResultStatus, ValidationCategory, ValidationSeverity
from .version import EmailVersion
from .collaboration import EmailComment, EmailCommentReply, ActivityEvent
from .campaign import Campaign, CampaignEmail, CampaignStatus
from .analytics import ProviderEvent, EmailAnalyticsAggregate, AnalyticsSource, AnalyticsEventType