import os
import logging
import json

from dotenv import load_dotenv
from typing import List, Dict, Optional
from groq import Groq
from pydantic import ValidationError
from schemas.gherkin import Feature, AcceptanceCriteria

logger = logging.getLogger(__name__)

load_dotenv()

class Llm_handler:
    def __init__(
            self,
            api_key: str=None,
            model_name: str="llama-3.3-70b-versatile",
            temperature: float=0.0,
            max_tokens: int=4096,
            seed: Optional[int]=42,
            **kwargs
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model_name = model_name

        if not self.api_key:
            logger.error("GROQ_API_KEY not found in environment or arguments.")
            raise ValueError("Missing GROQ_API_KEY")
        
        self.model_params = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "seed": seed,
            **kwargs
        }

        self.client = None
        logger.info(f"Initialzed groq handler with model: {self.model_name}")

    def _get_client(self):
        if self.client is None:
            try:
                self.client = Groq(api_key=self.api_key)
                logger.info(f"Sucessfully created groq client")
            except Exception as e:
                logger.error(f"Failed to create groq client: {str(e)}")
                raise
        return self.client
    
    def check_connection(self):
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Reply with only the word: OK"}
        ]
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=5,
                temperature=0.0
            )

            print(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return f"Error: Could not generate response."
        
    @staticmethod   
    def _strip_unwanted(raw:str) -> str:
        return (raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip())
    
    def generate_ac(self, message, max_retries:int=2) -> AcceptanceCriteria:
        """
        Stage 1:
        Story -> AcceptanceCriteria
        returns validated AcceptanceCriteria object. Retries on bad schema.
        """
        client = self._get_client()
        last_error = None
        for attempt in range(max_retries):
            response = client.chat.completions.create(
                model=self.model_name,
                messages=message,
                max_tokens=2048,
                temperature=0.0,
                seed=42,
                response_format={"type": "json_object"}
            )
            raw = self._strip_unwanted(raw=response.choices[0].message.content)
            try:
                data = json.loads(raw)
                return AcceptanceCriteria.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e
                logger.warning(f"Attempt {attempt+1} failed validation: {e}")
        raise last_error
    
    def generate_feature(self, messages, max_retries: int = 2) -> Feature:
        """
        Stage 2:
        AC -> Scenarios
        return validated Feature object. Retries on bad schema
        """
        client = self._get_client()
        last_error = None
        for attempt in range(max_retries):
            response = client.chat.completions.create(
                model=self.model_name, messages=messages,
                max_tokens=4096, temperature=0.0, seed=42,
                response_format={"type": "json_object"},
            )
            raw = self._strip_unwanted(raw=response.choices[0].message.content)
            try:
                data = json.loads(raw)
                return Feature.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e
                logger.warning(f"Attempt {attempt+1} failed validation: {e}")
        raise last_error

# if __name__=="__main__":
#     handler = Llm_handler()
#     handler.check_connection()

