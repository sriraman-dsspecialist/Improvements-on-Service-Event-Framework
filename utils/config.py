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

    def __getattr__(self, name):
        normalized_name = name.lower()
        for key, value in self.__dict__.items():
            if key.lower() == normalized_name:
                return value
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


def _normalize_path(path_value, base_dir=None):
    if path_value is None:
        return None

    text = str(path_value).strip()
    if not text:
        return base_dir or ""

    if base_dir is not None:
        text = text.replace("${base_dir}", str(base_dir)).replace("${BASE_DIR}", str(base_dir))

    value = text.replace("/", os.sep).replace("\\", os.sep)
    return os.path.normpath(value)


def _resolve_yaml_paths(data, base_dir):
    if isinstance(data, dict):
        resolved = {}
        for key, value in data.items():
            if key == "base_dir":
                resolved[key] = _normalize_path(value, base_dir)
            else:
                resolved[key] = _resolve_yaml_paths(value, base_dir)
        return resolved

    if isinstance(data, list):
        return [_resolve_yaml_paths(item, base_dir) for item in data]

    if isinstance(data, str):
        return _normalize_path(data, base_dir)

    return data


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

    base_dir = data.get("locations", {}).get("base_dir") or str(Path(filepath).resolve().parent)
    base_dir = _normalize_path(base_dir)
    data = _resolve_yaml_paths(data, base_dir)
    return ConfigFromYaml(data)

file_path = os.path.join(Path(__file__).resolve().parent.parent, 'config.yaml')
config = load_yaml_config(file_path)

# Ensure required data directories exist so the app can write outputs without manual setup.
for folder_key in ["inputs", "processed", "outputs"]:
    folder_path = getattr(config.locations, folder_key, None)
    if folder_path:
        Path(folder_path).mkdir(parents=True, exist_ok=True)



