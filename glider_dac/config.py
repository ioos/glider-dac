"""
Configuration module so that other DB connection, etc. can access configuration
in addition to the main Flask application
"""
import os.path
import logging
import yaml

def get_config() -> dict:
    cur_dir = os.path.dirname(__file__)
    with open(os.path.join(cur_dir, '..', 'config.yml')) as base_config:
        config = yaml.load(base_config, Loader=yaml.Loader)

    extra_config_path = os.path.join(cur_dir, '..', 'config.local.yml')
    # merge in settings from config.local.yml, if it exists
    # TODO: Why does this not recognize top-level import when run in gunicorn?
    # config.local.yml, if it exists
    if os.environ.get("FLASK_ENV") != "TESTING" and os.path.exists(extra_config_path):
        with open(extra_config_path) as extra_config:
            config = {**config, **yaml.load(extra_config,
                                            Loader=yaml.Loader)}
    try:
        config.update(config[os.environ["FLASK_ENV"]])
    except KeyError:
        logging.error(f"Cannot find config for {os.environ.get('ENV', None)}, "
                          "falling back to DEVELOPMENT")
        config.update(config["DEVELOPMENT"])


    # TODO: move to config YAML instead?
    config['SWAGGER'] = {
        'title': 'glider-dac',
        'uiversion': 3,
        'openapi': '3.0.2'
    }

    return config
