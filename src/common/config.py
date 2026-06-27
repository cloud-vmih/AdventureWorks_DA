import os
import yaml

def load_yaml(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def get_db_config(config_path="config/database.yml"):
    config = load_yaml(config_path)
    resolved_config = {}
    for db_key, db_settings in config.items():
        resolved_config[db_key] = {}
        for k, v in db_settings.items():
            # Resolve value from environment variable if it matches or is defined
            resolved_val = os.environ.get(v, v)
            # Fallback check
            if not resolved_val and v in os.environ:
                resolved_val = os.environ[v]
            resolved_config[db_key][k] = resolved_val
    return resolved_config

def get_macro_sources(config_path="config/macro_sources.yml"):
    return load_yaml(config_path)

def get_model_config(config_path="config/models.yml"):
    return load_yaml(config_path)
