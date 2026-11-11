from typing import Dict, Any, List, Optional
import os
import yaml
from pathlib import Path

class AISkill:
    """Represents an AI skill with instructions and capabilities"""
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        instructions: str, 
        use_cases: List[str],
        constraints: List[str],
        version: str = "1.0"
    ):
        self.name = name
        self.description = description
        self.instructions = instructions
        self.use_cases = use_cases
        self.constraints = constraints
        self.version = version
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the skill to a dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "instructions": self.instructions,
            "use_cases": self.use_cases,
            "constraints": self.constraints,
            "version": self.version
        }

# Initial skills as defined in the requirements
EMAIL_DESIGN_FUNDAMENTALS = AISkill(
    name="Email Design Fundamentals",
    description="Core principles of email layout design, typography, visual hierarchy, spacing, color balance, alignment, and layout composition.",
    instructions="""
1. Prioritize visual hierarchy with clear headings and section separation
2. Use consistent spacing and padding between elements
3. Apply appropriate typography with readable fonts and sizes
4. Maintain color balance using the brand palette effectively
5. Ensure proper alignment of all elements for a clean, professional appearance
6. Create balanced layouts with appropriate white space
7. Focus on readability and scannability for email content
""",
    use_cases=[
        "Improving overall email layout",
        "Enhancing visual appeal",
        "Creating balanced compositions",
        "Applying consistent spacing"
    ],
    constraints=[
        "Must follow brand color guidelines",
        "Must maintain responsive design principles",
        "Should not exceed recommended email width (600px)",
        "Must be compatible with major email clients"
    ]
)

RESPONSIVE_EMAIL_DESIGN = AISkill(
    name="Responsive Email Design",
    description="Techniques for creating mobile-friendly email layouts with responsive images, appropriate button sizing, and stacking columns.",
    instructions="""
1. Design for mobile-first experience
2. Use appropriate button sizes (minimum 44px touch targets)
3. Implement responsive image sizing
4. Stack columns on mobile devices
5. Ensure proper spacing and padding on all devices
6. Test across different screen sizes and email clients
7. Use fluid layouts that adapt to container width
8. Optimize for touch interactions
""",
    use_cases=[
        "Making emails mobile-friendly",
        "Improving responsive layouts",
        "Optimizing touch interactions",
        "Adapting designs for different screen sizes"
    ],
    constraints=[
        "Must be compatible with major email clients",
        "Should use standard responsive techniques",
        "Must maintain brand consistency",
        "Should not compromise desktop experience"
    ]
)

EVENT_INVITATION_DESIGN = AISkill(
    name="Event Invitation Design",
    description="Specialized design principles for event-focused emails with hero sections, date presentation, registration CTAs, and sponsor placement.",
    instructions="""
1. Create compelling hero sections with event branding
2. Clearly present event dates, times, and venues
3. Design prominent registration call-to-action buttons
4. Effectively showcase speakers or special guests
5. Strategically place sponsor logos and information
6. Include essential event details in a scannable format
7. Use excitement-inducing visuals and copy
8. Create urgency with early bird deadlines or limited capacity
""",
    use_cases=[
        "Creating event announcements",
        "Designing registration pages",
        "Showcasing event details",
        "Placing sponsor information"
    ],
    constraints=[
        "Must include all essential event information",
        "Should prioritize registration conversion",
        "Must be accessible to all users",
        "Should follow brand guidelines"
    ]
)

NEWSLETTER_DESIGN = AISkill(
    name="Newsletter Design",
    description="Design principles for newsletters with proper content hierarchy, multiple sections, readability, and article presentation.",
    instructions="""
1. Structure content with clear hierarchy
2. Organize multiple content sections logically
3. Enhance readability with appropriate typography
4. Present articles with featured images and teasers
5. Include clear section headers and dividers
6. Balance text and visual elements
7. Create scannable content with bullet points and lists
8. Design effective newsletter headers and footers
""",
    use_cases=[
        "Creating regular newsletters",
        "Organizing content sections",
        "Improving content readability",
        "Presenting multiple articles"
    ],
    constraints=[
        "Must maintain consistent branding",
        "Should be easy to scan quickly",
        "Must be accessible to all users",
        "Should encourage engagement with content"
    ]
)

SPONSORSHIP_OUTREACH = AISkill(
    name="Sponsorship Outreach",
    description="Professional communication techniques for sponsorship emails with value propositions, clear CTAs, and appropriate information hierarchy.",
    instructions="""
1. Communicate value proposition clearly and concisely
2. Design professional tone and presentation
3. Create clear call-to-action pathways
4. Structure information with appropriate hierarchy
5. Highlight benefits and return on investment
6. Include relevant statistics and credibility markers
7. Make contact information prominent and accessible
8. Follow industry-standard sponsorship outreach practices
""",
    use_cases=[
        "Creating sponsorship proposals",
        "Crafting professional outreach emails",
        "Presenting value propositions",
        "Designing clear CTAs"
    ],
    constraints=[
        "Must maintain professional tone",
        "Should be persuasive but not pushy",
        "Must include clear contact information",
        "Should highlight concrete benefits"
    ]
)

