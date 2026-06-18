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
    }}
  ]
}}

Include negative and edge cases. Use a Scenario Outline with examples for data-driven cases."""

    return [{"role": "system", "content": system_content},
            {"role": "user", "content": user_content}]