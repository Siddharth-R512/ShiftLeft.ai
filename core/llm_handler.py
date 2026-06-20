import os
import logging
import json

from dotenv import load_dotenv
from typing import List, Dict, Optional
from groq import Groq
from pydantic import ValidationError
from schemas.gherkin import Feature

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

    def generate_output(self, message, output_type: str = "Gherkin"):
        """
        Stream the LLM output token by token.
        Yields text chunks as they're received from the API.
        
        Args:
            message: List of message dictionaries with 'role' and 'content'
            output_type: Either "Gherkin" or "Test cases" for dynamic max_tokens
        
        Yields:
            str: Text chunks from the LLM response
        """
        # Dynamic max_tokens based on output type
        max_tokens = 4096 if output_type == "Test cases" else 2048
        
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model_name,
                messages=message,
                max_tokens=max_tokens,
                temperature=0.0,
                seed=42
            )

            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error during streaming: {str(e)}")
            return f"Error: Could not generate response. {str(e)}"
        
    def generate_feature(self, messages, max_retries: int = 2) -> Feature:
        client = self._get_client()
        last_error = None
        for attempt in range(max_retries):
            response = client.chat.completions.create(
                model=self.model_name, messages=messages,
                max_tokens=4096, temperature=0.0, seed=42,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
            raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
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

