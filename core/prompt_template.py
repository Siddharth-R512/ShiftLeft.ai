from typing import List, Dict, Optional


def create_llm_messages(user_story: str, output_type: str = "Gherkin",
                        test_types=None) -> list[dict]:
    test_types = test_types or ["Functional"]
    type_hint = ", ".join(test_types)

    system_content = """You are an expert QA engineer specializing in BDD.
You output ONLY valid JSON matching the requested schema. No prose, no markdown fences."""

    user_content = f"""Convert this user story into BDD scenarios.

User Story:
{user_story}

Emphasize these test types via scenario tags: {type_hint}
(use lowercase tags: functional, negative, edge, regression)

Return a JSON object with exactly this structure:
{{
  "name": "feature name",
  "description": "As a... \\nI want... \\nSo that...",
  "tags": ["string"],
  "background": [{{"keyword": "Given", "text": "..."}}] or null,
  "scenarios": [
    {{
      "name": "scenario name",
      "tags": ["functional"],
      "is_outline": false,
      "steps": [{{"keyword": "Given|When|Then|And|But", "text": "..."}}],
      "examples": null
    }},
    {{
      "name": "data-driven scenario name",
      "tags": ["negative"],
      "is_outline": true,
      "steps": [{{"keyword": "When", "text": "I submit card \\"<number>\\""}},
                {{"keyword": "Then", "text": "I see error \\"<message>\\""}}],
      "examples": {{
        "headers": ["number", "message"],
        "rows": [["0000", "Invalid card"], ["1111", "Card declined"]]
      }}
    }}
  ]
}}
IMPORTANT: Use these EXACT key names, spelled exactly as shown:
"name", "description", "tags", "background", "scenarios", "steps", "keyword", "text", "is_outline", "examples".
Do not rename, abbreviate, or pluralize differently. 
The "description" must be exactly three lines in the form
"As a <role>", "I want <capability>", "So that <benefit>",
separated by \\n escape characters — not a single run-on sentence.

For Scenario Outlines, set "is_outline": true, reference placeholders in step text with <angle_brackets>, and provide a non-null "examples" object whose "headers" match those placeholders and whose "rows" each contain exactly one value per header. For regular scenarios, set "is_outline": false and "examples": null.

Include negative and edge cases. Use a Scenario Outline with examples for data-driven cases."""

    return [{"role": "system", "content": system_content},
            {"role": "user", "content": user_content}]

def create_llm_messages_ac(user_story: str) -> List[Dict[str, str]]:
    """
    Stage 1 prompt: user story -> acceptance criteria.
    Personality: be exhaustive about rules; do not write tests yet.
    """
    system_prompt = """You are an expert Quality Assurance (QA) Engineer.
Analyze the provided user story and enumerate every distinct, testable rule it implies."""

    user_prompt = f"""Output ONLY a valid JSON object. No markdown fences, no prose, no commentary.

Your job is COVERAGE, not test design. Enumerate every distinct, testable rule the
story implies: happy paths, boundaries, error conditions, and implicit expectations.
Each item is ONE rule stated as a verifiable condition. Do NOT write Given/When/Then
steps yet. Keep ids contiguous: AC1, AC2, AC3, ...

Strict output schema:
{{"items": [
  {{"id": "AC1", "text": "Detailed, testable acceptance criterion..."}},
  {{"id": "AC2", "text": "Detailed, testable acceptance criterion..."}}
]}}

USER STORY:
{user_story}"""

    return [{"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}]