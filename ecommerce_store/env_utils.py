import os

from django.core.exceptions import ImproperlyConfigured


def get_env_variable(variable_name):
    try:
        return os.environ[variable_name]
    except KeyError:

        raise ImproperlyConfigured(f"Set the {variable_name} environment variable.")
