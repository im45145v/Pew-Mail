# Pew Mail AI Skills

---

## **Overview**
This directory contains modular AI skills for **PewPew**, Pew Mail's AI assistant. Each skill is a reusable capability that PewPew can invoke to assist users with specific tasks, such as email creation, design, validation, and workflow automation.

---

## **Skill Structure**
Each skill is defined in a YAML file with the following structure:

```yaml
name: "skill_name"            # Unique identifier (lowercase, underscores)
description: "Skill purpose"  # Brief description of what the skill does
version: "1.0"               # Skill version

# Detailed instructions for PewPew
instructions: |
  1. Step 1: Understand the user's request.
  2. Step 2: Gather relevant context (brand, project, email).
  3. Step 3: Execute the task using available tools.
  4. Step 4: Validate the output.
  5. Step 5: Present the results to the user.

# Use cases where the skill is applicable
use_cases:
  - "Creating a new email from a brief" 
  - "Improving an existing email layout"

# Constraints or requirements
constraints:
  - "Must have access to brand guidelines"
  - "Requires email document context"

# Backend tools the skill can use
tools:
  - "document_operations"
  - "brand_validation"
  - "email_rendering"
```

---

## **Skill Categories**
| Category               | Purpose                                                                 | Example Skills                                      |
|------------------------|-------------------------------------------------------------------------|----------------------------------------------------|
| **email_creation**     | Create new emails from user briefs.                                    | Email Architect, Newsletter Creator               |
| **email_design**       | Improve email layouts, typography, and visual hierarchy.               | Visual Hierarchy Expert, Responsive Email Designer|
| **writing**            | Optimize email copy and tone.                                          | Professional Copywriter, Subject Line Specialist   |
| **quality**            | Validate emails for accessibility, links, and brand consistency.       | Email Quality Auditor, Brand Consistency Checker  |
| **campaigns**          | Manage email campaigns and workflows.                                  | Campaign Planner, Follow-up Sequence Designer      |
| **brand**              | Manage and apply brand guidelines.                                     | Brand Manager, Typography Assistant               |
| **integrations**       | Integrate with external services (e.g., Google OAuth).                 | Gmail Integrator, Analytics Connector             |

---

## **Adding New Skills**
1. Create a new YAML file in the appropriate category directory.
2. Define the skill using the structure above.
3. Register the skill in `ai_skills/registry.json`.

---

## **Skill Registry**
The `registry.json` file tracks all available skills and their metadata. Example:

```json
{
  "skills": [
    {
      "name": "email_architect",
      "description": "Guides users through creating a structured email.",
      "category": "email_creation",
      "file": "email_creation/email_architect.yaml",
      "version": "1.0"
    },
    {
      "name": "visual_hierarchy_expert",
      "description": "Improves email layout and readability.",
      "category": "email_design",
      "file": "email_design/visual_hierarchy_expert.yaml",
      "version": "1.0"
    }
  ]
}
```