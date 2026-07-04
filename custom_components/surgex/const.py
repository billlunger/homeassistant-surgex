"""Constants for the SurgeX integration."""

from datetime import timedelta

DOMAIN = "surgex"

CONF_BASE_URL = "base_url"
CONF_HOST = "host"
CONF_PASSWORD = "password"
CONF_PORT = "port"
CONF_SSL = "ssl"
CONF_USERNAME = "username"

DEFAULT_NAME = "SurgeX"
DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = timedelta(seconds=15)
