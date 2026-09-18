import os
import yaml
from datetime import datetime
from pathlib import Path

class ConfigFromYaml:
    """
    Converts a nested dictionary (from YAML) into a nested object with attribute access.
    
    This class allows accessing configuration values using dot notation (e.g., config.run.store_interim_files)
    instead of dictionary notation (e.g., config['run']['store_interim_files']).
    
    Arguments:
        data (dict): Nested dictionary containing configuration key-value pairs
    
    Returns:
        ConfigFromYaml object with attributes corresponding to dictionary keys
    """
    def __init__(self, data):
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, ConfigFromYaml(value))
            else:
                setattr(self, key, value)

def load_yaml_config(filepath):
    """
    Loads configuration from a YAML file and converts it to a ConfigFromYaml object.
    
    Arguments:
        filepath (str): Absolute or relative path to the YAML configuration file
    
    Returns:
        ConfigFromYaml: Object with nested attributes representing the YAML structure
    
    Raises:
        FileNotFoundError: If the YAML file doesn't exist at the specified path
        yaml.YAMLError: If the YAML file contains invalid syntax
    """
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    return ConfigFromYaml(data)

file_path = os.path.join(Path(__file__).resolve().parent.parent, 'config.yaml')
config = load_yaml_config(file_path)



