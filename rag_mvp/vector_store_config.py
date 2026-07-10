import os
from urllib.parse import urljoin, urlparse

from qdrant_client import QdrantClient

try:
    import config
except Exception:
    config = None


DEFAULT_QDRANT_URL = "http://127.0.0.1:6333"
DEFAULT_QDRANT_TIMEOUT = 120
DEFAULT_COLLECTION_NAME = "personal_knowledge_base"

LOCAL_NO_PROXY_HOSTS = ["localhost", "127.0.0.1", "::1"]


def _get_config_value(name: str, default):
    """
    Read a value from config.py if it exists.

    config.py may be ignored by git in local deployments, so vector_store_config
    must still work when config.py is missing.
    """
    if config is None:
        return default

    return getattr(config, name, default)


def _first_non_empty(*values, default: str) -> str:
    for value in values:
        text = str(value or "").strip()

        if text:
            return text

    return default


def _env_int(name: str, default: int) -> int:
    """
    Read an integer from environment variables.
    """
    try:
        return int(os.environ.get(name, str(default)))
    except Exception:
        return default


def get_qdrant_url() -> str:
    """
    Return the configured Qdrant URL without a trailing slash.

    Priority:
    1. PKB_QDRANT_URL environment variable
    2. config.QDRANT_URL
    3. DEFAULT_QDRANT_URL
    """
    raw_url = _first_non_empty(
        os.environ.get("PKB_QDRANT_URL"),
        _get_config_value("QDRANT_URL", DEFAULT_QDRANT_URL),
        default=DEFAULT_QDRANT_URL,
    )

    return raw_url.rstrip("/")


def get_qdrant_timeout(default: int = DEFAULT_QDRANT_TIMEOUT) -> int:
    """
    Return the configured Qdrant timeout in seconds.

    Priority:
    1. PKB_QDRANT_TIMEOUT environment variable
    2. config.QDRANT_TIMEOUT
    3. default
    """
    if "PKB_QDRANT_TIMEOUT" in os.environ:
        return _env_int("PKB_QDRANT_TIMEOUT", default)

    try:
        return int(_get_config_value("QDRANT_TIMEOUT", default))
    except Exception:
        return default


def get_collection_name() -> str:
    """
    Return the configured Qdrant collection name.

    Priority:
    1. PKB_QDRANT_COLLECTION environment variable
    2. config.COLLECTION_NAME
    3. DEFAULT_COLLECTION_NAME
    """
    return _first_non_empty(
        os.environ.get("PKB_QDRANT_COLLECTION"),
        _get_config_value("COLLECTION_NAME", DEFAULT_COLLECTION_NAME),
        default=DEFAULT_COLLECTION_NAME,
    )


def get_qdrant_hostname(url: str | None = None) -> str:
    """
    Return the hostname portion of the configured Qdrant URL.
    """
    parsed = urlparse(url or get_qdrant_url())
    return parsed.hostname or ""


def _split_no_proxy(value: str) -> list[str]:
    """
    Split a NO_PROXY/no_proxy value into normalized host entries.
    """
    return [item.strip() for item in value.split(",") if item.strip()]


def configure_qdrant_environment(url: str | None = None) -> None:
    """
    Add the configured Qdrant host to NO_PROXY/no_proxy.

    Do not remove HTTP_PROXY/HTTPS_PROXY/ALL_PROXY because those variables may be
    needed by GitHub, external APIs, company proxies, or other tools.
    """
    hosts: list[str] = []

    for key in ("NO_PROXY", "no_proxy"):
        hosts.extend(_split_no_proxy(os.environ.get(key, "")))

    for host in LOCAL_NO_PROXY_HOSTS:
        if host not in hosts:
            hosts.append(host)

    hostname = get_qdrant_hostname(url)
    if hostname and hostname not in hosts:
        hosts.append(hostname)

    no_proxy = ",".join(hosts)
    os.environ["NO_PROXY"] = no_proxy
    os.environ["no_proxy"] = no_proxy


def get_qdrant_client(timeout: int | None = None) -> QdrantClient:
    """
    Create a Qdrant client using the shared vector-store configuration.
    """
    configure_qdrant_environment()

    return QdrantClient(
        url=get_qdrant_url(),
        check_compatibility=False,
        timeout=timeout if timeout is not None else get_qdrant_timeout(),
    )


def get_qdrant_rest_url(path: str = "") -> str:
    """
    Build a Qdrant REST URL from the configured base URL.
    """
    base_url = get_qdrant_url() + "/"
    return urljoin(base_url, path.lstrip("/"))


QDRANT_URL = get_qdrant_url()
COLLECTION_NAME = get_collection_name()
