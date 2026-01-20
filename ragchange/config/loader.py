import os
import yaml
from pathlib import Path


class ConfigLoader:
    """
    Loads configuration from YAML files.
    """
    def __init__(self):
        self.config_dir = Path(__file__).parent
        self._config_cache = {}
        self._config = self.load_config()
    
    def _load_yaml_config(self, filename):
        """ Load configuration from a YAML file. """
        # If this file was already loaded, serve the version from the cache
        if filename in self._config_cache:
            return self._config_cache[filename]
        
        # Check if the config file exists and load it
        config_path = self.config_dir / f"{filename}.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file {config_path} not found")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self._config_cache[filename] = config
        return config
    
    def _deep_merge(self, base: dict, override: dict):
        """Recursively merge override into base."""
        merged = base.copy()
        for key, value in override.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged
    
    def load_config(self):
        """Load and merge all configuration files."""
        default_config = self._load_yaml_config('defaults')
        local_config = self._load_yaml_config('local')
        merged_config = self._deep_merge(default_config, local_config)
        return merged_config
    
    def get(self, key, default=None):
        """Get a configuration parameter by key."""
        return self._config.get(key, default)


# Create a singleton instance for use throughout the application
# To get a config parameter, use: 
#   from config.loader import config # might need ragchange.config.loader
#   param = config.get('some_param')
config = ConfigLoader()

