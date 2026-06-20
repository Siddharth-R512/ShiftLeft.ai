from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional

"""
Gherkin Sample

@checkout
Feature: Shopping cart checkout
  As a shopper
  I want to pay for items in my cart
  So that I can complete my purchase

  Background:
    Given I am logged in
    And my cart has items

  @functional
  Scenario: Successful payment
    When I submit valid card details
    Then the order is confirmed

  @negative
  Scenario Outline: Payment fails with bad cards
    When I submit card "<number>"
    Then I see error "<message>"

    Examples:
      | number | message        |
      | 0000   | Invalid card   |
      | 1111   | Card declined  |

"""

class StepKeyword(str, Enum):
    given = "Given"
    when = "When"
    then = "Then"
    and_ = "And"
    but = "But"

class Step(BaseModel):
    keyword: StepKeyword
    text: str

class Examples(BaseModel):
    headers: List[str]
    rows: List[List[str]]

class Scenario(BaseModel):
    name: str
    tags: List[str] = Field(default_factory=list)
    is_outline: bool = False
    steps: List[Step]
    examples: Optional[Examples] = None

class Feature(BaseModel):
    name: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    background: Optional[List[Step]] = None
    scenarios: List[Scenario]
