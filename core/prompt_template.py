from typing import List, Dict, Optional

def create_optimal_prompt(
    user_story: str, 
    output_type: str = "Gherkin", 
    test_types: List[str] = None
) -> str:
    """
    Create an optimal prompt based on the output type (Gherkin or Test cases).
    
    Args:
        user_story: The user story/feature description
        output_type: Either "Gherkin" or "Test cases"
        test_types: List of test case types (e.g., ["Functional", "Edge Case", "Negative", "Regression"])
    
    Returns:
        A formatted prompt string for the LLM
    """
    if test_types is None:
        test_types = ["Functional"]
    
    if output_type == "Gherkin":
        prompt = f"""
You are a QA expert specializing in BDD (Behavior-Driven Development).
Convert the following user story into Gherkin scenarios (Given-When-Then format).

User Story:
{user_story}

Requirements:
- Create clear, concise scenarios
- Use proper Gherkin syntax (Feature, Scenario, Given, When, Then)
- Include multiple scenarios covering different user flows
- Ensure each step is testable

Gherkin Output:
"""
    else:  # Test cases
        test_types_str = ", ".join(test_types)
        prompt = f"""
You are a QA expert specializing in comprehensive test case design.
Create detailed test cases based on the following user story.

User Story:
{user_story}

Test Case Types to Generate:
{test_types_str}

Requirements:
- Create comprehensive test cases for each selected type
- Include Test ID, Title, Preconditions, Steps, Expected Results, and Actual Results
- Ensure test cases are independent and cover both positive and negative scenarios
- Include edge cases and boundary conditions where applicable

Test Cases Output:
"""
    
    return prompt


def create_llm_messages(
    user_story: str, 
    output_type: str = "Gherkin", 
    test_types: List[str] = None
) -> List[Dict[str, str]]:
    """
    Create messages list for LLM API calls with system and user roles.
    
    Args:
        user_story: The user story/feature description
        output_type: Either "Gherkin" or "Test cases"
        test_types: List of test case types (e.g., ["Functional", "Edge Case", "Negative", "Regression"])
    
    Returns:
        A list of message dictionaries with 'role' and 'content' keys
    """
    if test_types is None:
        test_types = ["Functional"]
    
    if output_type == "Gherkin":
        system_content = """You are an expert QA engineer specializing in Behavior-Driven Development (BDD) and Gherkin syntax.
Your task is to convert user stories into clear, executable Gherkin scenarios using Given-When-Then format.
Ensure scenarios are:
- Clear and concise
- Written in proper Gherkin syntax (Feature, Scenario, Given, When, Then, And, But)
- Testable and verifiable
- Covering main user flows and edge cases"""
        
        user_content = f"""Please convert the following user story into Gherkin scenarios:

User Story:
{user_story}

Generate comprehensive Gherkin scenarios that cover the main workflows and important edge cases."""
    
    else:  # Test cases
        test_types_str = ", ".join(test_types)
        system_content = """You are an expert QA engineer specializing in comprehensive test case design.
Your task is to create detailed, well-structured test cases based on user stories.
Ensure test cases are:
- Independent and self-contained
- Clearly documented with IDs, titles, and descriptions
- Comprehensive (covering positive, negative, and edge cases)
- Easily executable and verifiable"""
        
        user_content = f"""Please create detailed test cases for the following user story.

User Story:
{user_story}

Test Case Types to Generate: {test_types_str}

Include the following for each test case:
- Test ID
- Test Title
- Preconditions
- Test Steps (numbered)
- Expected Results
- Test Type (Functional/Edge Case/Negative/Regression)

Ensure comprehensive coverage of all scenarios."""
    
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]
    
    return messages