PROFESSIONAL_EMAIL_WRITING = AISkill(
    name="Professional Email Writing",
    description="Techniques for professional email copywriting, including subject lines, preheaders, concise copy, tone adjustment, and clear communication.",
    instructions="""
1. Craft compelling subject lines that increase open rates
2. Write informative preheaders that entice readers
3. Create concise copy that communicates effectively
4. Adjust tone to match audience and purpose
5. Ensure clear communication of key messages
6. Use action-oriented language
7. Minimize jargon and complex terminology
8. Proofread for grammar and spelling errors
""",
    use_cases=[
        "Writing subject lines",
        "Creating engaging preheaders",
        "Crafting concise copy",
        "Adjusting communication tone"
    ],
    constraints=[
        "Must be clear and actionable",
        "Should avoid excessive promotional language",
        "Must be proofread for errors",
        "Should be appropriate for the target audience"
    ]
)

BRAND_CONSISTENCY = AISkill(
    name="Brand Consistency",
    description="Principles for maintaining brand identity in emails, including color usage, typography, logo placement, tone, and footer standards.",
    instructions="""
1. Apply brand colors consistently throughout the email
2. Use brand-approved typography and font pairings
3. Place logos according to brand guidelines
4. Maintain consistent tone of voice
5. Follow footer standards with required information
6. Ensure all visual elements align with brand identity
7. Apply branded button styles and interactive elements
8. Maintain brand personality in copywriting
""",
    use_cases=[
        "Ensuring brand-aligned designs",
        "Applying brand colors and fonts",
        "Placing logos appropriately",
        "Maintaining tone consistency"
    ],
    constraints=[
        "Must strictly follow brand guidelines",
        "Should not deviate from established brand identity",
        "Must include required legal/compliance information",
        "Should reflect brand personality accurately"
    ]
)

EMAIL_ACCESSIBILITY = AISkill(
    name="Email Accessibility",
    description="Accessibility best practices for emails, including alt text, semantic structure, readability, contrast, and accessible links/buttons.",
    instructions="""
1. Provide descriptive alt text for all images
2. Create semantic structure with proper heading hierarchy
3. Maintain high contrast ratios for text and backgrounds
4. Ensure readable font sizes and line heights
5. Design accessible links and buttons with clear labels
6. Use ARIA attributes where appropriate
7. Provide text alternatives for visual content
8. Test with screen readers and accessibility tools
""",
    use_cases=[
        "Improving email accessibility",
        "Adding alt text to images",
        "Structuring content semantically",
        "Ensuring adequate contrast"
    ],
    constraints=[
        "Must meet WCAG accessibility standards",
        "Should be compatible with assistive technologies",
        "Must not compromise visual design",
        "Should follow email accessibility best practices"
    ]
)

# Registry of all available skills
SKILLS_REGISTRY = {
    "email_design_fundamentals": EMAIL_DESIGN_FUNDAMENTALS,
    "responsive_email_design": RESPONSIVE_EMAIL_DESIGN,
    "event_invitation_design": EVENT_INVITATION_DESIGN,
    "newsletter_design": NEWSLETTER_DESIGN,
    "sponsorship_outreach": SPONSORSHIP_OUTREACH,
    "professional_email_writing": PROFESSIONAL_EMAIL_WRITING,
    "brand_consistency": BRAND_CONSISTENCY,
    "email_accessibility": EMAIL_ACCESSIBILITY
}

def get_skill(skill_id: str) -> Optional[AISkill]:
    """Get a skill by its ID"""
    return SKILLS_REGISTRY.get(skill_id)

def get_all_skills() -> Dict[str, AISkill]:
    """Get all available skills"""
    return SKILLS_REGISTRY

def select_relevant_skills(user_request: str, project_context: Dict[str, Any]) -> List[AISkill]:
    """
    Select relevant skills based on user request and project context.
    
    This is a simplified implementation. In a real system, this would use
    more sophisticated matching algorithms.
    """
    relevant_skills = []
    
    # Simple keyword-based matching for demonstration
    request_lower = user_request.lower()
    
    if any(keyword in request_lower for keyword in ["design", "layout", "visual", "aesthetic"]):
        relevant_skills.append(EMAIL_DESIGN_FUNDAMENTALS)
        relevant_skills.append(RESPONSIVE_EMAIL_DESIGN)
    
    if any(keyword in request_lower for keyword in ["event", "hackathon", "conference", "workshop"]):
        relevant_skills.append(EVENT_INVITATION_DESIGN)
    
    if "newsletter" in request_lower:
        relevant_skills.append(NEWSLETTER_DESIGN)
    
    if any(keyword in request_lower for keyword in ["sponsor", "partnership", "collaboration"]):
        relevant_skills.append(SPONSORSHIP_OUTREACH)
    
    if any(keyword in request_lower for keyword in ["write", "copy", "text", "content"]):
        relevant_skills.append(PROFESSIONAL_EMAIL_WRITING)
    
    if "brand" in request_lower:
        relevant_skills.append(BRAND_CONSISTENCY)
    
    if any(keyword in request_lower for keyword in ["accessibility", "accessible", "screen reader"]):
        relevant_skills.append(EMAIL_ACCESSIBILITY)
    
    # Always include fundamentals
    if EMAIL_DESIGN_FUNDAMENTALS not in relevant_skills:
        relevant_skills.append(EMAIL_DESIGN_FUNDAMENTALS)
    
    return relevant_skills