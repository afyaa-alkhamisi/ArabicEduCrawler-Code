import os
import json


class ConfigMiddleware:
    """
    Middleware that injects site-specific configuration into request.meta
    and allows spiders to fetch the config directly.
    """

    _configs = None  # class-level cache to avoid reloading

    def __init__(self):
        if ConfigMiddleware._configs is None:
            config_path = os.path.join(
                os.path.dirname(__file__), '..', 'configs', 'sites_config.json'
            )
            with open(config_path, encoding='utf-8') as f:
                ConfigMiddleware._configs = json.load(f)
        self.configs = ConfigMiddleware._configs

    def process_request(self, request, spider):
        """
        Attach site_config to the request meta before sending.
        Ensures response.meta always has safe access.
        """
        try:
            domain = request.url.split('/')[2]
            site_config = self.configs.get(domain, {})
            request.meta['site_config'] = site_config
        except IndexError:
            request.meta['site_config'] = {}
        return None

    @classmethod
    def get_site_config(cls, domain: str) -> dict:
        """
        Helper method for spiders to fetch site_config without a request.
        """
        if cls._configs is None:
            # Should never happen, but fallback if middleware not initialized
            config_path = os.path.join(
                os.path.dirname(__file__), '..', 'configs', 'sites_config.json'
            )
            with open(config_path, encoding='utf-8') as f:
                cls._configs = json.load(f)
        return cls._configs.get(domain, {})
