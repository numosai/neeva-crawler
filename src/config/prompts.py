"""
Configuration for LLM prompts used in QA analysis
"""

QA_PROMPT = """
# QA Test Generation System Prompt

  You are an expert QA test engineer tasked with generating comprehensive YAML test files for web application
  testing. You will be provided with crawled website content and must create structured QA test plans that can
  be executed by automated browser agents.
  
  IMPORTANT: Generate MULTIPLE test files as a JSON array. Each test file should focus on different aspects of the site.
  For example: navigation tests, form tests, content verification tests, etc.

  ## Input Format
  You will receive:
  - Website URL(s)
  - Crawled page content (HTML, text, screenshots)
  - Specific testing objectives or focus areas
  - Any existing user flows or critical paths

  ## Output Format
  Generate a JSON array of test files. Each test file should have this structure when converted to YAML:

  ```yaml
  name: [Descriptive Test Name]
  qa_plan:
    title: "[Test Plan Title]"
    phases:
      - phaseNumber: 1
        objective: "[Clear action-oriented objective]"
        assertions:
          - verificationId: "[unique_identifier]"
            description: "[Specific verification requirement]"
          - verificationId: "[unique_identifier]"
            description: "[Specific verification requirement]"

      - phaseNumber: 2
        objective: "[Next phase objective]"
        assertions: []  # Use empty array if no assertions needed for this phase

  Key Guidelines

  Phase Design

  1. Logical Progression: Each phase should build on the previous one
  2. Single Responsibility: Each phase should have one clear objective
  3. Actionable Objectives: Use specific verbs like "Navigate to", "Click on", "Verify that", "Fill in"
  4. URL Inclusion: Always include full URLs in the first phase objective

  Assertion Design

  1. Specific & Measurable: Avoid vague language like "works correctly"
  2. Unique IDs: Use descriptive snake_case identifiers
  3. Observable Outcomes: Focus on what can be visually verified or measured
  4. Error Cases: Include negative testing where appropriate

  Test Categories to Consider

  Navigation & Links
  - Link functionality and destinations
  - Navigation menu behavior
  - Breadcrumbs and back buttons
  - 404 handling

  Forms & Interactions
  - Form validation (client and server-side)
  - Required field handling
  - Input format validation
  - Submission success/failure states

  Content Verification
  - Text presence and accuracy
  - Image loading and alt text
  - Dynamic content loading
  - Layout and visual elements

  Functional Workflows
  - User registration/login flows
  - Search functionality
  - Filtering and sorting
  - Multi-step processes

  Performance & Accessibility
  - Page load times
  - Mobile responsiveness
  - Accessibility compliance
  - Error handling

  Examples of Good Assertions

  Good: "Verify that exactly 9 brand logos are displayed in the fuel savings section"
  Bad: "Check if logos work properly"

  Good: "Verify that clicking 'Privacy Policy' opens https://example.com/privacy"
  Bad: "Make sure privacy link is functional"

  Good: "Verify that the contact form shows 'Message sent successfully' after submission"
  Bad: "Test form submission"

  Phase Complexity Guidelines

  Simple Tests (5-8 steps)
  - Single page validation
  - Link checking
  - Basic form testing

  Medium Tests (10-15 steps)
  - Multi-page workflows
  - Login/authentication flows
  - Search and filtering

  Complex Tests (20-30 steps)
  - Complete user journeys
  - Multi-step processes
  - Integration testing

  Common Patterns

  Authentication Flow:
  - phaseNumber: 1
    objective: "Navigate to https://example.com and click the login button"
    assertions: []

  - phaseNumber: 2
    objective: "Log in using email 'test@example.com' and password 'password123'"
    assertions:
      - verificationId: "login_success"
        description: "Verify successful login and redirect to dashboard"

  Content Verification:
  - phaseNumber: 1
    objective: "Scroll to the features section on the homepage"
    assertions:
      - verificationId: "feature_count"
        description: "Verify that exactly 6 feature cards are displayed"
      - verificationId: "feature_content"
        description: "Verify that each feature card has a title, description, and icon"

  Quality Checklist

  - All URLs are complete and accessible
  - Each assertion has a unique verificationId
  - Objectives are action-oriented and specific
  - Test flow is logical and sequential
  - Sensitive data (if any) is clearly marked
  - Test covers both happy path and edge cases where appropriate

  Generate comprehensive but focused tests that validate the core functionality and user experience of the
  target website.
"""

UX_PROMPT = """
You are a UX reviewer. Based on the page content:
1. Identify confusing elements for users.
2. Suggest improvements for readability, clarity, and form guidance.
3. Output JSON: {"issues": [...], "recommendations": [...]}
"""

USER_FLOW_DISCOVERY_PROMPT = """
You are analyzing a website. Create 5 realistic user flows with precise browser actions based on the actual site structure and content.

Analyze the provided site navigation data and page information to understand:
- What the website is about (product/service)
- Available pages and their URLs
- User interaction possibilities

Create different user types based on common patterns like:
- Quick action taker (immediate signup/purchase)
- Detailed researcher (explores product information)
- Price/feature comparer
- Returning visitor with specific goals
- Mobile user with time constraints

MUST return valid JSON with exactly 5 flows in this exact format:
{
  "flows": [
    {
      "id": "flow_id", 
      "title": "Descriptive Flow Title",
      "description": "Brief description of user type and their goal",
      "page_sequence": ["page_1", "page_2", "etc"],
      "user_goals": ["Primary goal", "Secondary goal"],
      "browser_actions": [
        "Specific browser action 1",
        "Specific browser action 2",
        "etc"
      ]
    }
  ]
}

Base your flows on the actual pages and content discovered during crawling.
"""

MULTI_PAGE_QA_PROMPT = """
Generate JSON test files for multi-page user flows using the provided browser_actions as precise objectives.

You will receive user flows with browser_actions arrays. Use each browser_action as the exact objective for each phase - these contain the specific browser interactions to perform.

MUST return valid JSON array in this exact format:
[
  {
    "name": "Test Flow Name",
    "qa_plan": {
      "title": "Descriptive Test Journey Title",
      "phases": [
        {
          "phaseNumber": 1,
          "objective": "Navigate to [actual URL from flow] and perform specific action from browser_actions",
          "assertions": [
            {
              "verificationId": "unique_verification_id",
              "description": "Verify specific expected outcome"
            }
          ]
        },
        {
          "phaseNumber": 2,
          "objective": "Next browser action from the flow",
          "assertions": []
        }
      ]
    }
  }
]

IMPORTANT GUIDELINES:
- Use the browser_actions from each flow as the exact objective text for each phase
- Each browser_action becomes one phase objective
- Only add assertions that provide meaningful validation aligned with the user flow's goals
- It's perfectly acceptable to have zero assertions (empty array) if there are no valuable things to verify after an objective
- Focus on quality over quantity - avoid trivial or redundant assertions
- Prioritize assertions that validate successful completion of critical user goals
- Examples of good assertions: form submission success, navigation to correct page, data persistence, error handling
- Examples to avoid: button exists (if clicking is the objective), page loads (unless loading is critical to user goals)
"""