from typing import Dict, List, Tuple, Optional, Any
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import re
from app.models.email.validation import ValidationSeverity, ValidationCategory, ValidationResultStatus
from app.models.email.staging import StagingSnapshot
import logging
import time

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class ValidationResult:
    """Represents a single validation result"""
    
    def __init__(
        self,
        check_id: str,
        category: ValidationCategory,
        severity: ValidationSeverity,
        status: ValidationResultStatus,
        description: str,
        affected_section_id: Optional[str] = None,
        suggested_resolution: Optional[str] = None,
        raw_data: Optional[str] = None
    ):
        self.check_id = check_id
        self.category = category
        self.severity = severity
        self.status = status
        self.description = description
        self.affected_section_id = affected_section_id
        self.suggested_resolution = suggested_resolution
        self.raw_data = raw_data

class ValidationEngine:
    """Main validation engine for email content"""
    
    def __init__(self):
        self.session = requests.Session()
        # Set a timeout for all requests
        self.session.timeout = 10
        # Limit redirects to prevent infinite loops
        self.session.max_redirects = 5
    
    def validate_staging_snapshot(self, staging_snapshot: StagingSnapshot) -> Tuple[List[ValidationResult], int]:
        """
        Run all validations on a staging snapshot
        
        Args:
            staging_snapshot: The staging snapshot to validate
            
        Returns:
            Tuple of (validation results, overall score)
        """
        results = []
        
        try:
            # Parse HTML for easier analysis
            soup = BeautifulSoup(staging_snapshot.html_snapshot, 'html.parser')
        except Exception as e:
            results.append(ValidationResult(
                check_id="html_parse_failure",
                category=ValidationCategory.HTML,
                severity=ValidationSeverity.ERROR,
                status=ValidationResultStatus.FAIL,
                description=f"Failed to parse HTML: {str(e)}",
                suggested_resolution="Ensure the HTML is well-formed"
            ))
            return results, 0
        
        # Run all validation checks
        results.extend(self._validate_html_structure(soup))
        results.extend(self._validate_links(staging_snapshot, soup))
        results.extend(self._validate_images(staging_snapshot, soup))
        results.extend(self._validate_content(staging_snapshot, soup))
        results.extend(self._validate_accessibility(soup))
        results.extend(self._validate_responsive_design(staging_snapshot, soup))
        
        # Calculate overall score
        score = self._calculate_score(results)
        
        return results, score
    
    def _validate_html_structure(self, soup: BeautifulSoup) -> List[ValidationResult]:
        """Validate HTML structure and basic requirements"""
        results = []
        
        # Check for document metadata
        if not soup.find('title'):
            results.append(ValidationResult(
                check_id="missing_title",
                category=ValidationCategory.HTML,
                severity=ValidationSeverity.WARNING,
                status=ValidationResultStatus.FAIL,
                description="Missing <title> tag in HTML head",
                suggested_resolution="Add a descriptive title to your email"
            ))
        
        # Check for document language
        html_tag = soup.find('html')
        if html_tag and not html_tag.get('lang'):
            results.append(ValidationResult(
                check_id="missing_language",
                category=ValidationCategory.HTML,
                severity=ValidationSeverity.WARNING,
                status=ValidationResultStatus.FAIL,
                description="Missing lang attribute in <html> tag",
                suggested_resolution="Add a lang attribute to the <html> tag (e.g., lang='en')"
            ))
        
        # Check for dangerous elements
        dangerous_tags = ['script', 'iframe', 'embed', 'object']
        for tag in dangerous_tags:
            if soup.find(tag):
                results.append(ValidationResult(
                    check_id=f"dangerous_{tag}",
                    category=ValidationCategory.HTML,
                    severity=ValidationSeverity.ERROR,
                    status=ValidationResultStatus.FAIL,
                    description=f"Found dangerous <{tag}> tag in email",
                    suggested_resolution=f"Remove all <{tag}> tags from the email"
                ))
        
        # Check for proper doctype
        doctype = soup.decode_contents()[:50].lower()
        if '<!doctype html>' not in doctype and '<html' in doctype.lower():
            results.append(ValidationResult(
                check_id="missing_doctype",
                category=ValidationCategory.HTML,
                severity=ValidationSeverity.WARNING,
                status=ValidationResultStatus.FAIL,
                description="Missing or incorrect DOCTYPE declaration",
                suggested_resolution="Add <!DOCTYPE html> at the beginning of the document"
            ))
        
        return results
    
    def _validate_links(self, staging_snapshot: StagingSnapshot, soup: BeautifulSoup) -> List[ValidationResult]:
        """Validate all links in the email"""
        results = []
        checked_urls = set()
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            
            # Check for missing URL
            if not href or href.strip() == '':
                results.append(ValidationResult(
                    check_id="empty_link",
                    category=ValidationCategory.LINK,
                    severity=ValidationSeverity.ERROR,
                    status=ValidationResultStatus.FAIL,
                    description="Found link with empty href attribute",
                    affected_section_id=getattr(link, 'id', None),
                    suggested_resolution="Add a valid URL to the href attribute or remove the link"
                ))
                continue
            
            # Check for placeholder links
            if href in ['#', 'http://', 'https://', 'link']:
                results.append(ValidationResult(
                    check_id="placeholder_link",
                    category=ValidationCategory.LINK,
                    severity=ValidationSeverity.WARNING,
                    status=ValidationResultStatus.FAIL,
                    description=f"Found placeholder link: {href}",
                    affected_section_id=getattr(link, 'id', None),
                    suggested_resolution="Replace placeholder links with actual URLs"
                ))
                continue
            
            # Validate URL format
            if not self._is_valid_url(href):
                results.append(ValidationResult(
                    check_id="invalid_url_format",
                    category=ValidationCategory.LINK,
                    severity=ValidationSeverity.ERROR,
                    status=ValidationResultStatus.FAIL,
                    description=f"Invalid URL format: {href}",
                    affected_section_id=getattr(link, 'id', None),
                    suggested_resolution="Fix the URL to conform to RFC 3986 standard"
                ))
                continue
            
            # Check for HTTP links when HTTPS is expected
            if href.startswith('http://'):
                results.append(ValidationResult(
                    check_id="insecure_http_link",
                    category=ValidationCategory.LINK,
                    severity=ValidationSeverity.WARNING,
                    status=ValidationResultStatus.FAIL,
                    description=f"Insecure HTTP link: {href}",
                    affected_section_id=getattr(link, 'id', None),
                    suggested_resolution="Use HTTPS instead of HTTP for better security"
                ))
            
            # Check for unreachable destinations (only for safe URLs)
            if href not in checked_urls and self._is_safe_url(href):
                checked_urls.add(href)
                try:
                    # Only check URLs that are likely to be public
                    if self._should_check_url_reachability(href):
                        response = self.session.head(href, allow_redirects=True)
                        if response.status_code >= 400:
                            results.append(ValidationResult(
                                check_id="unreachable_link",
                                category=ValidationCategory.LINK,
                                severity=ValidationSeverity.WARNING,
                                status=ValidationResultStatus.FAIL,
                                description=f"Unreachable link (HTTP {response.status_code}): {href}",
                                affected_section_id=getattr(link, 'id', None),
                                suggested_resolution="Fix the link to point to a reachable destination"
                            ))
                except requests.exceptions.RequestException as e:
                    # Only warn about network issues for non-local URLs
                    if not self._is_local_url(href):
                        results.append(ValidationResult(
                            check_id="link_check_error",
                            category=ValidationCategory.LINK,
                            severity=ValidationSeverity.WARNING,
                            status=ValidationResultStatus.FAIL,
                            description=f"Could not verify link reachability: {href} ({str(e)})",
                            affected_section_id=getattr(link, 'id', None),
                            suggested_resolution="Manually verify this link works correctly"
                        ))
                except Exception as e:
                    results.append(ValidationResult(
                        check_id="link_check_exception",
                        category=ValidationCategory.LINK,
                        severity=ValidationSeverity.WARNING,
                        status=ValidationResultStatus.FAIL,
                        description=f"Error checking link: {href} ({str(e)})",
                        affected_section_id=getattr(link, 'id', None),
                        suggested_resolution="Manually verify this link works correctly"
                    ))
            
            # Check for empty buttons (links that look like buttons but have no text)
            if link.find_parent(class_=re.compile(r'button', re.I)) and not link.get_text(strip=True):
                results.append(ValidationResult(
                    check_id="empty_button",
                    category=ValidationCategory.LINK,
                    severity=ValidationSeverity.ERROR,
                    status=ValidationResultStatus.FAIL,
                    description="Found button with no text content",
                    affected_section_id=getattr(link, 'id', None),
                    suggested_resolution="Add descriptive text to the button"
                ))
        
        return results
    
    def _validate_images(self, staging_snapshot: StagingSnapshot, soup: BeautifulSoup) -> List[ValidationResult]:
        """Validate all images in the email"""
        results = []
        checked_images = set()
        
        # Find all images
        images = soup.find_all('img')
        
        for img in images:
            src = img.get('src', '')
            
            # Check for missing image source
            if not src or src.strip() == '':
                results.append(ValidationResult(
                    check_id="missing_image_src",
                    category=ValidationCategory.IMAGE,
                    severity=ValidationSeverity.ERROR,
                    status=ValidationResultStatus.FAIL,
                    description="Found image with empty src attribute",
                    affected_section_id=getattr(img, 'id', None),
                    suggested_resolution="Add a valid image source to the src attribute or remove the image"
                ))
                continue
            
            # Check for missing alt text
            alt = img.get('alt', '')
            if alt is None or alt.strip() == '':
                results.append(ValidationResult(
                    check_id="missing_alt_text",
                    category=ValidationCategory.IMAGE,
                    severity=ValidationSeverity.WARNING,
                    status=ValidationResultStatus.FAIL,
                    description="Image missing alt text",
                    affected_section_id=getattr(img, 'id', None),
                    suggested_resolution="Add descriptive alt text for accessibility"
                ))
            
            # Validate URL format for image sources
            if not self._is_valid_url(src) and not src.startswith('cid:'):
                results.append(ValidationResult(
                    check_id="invalid_image_url",
                    category=ValidationCategory.IMAGE,
                    severity=ValidationSeverity.ERROR,
                    status=ValidationResultStatus.FAIL,
                    description=f"Invalid image URL format: {src}",
                    affected_section_id=getattr(img, 'id', None),
                    suggested_resolution="Fix the image URL to conform to RFC 3986 standard"
                ))
                continue
            
            # Check for inaccessible images (only for safe URLs)
            if src not in checked_images and self._is_safe_url(src) and not src.startswith('cid:'):
                checked_images.add(src)
                try:
                    # Only check URLs that are likely to be public
                    if self._should_check_url_reachability(src):
                        response = self.session.head(src, allow_redirects=True)
                        if response.status_code >= 400:
                            results.append(ValidationResult(
                                check_id="unreachable_image",
                                category=ValidationCategory.IMAGE,
                                severity=ValidationSeverity.WARNING,
                                status=ValidationResultStatus.FAIL,
                                description=f"Unreachable image (HTTP {response.status_code}): {src}",
                                affected_section_id=getattr(img, 'id', None),
                                suggested_resolution="Fix the image source to point to a reachable image"
                            ))
                except requests.exceptions.RequestException as e:
                    # Only warn about network issues for non-local URLs
                    if not self._is_local_url(src):
                        results.append(ValidationResult(
                            check_id="image_check_error",
                            category=ValidationCategory.IMAGE,
                            severity=ValidationSeverity.WARNING,
                            status=ValidationResultStatus.FAIL,
                            description=f"Could not verify image accessibility: {src} ({str(e)})",
                            affected_section_id=getattr(img, 'id', None),
                            suggested_resolution="Manually verify this image is accessible"
                        ))
                except Exception as e:
                    results.append(ValidationResult(
                        check_id="image_check_exception",
                        category=ValidationCategory.IMAGE,
                        severity=ValidationSeverity.WARNING,
                        status=ValidationResultStatus.FAIL,
                        description=f"Error checking image: {src} ({str(e)})",
                        affected_section_id=getattr(img, 'id', None),
                        suggested_resolution="Manually verify this image is accessible"
                    ))
        
        return results
    
    def _validate_content(self, staging_snapshot: StagingSnapshot, soup: BeautifulSoup) -> List[ValidationResult]:
        """Validate email content"""
        results = []
        
        # Check for missing subject
        if not staging_snapshot.subject or staging_snapshot.subject.strip() == '':
            results.append(ValidationResult(
                check_id="missing_subject",
                category=ValidationCategory.CONTENT,
                severity=ValidationSeverity.ERROR,
                status=ValidationResultStatus.FAIL,
                description="Email subject is missing or empty",
                suggested_resolution="Add a descriptive subject line"
            ))
        
        # Check for unresolved template variables (common patterns)
        template_patterns = [r'\{\{.*?\}\}', r'\$\{.*?\}', r'<%=?.*?%>']
        html_content = str(soup)
        
        for pattern in template_patterns:
            matches = re.findall(pattern, html_content)
            if matches:
                results.append(ValidationResult(
                    check_id="unresolved_template_variables",
                    category=ValidationCategory.CONTENT,
                    severity=ValidationSeverity.ERROR,
                    status=ValidationResultStatus.FAIL,
                    description=f"Found unresolved template variables: {', '.join(matches[:3])}",
                    suggested_resolution="Replace template variables with actual content or remove them"
                ))
                break  # Only report the first type found
        
        # Check for placeholder text
        placeholder_texts = [
            'lorem ipsum', 'placeholder text', '[company]', '[name]', 
            '[insert]', 'sample text', 'dummy content'
        ]
        
        lowercase_content = html_content.lower()
        for placeholder in placeholder_texts:
            if placeholder in lowercase_content:
                results.append(ValidationResult(
                    check_id="placeholder_text_detected",
                    category=ValidationCategory.CONTENT,
                    severity=ValidationSeverity.WARNING,
                    status=ValidationResultStatus.FAIL,
                    description=f"Detected placeholder text: '{placeholder}'",
                    suggested_resolution="Replace placeholder text with actual content"
                ))
        
        # Check for empty content sections
        text_elements = soup.find_all(['p', 'div', 'span', 'td', 'th'])
        empty_sections = 0
        
        for element in text_elements:
            if not element.get_text(strip=True) and element.find('img') is None:
                # Only count it if it's not just a structural element
                if element.name in ['p'] or ('class' in element.attrs and 'content' in ' '.join(element.attrs.get('class', []))):
                    empty_sections += 1
        
        if empty_sections > 3:  # Allow a few empty elements for layout
            results.append(ValidationResult(
                check_id="too_many_empty_sections",
                category=ValidationCategory.CONTENT,
                severity=ValidationSeverity.WARNING,
                status=ValidationResultStatus.FAIL,
                description=f"Found {empty_sections} empty content sections",
                suggested_resolution="Remove empty content sections or add content to them"
            ))
        
        return results
    
    def _validate_accessibility(self, soup: BeautifulSoup) -> List[ValidationResult]:
        """Validate accessibility aspects of the email"""
        results = []
        
        # Check image alt text (count those without alt text)
        images = soup.find_all('img')
        missing_alt_count = 0
        
        for img in images:
            alt = img.get('alt', '')
            if alt is None or alt.strip() == '':
                missing_alt_count += 1
        
        if missing_alt_count > 0:
            results.append(ValidationResult(
                check_id="missing_alt_text_count",
                category=ValidationCategory.ACCESSIBILITY,
                severity=ValidationSeverity.WARNING,
                status=ValidationResultStatus.FAIL,
                description=f"{missing_alt_count} images missing alt text",
                suggested_resolution="Add descriptive alt text to all images for screen reader users"
            ))
        
        # Check for semantic heading structure
        headings = soup.find_all(re.compile(r'^h[1-6]$'))
        if not headings:
            results.append(ValidationResult(
                check_id="missing_headings",
                category=ValidationCategory.ACCESSIBILITY,
                severity=ValidationSeverity.WARNING,
                status=ValidationResultStatus.FAIL,
                description="No semantic headings found in email",
                suggested_resolution="Use semantic heading tags (h1-h6) to structure content"
            ))
        
        # Check color contrast - simplified check
        # This is a basic check - full contrast checking would require CSS parsing
        text_elements = soup.find_all(['p', 'div', 'span', 'td'])
        low_contrast_count = 0
        
        # Count elements with inline styles that might have low contrast
        for element in text_elements:
            style = element.get('style', '').lower()
            if 'color:' in style and ('background-color:' in style or 'background:' in style):
                # Very basic heuristic - real contrast checking would be more complex
                # Just flag this as a potential issue that needs manual checking
                low_contrast_count += 1
        
        if low_contrast_count > 5:
            results.append(ValidationResult(
                check_id="potential_low_contrast",
                category=ValidationCategory.ACCESSIBILITY,
                severity=ValidationSeverity.WARNING,
                status=ValidationResultStatus.FAIL,
                description=f"Found {low_contrast_count} elements with potentially low color contrast",
                suggested_resolution="Verify color contrast meets WCAG AA standards (4.5:1 for normal text)"
            ))
        
        # Check for link clarity
        links = soup.find_all('a', href=True)
        unclear_links = 0
        
        for link in links:
            text = link.get_text(strip=True).lower()
            unclear_phrases = ['click here', 'read more', 'learn more', 'go here', 'link']
            
            for phrase in unclear_phrases:
                if phrase in text:
                    unclear_links += 1
                    break
        
        if unclear_links > 0:
            results.append(ValidationResult(
                check_id="unclear_links",
                category=ValidationCategory.ACCESSIBILITY,
                severity=ValidationSeverity.WARNING,
                status=ValidationResultStatus.FAIL,
                description=f"Found {unclear_links} links with unclear text",
                suggested_resolution="Use descriptive link text that indicates the destination"
            ))
        
        return results
    
    def _validate_responsive_design(self, staging_snapshot: StagingSnapshot, soup: BeautifulSoup) -> List[ValidationResult]:
        """Validate responsive design aspects"""
        results = []
        
        # Check for viewport meta tag
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        if not viewport_meta:
            results.append(ValidationResult(
                check_id="missing_viewport_meta",
                category=ValidationCategory.RESPONSIVE,
                severity=ValidationSeverity.WARNING,
                status=ValidationResultStatus.FAIL,
                description="Missing viewport meta tag",
                suggested_resolution="Add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"> to <head>"
            ))
        
        # Check for fixed width elements that might cause overflow
        style_tags = soup.find_all('style')
        inline_styles = [elem.get('style', '') for elem in soup.find_all(attrs={'style': True})]
        
        all_css = ' '.join([tag.get_text() for tag in style_tags] + inline_styles)
        
        # Look for fixed widths that might cause issues
        fixed_width_patterns = [
            r'width:\s*\d{4,}px',  # Widths over 1000px
            r'max-width:\s*\d{4,}px',
            r'min-width:\s*\d{4,}px'
        ]
        
        large_fixed_widths = 0
        for pattern in fixed_width_patterns:
            matches = re.findall(pattern, all_css, re.IGNORECASE)
            large_fixed_widths += len(matches)
        
        if large_fixed_widths > 0:
            results.append(ValidationResult(
                check_id="large_fixed_widths",
                category=ValidationCategory.RESPONSIVE,
                severity=ValidationSeverity.WARNING,
                status=ValidationResultStatus.FAIL,
                description=f"Found {large_fixed_widths} elements with large fixed widths that may not fit on mobile screens",
                suggested_resolution="Use percentage-based widths or max-width constraints for better responsiveness"
            ))
        
        # Check for tables used for layout (warning)
        layout_tables = soup.find_all('table', attrs={'role': lambda x: x != 'presentation'})
        if len(layout_tables) > 5:
            results.append(ValidationResult(
                check_id="many_layout_tables",
                category=ValidationCategory.RESPONSIVE,
                severity=ValidationSeverity.WARNING,
                status=ValidationResultStatus.FAIL,
                description=f"Found {len(layout_tables)} tables that might be used for layout",
                suggested_resolution="Consider using CSS Grid or Flexbox instead of tables for layout"
            ))
        
        return results
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _is_safe_url(self, url: str) -> bool:
        """Check if a URL is safe to check (not internal/localhost)"""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            
            if not hostname:
                return False
                
            # Block obviously unsafe hosts
            unsafe_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
            if hostname in unsafe_hosts:
                return False
                
            # Block private IP ranges
            if hostname.startswith('10.') or \
               hostname.startswith('172.') and 16 <= int(hostname.split('.')[1]) <= 31 or \
               hostname.startswith('192.168.'):
                return False
                
            return True
        except Exception:
            return False
    
    def _is_local_url(self, url: str) -> bool:
        """Check if a URL is local (localhost, internal IPs)"""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            
            if not hostname:
                return False
                
            local_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
            if hostname in local_hosts:
                return True
                
            if hostname.startswith('10.') or \
               hostname.startswith('172.') and 16 <= int(hostname.split('.')[1]) <= 31 or \
               hostname.startswith('192.168.'):
                return True
                
            return False
        except Exception:
            return False
    
    def _should_check_url_reachability(self, url: str) -> bool:
        """Determine if we should check the reachability of a URL"""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            
            if not hostname:
                return False
            
            # Skip checking certain domains that are problematic
            skip_domains = [
                'example.com',
                'yourdomain.com',
                'test.com'
            ]
            
            for domain in skip_domains:
                if domain in hostname:
                    return False
            
            # Only check HTTP/HTTPS URLs
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Skip local addresses
            if self._is_local_url(url):
                return False
            
            return True
        except Exception:
            return False
    
    def _calculate_score(self, results: List[ValidationResult]) -> int:
        """Calculate an overall validation score (0-100)"""
        if not results:
            return 100
            
        # Weighted scoring
        error_weight = 10
        warning_weight = 3
        info_weight = 1
        
        max_possible_penalty = len(results) * error_weight  # Worst case scenario
        if max_possible_penalty == 0:
            return 100
            
        actual_penalty = 0
        
        for result in results:
            if result.status == ValidationResultStatus.FAIL:
                if result.severity == ValidationSeverity.ERROR:
                    actual_penalty += error_weight
                elif result.severity == ValidationSeverity.WARNING:
                    actual_penalty += warning_weight
                elif result.severity == ValidationSeverity.INFORMATION:
                    actual_penalty += info_weight
        
        # Calculate score (higher is better)
        score = max(0, 100 - (actual_penalty / max_possible_penalty * 100))
        return int(score)