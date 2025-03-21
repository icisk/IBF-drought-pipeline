import logging
import os
from enum import Enum
from dotenv import load_dotenv
import json
import yaml
from urllib.parse import urlparse


def is_url(x):
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


class SecretsSource(Enum):
    env = "env"
    json = "json"
    yaml = "yaml"


class Secrets:
    """
    Secrets (API keys, tokens, etc.)
    """

    def __init__(self, path_or_url=".env", source=None):

        if source is None:
            if is_url(path_or_url):
                source = "azure"
            elif path_or_url.split(".")[-1] in [e.value for e in SecretsSource]:
                source = path_or_url.split(".")[-1]
        self.secret_source = SecretsSource(source)
        self.secret_path = path_or_url
        self.secrets = None
        self.load_secrets()

    def load_secrets(self):
        if self.secret_source is SecretsSource.env:
            load_dotenv(self.secret_path)
        elif self.secret_source is SecretsSource.json:
            with open(self.secret_path) as file:
                self.secrets = json.load(file)
                for k, v in self.secrets.items():
                    setattr(self, k, v)
        elif self.secret_source is SecretsSource.yaml:
            self.secrets = yaml.load(self.secret_path, Loader=yaml.FullLoader)

    def get_secret(self, secret):
        secret_value = None
        if self.secret_source is SecretsSource.env:
            secret_value = os.getenv(secret)
        elif self.secret_source is SecretsSource.json:
            if secret in self.secrets.keys():
                secret_value = self.secrets[secret]
        elif self.secret_source is SecretsSource.yaml:
            if secret in self.secrets.keys():
                secret_value = self.secrets[secret]
        elif self.secret_source is SecretsSource.azure:
            secret_value = self.secrets.get_secret(secret).value
        else:
            raise ValueError(f"Cannot get secrets from {self.secret_path}")
        if secret_value is None:
            raise ValueError(f"Secret {secret} not found in {self.secret_path}")
        return secret_value

    def check_secrets(self, secrets):
        missing_secrets = []
        for secret in secrets:
            try:
                self.get_secret(secret)
            except ValueError:
                missing_secrets.append(secret)
        if missing_secrets:
            logging.info(f"Missing secrets {', '.join(missing_secrets)}")
            # raise Exception(
            #     f"Missing secrets {', '.join(missing_secrets)} in {self.secret_path}"
            # )
