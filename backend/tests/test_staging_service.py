import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.email.staging import StagingSnapshot, StagingSnapshotStatus
from app.models.email.email import Email
from app.models.email.version import EmailVersion
from app.models.user import User
from app.models.project import Project
from app.services.email.staging import StagingService
from app.services.email.validation import ValidationEngine
import uuid

# Test database setup
@pytest.fixture(scope="function")
def test_db():
    # Create in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def mock_validation_engine():
    mock_engine = Mock(spec=ValidationEngine)
    mock_engine.validate_staging_snapshot.return_value = ([], 100)  # No errors, perfect score
    return mock_engine

@pytest.fixture
def staging_service(test_db, mock_validation_engine):
    service = StagingService(test_db)
    service.validation_engine = mock_validation_engine
    return service

@pytest.fixture
def sample_data(test_db):
    # Create sample user
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        name="Test User"
    )
    test_db.add(user)
    
    # Create sample project
    project = Project(
        id=uuid.uuid4(),
        name="Test Project",
        organization_id=uuid.uuid4()
    )
    test_db.add(project)
    
    # Create sample email
    email = Email(
        id=uuid.uuid4(),
        name="Test Email",
        subject="Test Subject",
        project_id=project.id,
        document={}
    )
    test_db.add(email)
    
    # Create sample email version
    email_version = EmailVersion(
        id=uuid.uuid4(),
        email_id=email.id,
        version_number=1,
        document_snapshot={}
    )
    test_db.add(email_version)
    
    test_db.commit()
    
    return {
        "user": user,
        "project": project,
        "email": email,
        "email_version": email_version
    }

def test_create_staging_snapshot(staging_service, sample_data):
    """Test creating a staging snapshot"""
    user = sample_data["user"]
    email = sample_data["email"]
    email_version = sample_data["email_version"]
    
    with patch('app.services.email.staging.email_rendering_service') as mock_renderer:
        mock_renderer.render_document_to_html.return_value = ("<mjml></mjml>", "<html></html>", None)
        
        staging_snapshot = staging_service.create_staging_snapshot(
            str(email.id),
            str(email_version.id),
            str(user.id)
        )
        
        assert staging_snapshot.email_id == email.id
        assert staging_snapshot.email_version_id == email_version.id
        assert staging_snapshot.author_id == user.id
        assert staging_snapshot.staging_status == StagingSnapshotStatus.VALIDATION_PENDING

def test_get_staging_snapshot(staging_service, sample_data):
    """Test getting a staging snapshot"""
    user = sample_data["user"]
    email = sample_data["email"]
    email_version = sample_data["email_version"]
    
    with patch('app.services.email.staging.email_rendering_service') as mock_renderer:
        mock_renderer.render_document_to_html.return_value = ("<mjml></mjml>", "<html></html>", None)
        
        # Create a staging snapshot
        created_snapshot = staging_service.create_staging_snapshot(
            str(email.id),
            str(email_version.id),
            str(user.id)
        )
        
        # Retrieve it
        retrieved_snapshot = staging_service.get_staging_snapshot(str(created_snapshot.id))
        
        assert retrieved_snapshot is not None
        assert retrieved_snapshot.id == created_snapshot.id

def test_get_staging_history(staging_service, sample_data):
    """Test getting staging history"""
    user = sample_data["user"]
    email = sample_data["email"]
    email_version = sample_data["email_version"]
    
    with patch('app.services.email.staging.email_rendering_service') as mock_renderer:
        mock_renderer.render_document_to_html.return_value = ("<mjml></mjml>", "<html></html>", None)
        
        # Create multiple staging snapshots
        snapshot1 = staging_service.create_staging_snapshot(
            str(email.id),
            str(email_version.id),
            str(user.id)
        )
        
        snapshot2 = staging_service.create_staging_snapshot(
            str(email.id),
            str(email_version.id),
            str(user.id)
        )
        
        # Get history
        history = staging_service.get_staging_history(str(email.id))
        
        assert len(history) == 2
        # Should be ordered by creation date (descending)
        assert history[0].id == snapshot2.id
        assert history[1].id == snapshot1.id

def test_update_staging_status_valid_transition(staging_service, sample_data):
    """Test updating staging status with valid transition"""
    user = sample_data["user"]
    email = sample_data["email"]
    email_version = sample_data["email_version"]
    
    with patch('app.services.email.staging.email_rendering_service') as mock_renderer:
        mock_renderer.render_document_to_html.return_value = ("<mjml></mjml>", "<html></html>", None)
        
        # Create a staging snapshot
        staging_snapshot = staging_service.create_staging_snapshot(
            str(email.id),
            str(email_version.id),
            str(user.id)
        )
        
        # Update status (valid transition)
        updated_snapshot = staging_service.update_staging_status(
            str(staging_snapshot.id),
            StagingSnapshotStatus.VALIDATION_IN_PROGRESS,
            str(user.id)
        )
        
        assert updated_snapshot.staging_status == StagingSnapshotStatus.VALIDATION_IN_PROGRESS

def test_update_staging_status_invalid_transition(staging_service, sample_data):
    """Test updating staging status with invalid transition"""
    user = sample_data["user"]
    email = sample_data["email"]
    email_version = sample_data["email_version"]
    
    with patch('app.services.email.staging.email_rendering_service') as mock_renderer:
        mock_renderer.render_document_to_html.return_value = ("<mjml></mjml>", "<html></html>", None)
        
        # Create a staging snapshot
        staging_snapshot = staging_service.create_staging_snapshot(
            str(email.id),
            str(email_version.id),
            str(user.id)
        )
        
        # Try invalid transition (directly from PENDING to APPROVED)
        with pytest.raises(ValueError):
            staging_service.update_staging_status(
                str(staging_snapshot.id),
                StagingSnapshotStatus.APPROVED,
                str(user.id)
            )

def test_is_valid_status_transition(staging_service):
    """Test status transition validation"""
    # Valid transitions
    assert staging_service._is_valid_status_transition(
        StagingSnapshotStatus.VALIDATION_PENDING,
        StagingSnapshotStatus.VALIDATION_IN_PROGRESS
    ) == True
    
    assert staging_service._is_valid_status_transition(
        StagingSnapshotStatus.VALIDATION_IN_PROGRESS,
        StagingSnapshotStatus.VALIDATION_COMPLETED
    ) == True
    
    # Invalid transitions
    assert staging_service._is_valid_status_transition(
        StagingSnapshotStatus.VALIDATION_PENDING,
        StagingSnapshotStatus.APPROVED
    ) == False
    
    # Terminal state
    assert staging_service._is_valid_status_transition(
        StagingSnapshotStatus.DISCARDED,
        StagingSnapshotStatus.VALIDATION_IN_PROGRESS
    ) == False

def test_discard_staging_snapshot(staging_service, sample_data):
    """Test discarding a staging snapshot"""
    user = sample_data["user"]
    email = sample_data["email"]
    email_version = sample_data["email_version"]
    
    with patch('app.services.email.staging.email_rendering_service') as mock_renderer:
        mock_renderer.render_document_to_html.return_value = ("<mjml></mjml>", "<html></html>", None)
        
        # Create a staging snapshot
        staging_snapshot = staging_service.create_staging_snapshot(
            str(email.id),
            str(email_version.id),
            str(user.id)
        )
        
        # Discard it
        discarded_snapshot = staging_service.discard_staging_snapshot(
            str(staging_snapshot.id),
            str(user.id)
        )
        
        assert discarded_snapshot.staging_status == StagingSnapshotStatus.DISCARDED

if __name__ == "__main__":
    pytest.main([__file__])