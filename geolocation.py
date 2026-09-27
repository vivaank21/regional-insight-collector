"""
geolocation.py
---------------
Server-side IP detection and approximate geolocation lookup.

The raw IP address is handled entirely on the server. Nothing in this
module should ever be passed back to the browser as-is.
"""

import ipaddress
import logging

import requests
from flask import request

from config import Config

logger = logging.getLogger("regional_insight")

UNKNOWN_LOCATION = {
    "country": "Unknown",
    "region": "Unknown",
    "state": "Unknown",
    "city": "Unknown",
    "timezone": "Unknown",
}

# Private/reserved ranges we don't bother sending to the geolocation API
# (e.g. localhost during development). These will simply resolve to
# "Unknown" rather than wasting an external request.
_PRIVATE_NETWORKS = [
    ipaddress.ip_network(net)
    for net in (
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "::1/128",
        "fc00::/7",
    )
]


def _is_private(ip_str):
    try:
        ip_obj = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return any(ip_obj in net for net in _PRIVATE_NETWORKS)


def get_client_ip():
    """
    Determine the visitor's IP address.

    By default we trust only `request.remote_addr`, which Werkzeug sets
    from the actual TCP connection and cannot be spoofed by a client.

    If TRUST_PROXY_HEADERS is enabled in config (meaning the app is
    deployed behind a *known* reverse proxy), the app should be wrapped
    with werkzeug's ProxyFix middleware (see app.py) so that
    request.remote_addr is correctly rewritten from X-Forwarded-For by a
    trusted, bounded number of hops. This function deliberately does NOT
    read X-Forwarded-For itself, to avoid blindly trusting arbitrary
    client-supplied headers.
    """
    ip = request.remote_addr or "0.0.0.0"
    return ip


def get_location(ip_address):
    """
    Look up approximate geolocation data for an IP address.

    Returns a dict with keys: country, region, state, city, timezone.
    Any failure (timeout, bad response, private IP, rate limit, etc.)
    results in the UNKNOWN_LOCATION dict rather than raising, so the
    caller can always proceed with a graceful fallback.
    """
    # In development mode with mock geolocation enabled, return mock data
    # for localhost addresses to enable testing without a public IP.
    if Config.DEV_MODE_MOCK_GEOLOCATION and _is_private(ip_address):
        logger.info(
            "Development mode: returning mock geolocation for private IP %s",
            ip_address,
        )
        return {
            "country": "India",
            "region": "Maharashtra",
            "state": "Maharashtra",
            "city": "Mumbai",
            "timezone": "Asia/Kolkata",
        }

    if not ip_address or _is_private(ip_address):
        logger.info("Skipping geolocation lookup for private/local IP.")
        return dict(UNKNOWN_LOCATION)

    try:
        response = requests.get(
            f"{Config.GEOLOCATION_API_URL.rstrip('/')}/{ip_address}",
            params={"fields": "status,message,country,regionName,city,timezone"},
            timeout=Config.GEOLOCATION_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()

        if payload.get("status") != "success":
            logger.warning(
                "Geolocation API returned failure status: %s",
                payload.get("message", "unknown reason"),
            )
            return dict(UNKNOWN_LOCATION)

        region_name = payload.get("regionName") or "Unknown"

        return {
            "country": payload.get("country") or "Unknown",
            # This provider doesn't separate "region" (e.g. a multi-state
            # zone) from "state"; we surface the same admin-1 division
            # under both fields so downstream code has both available.
            "region": region_name,
            "state": region_name,
            "city": payload.get("city") or "Unknown",
            "timezone": payload.get("timezone") or "Unknown",
        }

    except requests.exceptions.Timeout:
        logger.error("Geolocation API request timed out for IP lookup.")
    except requests.exceptions.RequestException as exc:
        logger.error("Geolocation API request failed: %s", exc)
    except ValueError:
        logger.error("Geolocation API returned invalid JSON.")
    except Exception as exc:  # pragma: no cover - defensive catch-all
        logger.error("Unexpected error during geolocation lookup: %s", exc)

    return dict(UNKNOWN_LOCATION)
