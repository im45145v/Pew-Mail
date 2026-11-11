from typing import Optional
from sqlalchemy.orm import Session
from app.models.email.staging import StagingSnapshot
import html

class PreviewService:
    """Service for generating email previews"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_preview_html(self, staging_snapshot_id: str, preview_type: str = "desktop") -> str:
        """
        Get HTML for email preview
        
        Args:
            staging_snapshot_id: ID of the staging snapshot
            preview_type: Type of preview (desktop, mobile, tablet)
            
        Returns:
            HTML string for the preview
        """
        # Get the staging snapshot
        staging_snapshot = self.db.query(StagingSnapshot).filter(
            StagingSnapshot.id == staging_snapshot_id
        ).first()
        
        if not staging_snapshot:
            raise ValueError(f"Staging snapshot with ID {staging_snapshot_id} not found")
        
        # Return the HTML snapshot with appropriate wrapper
        return self._wrap_html_for_preview(staging_snapshot.html_snapshot, preview_type)
    
    def _wrap_html_for_preview(self, html_content: str, preview_type: str) -> str:
        """
        Wrap HTML content with preview-specific styling and container
        
        Args:
            html_content: The HTML content to wrap
            preview_type: Type of preview (desktop, mobile, tablet)
            
        Returns:
            Wrapped HTML with preview styling
        """
        # Define preview dimensions
        dimensions = {
            "desktop": ("100%", "auto"),
            "mobile": ("375px", "667px"),
            "tablet": ("768px", "1024px")
        }
        
        width, height = dimensions.get(preview_type, dimensions["desktop"])
        
        # Escape HTML content for safe embedding
        escaped_html = html.escape(html_content)
        
        # Create preview wrapper
        preview_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Preview</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            font-family: Arial, sans-serif;
        }}
        .preview-container {{
            display: flex;
            justify-content: center;
            width: 100%;
        }}
        .preview-frame {{
            width: {width};
            height: {height};
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: auto;
        }}
        .preview-header {{
            padding: 15px;
            border-bottom: 1px solid #eee;
            background-color: #fafafa;
        }}
        .preview-header h3 {{
            margin: 0;
            color: #333;
        }}
        .preview-header p {{
            margin: 5px 0 0 0;
            color: #666;
            font-size: 14px;
        }}
        .preview-content {{
            padding: 20px;
            height: calc(100% - 80px);
            overflow: auto;
        }}
        .preview-warning {{
            background-color: #fff8e1;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        .preview-warning strong {{
            color: #e65100;
        }}
    </style>
</head>
<body>
    <div class="preview-container">
        <div class="preview-frame">
            <div class="preview-header">
                <h3>Email Preview ({preview_type.capitalize()})</h3>
                <p>This is a simulation. Actual email clients may render differently.</p>
            </div>
            <div class="preview-warning">
                <strong>Preview Only:</strong> This preview shows approximate rendering in a browser.
                Actual email clients may display this content differently.
            </div>
            <div class="preview-content">
                {html_content}
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        return preview_html
    
    def get_preview_metadata(self, staging_snapshot_id: str) -> dict:
        """
        Get metadata for email preview
        
        Args:
            staging_snapshot_id: ID of the staging snapshot
            
        Returns:
            Dictionary with preview metadata
        """
        # Get the staging snapshot
        staging_snapshot = self.db.query(StagingSnapshot).filter(
            StagingSnapshot.id == staging_snapshot_id
        ).first()
        
        if not staging_snapshot:
            raise ValueError(f"Staging snapshot with ID {staging_snapshot_id} not found")
        
        return {
            "subject": staging_snapshot.subject,
            "preheader": staging_snapshot.preheader,
            "created_at": staging_snapshot.created_at.isoformat(),
            "author_id": str(staging_snapshot.author_id),
            "staging_status": staging_snapshot.staging_status.value
        }