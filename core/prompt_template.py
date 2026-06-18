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
  "description": "As a... I want... So that...",
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

For Scenario Outlines, set "is_outline": true, reference placeholders in step text with <angle_brackets>, and provide a non-null "examples" object whose "headers" match those placeholders and whose "rows" each contain exactly one value per header. For regular scenarios, set "is_outline": false and "examples": null.

Include negative and edge cases. Use a Scenario Outline with examples for data-driven cases."""

    return [{"role": "system", "content": system_content},
            {"role": "user", "content": user_content}]