import os
from django.test import TestCase, SimpleTestCase

# Create your tests here.
class Config_Test(SimpleTestCase):
    
    def test_env_loading(self):
        import os
        SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
        DJANGO_DEBUG = os.environ.get('DJANGO_DEBUG')
        ALLOWED_HOSTS = [host for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if host]
        self.assertIsInstance(SECRET_KEY, str)
        self.assertIn(DJANGO_DEBUG, ('True', 'False'))
        self.assertIsInstance(ALLOWED_HOSTS, list)
        
    def test_yaml_config_loading(self):
        from ragchange.config.loader import config
        necessary_params = {
            'llm_provider': str,
            'llm_model': str,
            'record_data': bool,
            'embedding_model': str,
            'vector_db_path': str,
            'vector_db_collection': str,
            'n_results': int,
            'data_source_path': str,
        }
        for param, type_ in necessary_params.items():
            assert config.get(param) is not None
            assert isinstance(config.get(param), type_)