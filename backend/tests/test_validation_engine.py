import pytest
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.email.staging import StagingSnapshot
from app.services.email.validation import ValidationEngine, ValidationResult, ValidationSeverity, ValidationCategory, ValidationResultStatus
import tempfile
import os

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
def validation_engine():
    return ValidationEngine()

@pytest.fixture
def sample_html():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Test Email</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        <h1>Welcome to Our Service</h1>
        <p>This is a test email with <a href="https://example.com">a link</a>.</p>
        <img src="https://example.com/image.jpg" alt="Test image">
        <a href="https://example.com/button">Click Here</a>
    </body>
    </html>
    """

@pytest.fixture
def sample_staging_snapshot(sample_html):
    snapshot = Mock(spec=StagingSnapshot)
    snapshot.html_snapshot = sample_html
    snapshot.subject = "Test Subject"
    return snapshot

def test_validate_html_structure(validation_engine, sample_html):
    """Test HTML structure validation"""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(sample_html, 'html.parser')
    
    results = validation_engine._validate_html_structure(soup)
    
    # Should have no errors for valid HTML
    error_results = [r for r in results if r.severity == ValidationSeverity.ERROR and r.status == ValidationResultStatus.FAIL]
    assert len(error_results) == 0

def test_validate_html_missing_title(validation_engine):
    """Test detection of missing title tag"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
    </head>
    <body>
        <h1>Test</h1>
    </body>
    </html>
    """
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    results = validation_engine._validate_html_structure(soup)
    
    # Should have a warning about missing title
    missing_title_results = [r for r in results if r.check_id == "missing_title"]
    assert len(missing_title_results) == 1
    assert missing_title_results[0].severity == ValidationSeverity.WARNING

def test_validate_links(validation_engine, sample_staging_snapshot):
    """Test link validation"""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(sample_staging_snapshot.html_snapshot, 'html.parser')
    
    with patch.object(validation_engine.session, 'head') as mock_head:
        mock_head.return_value.status_code = 200
        
        results = validation_engine._validate_links(sample_staging_snapshot, soup)
        
        # Should have no errors for valid links
        error_results = [r for r in results if r.severity == ValidationSeverity.ERROR and r.status == ValidationResultStatus.FAIL]
        assert len(error_results) == 0

def test_validate_links_placeholder(validation_engine, sample_staging_snapshot):
    """Test detection of placeholder links"""
    html = """
    <!DOCTYPE html>
    <html>
    <body>
        <a href="#">Placeholder link</a>
        <a href="http://">Another placeholder</a>
    </body>
    </html>
    """
    
    sample_staging_snapshot.html_snapshot = html
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    results = validation_engine._validate_links(sample_staging_snapshot, soup)
    
    # Should have errors for placeholder links
    placeholder_results = [r for r in results if r.check_id == "placeholder_link"]
    assert len(placeholder_results) == 2

def test_validate_images(validation_engine, sample_staging_snapshot):
    """Test image validation"""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(sample_staging_snapshot.html_snapshot, 'html.parser')
    
    with patch.object(validation_engine.session, 'head') as mock_head:
        mock_head.return_value.status_code = 200
        
        results = validation_engine._validate_images(sample_staging_snapshot, soup)
        
        # Should have a warning about missing alt text (our sample has alt text)
        missing_alt_results = [r for r in results if r.check_id == "missing_alt_text"]
        assert len(missing_alt_results) == 0  # Our sample has alt text

def test_validate_images_missing_alt(validation_engine):
    """Test detection of missing alt text"""
    html = """
    <!DOCTYPE html>
    <html>
    <body>
        <img src="https://example.com/image.jpg">
    </body>
    </html>
    """
    
    snapshot = Mock(spec=StagingSnapshot)
    snapshot.html_snapshot = html
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    results = validation_engine._validate_images(snapshot, soup)
    
    # Should have a warning about missing alt text
    missing_alt_results = [r for r in results if r.check_id == "missing_alt_text"]
    assert len(missing_alt_results) == 1

def test_validate_content_missing_subject(validation_engine):
    """Test detection of missing subject"""
    snapshot = Mock(spec=StagingSnapshot)
    snapshot.subject = ""  # Missing subject
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup("<html><body><h1>Test</h1></body></html>", 'html.parser')
    
    results = validation_engine._validate_content(snapshot, soup)
    
    # Should have an error about missing subject
    missing_subject_results = [r for r in results if r.check_id == "missing_subject"]
    assert len(missing_subject_results) == 1
    assert missing_subject_results[0].severity == ValidationSeverity.ERROR

def test_validate_content_placeholder_text(validation_engine):
    """Test detection of placeholder text"""
    html = """
    <!DOCTYPE html>
    <html>
    <body>
        <p>Lorem ipsum dolor sit amet</p>
        <p>This is placeholder text for testing</p>
    </body>
    </html>
    """
    
    snapshot = Mock(spec=StagingSnapshot)
    snapshot.subject = "Test Subject"
    snapshot.html_snapshot = html
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    results = validation_engine._validate_content(snapshot, soup)
    
    # Should have warnings about placeholder text
    placeholder_results = [r for r in results if r.check_id == "placeholder_text_detected"]
    assert len(placeholder_results) > 0

def test_is_valid_url(validation_engine):
    """Test URL validation"""
    assert validation_engine._is_valid_url("https://example.com") == True
    assert validation_engine._is_valid_url("http://example.com/path") == True
    assert validation_engine._is_valid_url("https://example.com?param=value") == True
    assert validation_engine._is_valid_url("invalid-url") == False
    assert validation_engine._is_valid_url("") == False

def test_is_safe_url(validation_engine):
    """Test safe URL checking"""
    assert validation_engine._is_safe_url("https://example.com") == True
    assert validation_engine._is_safe_url("http://localhost") == False
    assert validation_engine._is_safe_url("http://127.0.0.1") == False
    assert validation_engine._is_safe_url("http://10.0.0.1") == False
    assert validation_engine._is_safe_url("http://192.168.1.1") == False

def test_calculate_score_no_results(validation_engine):
    """Test score calculation with no results"""
    results = []
    score = validation_engine._calculate_score(results)
    assert score == 100

def test_calculate_score_with_errors(validation_engine):
    """Test score calculation with errors"""
    results = [
        ValidationResult(
            check_id="test1",
            category=ValidationCategory.HTML,
            severity=ValidationSeverity.ERROR,
            status=ValidationResultStatus.FAIL,
            description="Test error"
        )
    ]
    score = validation_engine._calculate_score(results)
    assert 0 <= score < 100  # Score should be reduced due to error

if __name__ == "__main__":
    pytest.main([__file__])