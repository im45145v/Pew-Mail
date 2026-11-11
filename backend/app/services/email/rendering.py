from typing import Dict, Any, Tuple, Optional
import json
from mjml import mjml2html
import logging

logger = logging.getLogger(__name__)

class EmailRenderingService:
    """Service for rendering structured email documents to HTML using MJML"""
    
    def __init__(self):
        pass
    
    def render_document_to_mjml(self, document: Dict[str, Any]) -> str:
        """
        Convert a structured email document to MJML markup
        
        Args:
            document: Structured email document
            
        Returns:
            MJML markup string
        """
        try:
            # Extract document components
            metadata = document.get("metadata", {})
            settings = document.get("settings", {})
            sections = document.get("sections", [])
            
            # Build MJML structure
            mjml_parts = []
            
            # Add MJML boilerplate
            mjml_parts.append('<mjml>')
            mjml_parts.append('  <mj-head>')
            
            # Add title if available
            if "subject" in metadata:
                mjml_parts.append(f'    <mj-title>{metadata["subject"]}</mj-title>')
                mjml_parts.append(f'    <mj-preview>{metadata.get("preheader", "")}</mj-preview>')
            
            # Add styles
            mjml_parts.append('    <mj-style inline="inline">')
            mjml_parts.append('      .paragraph { margin: 0; }')
            mjml_parts.append('    </mj-style>')
            
            mjml_parts.append('  </mj-head>')
            mjml_parts.append('  <mj-body>')
            
            # Apply global settings
            body_attrs = []
            if "background_color" in settings:
                body_attrs.append(f'background-color="{settings["background_color"]}"')
            if "width" in settings:
                body_attrs.append(f'width="{settings["width"]}"')
            
            body_attr_str = " ".join(body_attrs) if body_attrs else ""
            mjml_parts.append(f'    <mj-section {body_attr_str}>')
            mjml_parts.append('      <mj-column>')
            
            # Render each section
            for section in sections:
                mjml_component = self._render_section(section)
                if mjml_component:
                    mjml_parts.append(f'        {mjml_component}')
            
            # Close section and column
            mjml_parts.append('      </mj-column>')
            mjml_parts.append('    </mj-section>')
            mjml_parts.append('  </mj-body>')
            mjml_parts.append('</mjml>')
            
            return "\n".join(mjml_parts)
        except Exception as e:
            logger.error(f"Error converting document to MJML: {str(e)}")
            raise
    
    def _render_section(self, section: Dict[str, Any]) -> Optional[str]:
        """
        Render a single section/component to MJML
        
        Args:
            section: Section/component data
            
        Returns:
            MJML string for the component
        """
        section_type = section.get("type", "")
        props = section.get("props", {})
        
        if section_type == "header":
            return self._render_header(props)
        elif section_type == "hero":
            return self._render_hero(props)
        elif section_type == "heading":
            return self._render_heading(props)
        elif section_type == "paragraph":
            return self._render_paragraph(props)
        elif section_type == "image":
            return self._render_image(props)
        elif section_type == "button":
            return self._render_button(props)
        elif section_type == "divider":
            return self._render_divider(props)
        elif section_type == "spacer":
            return self._render_spacer(props)
        elif section_type == "columns":
            return self._render_columns(props)
        elif section_type == "social":
            return self._render_social(props)
        elif section_type == "footer":
            return self._render_footer(props)
        elif section_type == "html":
            return self._render_html(props)
        else:
            logger.warning(f"Unknown section type: {section_type}")
            return None
    
    def _render_header(self, props: Dict[str, Any]) -> str:
        """Render header component"""
        # Simple implementation - in a real app, this would be more sophisticated
        text = props.get("text", "Header")
        return f'<mj-text>{text}</mj-text>'
    
    def _render_hero(self, props: Dict[str, Any]) -> str:
        """Render hero component"""
        title = props.get("title", "Hero Title")
        subtitle = props.get("subtitle", "")
        alignment = props.get("alignment", "center")
        
        hero_parts = []
        hero_parts.append(f'<mj-text align="{alignment}"><h1>{title}</h1></mj-text>')
        if subtitle:
            hero_parts.append(f'<mj-text align="{alignment}">{subtitle}</mj-text>')
        
        return "\n".join(hero_parts)
    
    def _render_heading(self, props: Dict[str, Any]) -> str:
        """Render heading component"""
        text = props.get("text", "Heading")
        level = props.get("level", 2)
        alignment = props.get("alignment", "left")
        
        return f'<mj-text align="{alignment}"><h{level}>{text}</h{level}></mj-text>'
    
    def _render_paragraph(self, props: Dict[str, Any]) -> str:
        """Render paragraph component"""
        content = props.get("content", "Paragraph text")
        alignment = props.get("alignment", "left")
        
        return f'<mj-text align="{alignment}" css-class="paragraph">{content}</mj-text>'
    
    def _render_image(self, props: Dict[str, Any]) -> str:
        """Render image component"""
        src = props.get("src", "")
        alt = props.get("alt", "")
        width = props.get("width", "100%")
        alignment = props.get("alignment", "center")
        
        if not src:
            return ""
        
        attrs = [f'src="{src}"']
        if alt:
            attrs.append(f'alt="{alt}"')
        attrs.append(f'width="{width}"')
        attrs.append(f'align="{alignment}"')
        
        return f'<mj-image {" ".join(attrs)} />'
    
    def _render_button(self, props: Dict[str, Any]) -> str:
        """Render button component"""
        label = props.get("label", "Click Me")
        url = props.get("url", "#")
        background_color = props.get("background_color", "#007bff")
        text_color = props.get("text_color", "#ffffff")
        border_radius = props.get("border_radius", "4px")
        alignment = props.get("alignment", "center")
        
        attrs = [
            f'href="{url}"',
            f'background-color="{background_color}"',
            f'color="{text_color}"',
            f'border-radius="{border_radius}"',
            f'align="{alignment}"'
        ]
        
        return f'<mj-button {" ".join(attrs)}>{label}</mj-button>'
    
    def _render_divider(self, props: Dict[str, Any]) -> str:
        """Render divider component"""
        border_width = props.get("border_width", "1px")
        border_style = props.get("border_style", "solid")
        border_color = props.get("border_color", "#cccccc")
        
        attrs = [
            f'border-width="{border_width}"',
            f'border-style="{border_style}"',
            f'border-color="{border_color}"'
        ]
        
        return f'<mj-divider {" ".join(attrs)} />'
    
    def _render_spacer(self, props: Dict[str, Any]) -> str:
        """Render spacer component"""
        height = props.get("height", "20px")
        return f'<mj-spacer height="{height}" />'
    
    def _render_columns(self, props: Dict[str, Any]) -> str:
        """Render columns component"""
        columns = props.get("columns", [])
        column_count = len(columns)
        
        if column_count == 0:
            return ""
        
        # Calculate column widths
        width = 100 // column_count
        
        column_parts = ['<mj-section>']
        for i, column in enumerate(columns):
            column_parts.append(f'  <mj-column width="{width}%">')
            
            # Render column content
            for item in column.get("content", []):
                component = self._render_section(item)
                if component:
                    column_parts.append(f'    {component}')
            
            column_parts.append('  </mj-column>')
        
        column_parts.append('</mj-section>')
        return "\n".join(column_parts)
    
    def _render_social(self, props: Dict[str, Any]) -> str:
        """Render social links component"""
        links = props.get("links", [])
        
        if not links:
            return ""
        
        social_parts = ['<mj-social font-size="15px" icon-size="30px" mode="horizontal">']
        
        for link in links:
            platform = link.get("platform", "")
            url = link.get("url", "#")
            if platform:
                social_parts.append(f'  <mj-social-element name="{platform}" href="{url}" />')
        
        social_parts.append('</mj-social>')
        return "\n".join(social_parts)
    
    def _render_footer(self, props: Dict[str, Any]) -> str:
        """Render footer component"""
        text = props.get("text", "Footer text")
        return f'<mj-text align="center">{text}</mj-text>'
    
    def _render_html(self, props: Dict[str, Any]) -> str:
        """Render custom HTML component"""
        html = props.get("html", "")
        return html
    
    def compile_mjml_to_html(self, mjml_content: str) -> Tuple[str, Optional[str]]:
        """
        Compile MJML to HTML
        
        Args:
            mjml_content: MJML markup string
            
        Returns:
            Tuple of (compiled HTML, error message if any)
        """
        try:
            result = mjml2html(mjml_content)
            if result.get("errors"):
                error_messages = [error.get("message", "") for error in result["errors"]]
                return result.get("html", ""), "; ".join(error_messages)
            return result.get("html", ""), None
        except Exception as e:
            logger.error(f"Error compiling MJML: {str(e)}")
            return "", str(e)
    
    def render_document_to_html(self, document: Dict[str, Any]) -> Tuple[str, str, Optional[str]]:
        """
        Render a structured email document to HTML through MJML
        
        Args:
            document: Structured email document
            
        Returns:
            Tuple of (MJML content, HTML content, error message if any)
        """
        try:
            # Convert document to MJML
            mjml_content = self.render_document_to_mjml(document)
            
            # Compile MJML to HTML
            html_content, error = self.compile_mjml_to_html(mjml_content)
            
            return mjml_content, html_content, error
        except Exception as e:
            logger.error(f"Error rendering document to HTML: {str(e)}")
            return "", "", str(e)

# Singleton instance
email_rendering_service = EmailRenderingService()