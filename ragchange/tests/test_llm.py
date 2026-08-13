import os
from django.test import TestCase, SimpleTestCase

# Create your tests here.
class Llm_Test(SimpleTestCase):
        
    def test_llm_completion(self):
        from ragchange.config.loader import config
        from raginterface.services.llm import LLMService
        
        llm_service = LLMService()
        test_response = llm_service.test()
        assert test_response is not None, "LLM test response should not be None"