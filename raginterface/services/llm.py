import logging
from any_llm import AnyLLM

from ragchange.config.loader import config

logger = logging.getLogger('raginterface')


class LLMService:
    """
    A service class to interact with different LLM providers using the any-llm API.
    Supports both synchronous and asynchronous operations.
    """
    
    def __init__(self):
        provider = config.get('llm_provider')
        api_key = config.get('llm_api_key')
        api_base = config.get('llm_api_base')
        api_base = None if api_base == '' else api_base
        
        self.model_name = config.get('llm_model')
        self.llm = AnyLLM.create(provider, api_key=api_key, api_base=api_base)
        
    def test(self):
        """Synchronous test of LLM service availability."""
        try:
            response = self.llm.completion(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, how are you?"}
                ],
                stream=False,
            )
            logger.info(f"LLM test response: {response.choices[0].message.content}\nContinuing")
            return response.choices[0].message.content
        except Exception as e:
            logger.exception("LLM test failed")
            return None

    def generate_response(self, prompt):
        """Synchronous response generation."""
        try:
            response = self.llm.completion(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a RAG system."},
                    {"role": "user", "content": prompt}
                ],
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.exception("Error during response generation")
            raise RuntimeError(f"An error occurred during response generation: {e}")

