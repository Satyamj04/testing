"""
mitmproxy addon for VAPT Agent.
Captures HTTP/HTTPS traffic and sends metadata to the backend API.
All traffic is scope-checked server-side before storage.

Usage:
    mitmdump -p 8080 -s mitm_addon.py
"""
import json
import time
import os
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import httpx
from mitmproxy import http, ctx
from mitmproxy.http import HTTPFlow

BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")
VAPT_TARGET_ID = os.environ.get("VAPT_TARGET_ID", "")
VAPT_SCAN_ID = os.environ.get("VAPT_SCAN_ID", "")
VAPT_API_TOKEN = os.environ.get("VAPT_API_TOKEN", "")

SENSITIVE_HEADERS = {
    "authorization", "cookie", "set-cookie", "x-api-key",
    "api-key", "x-auth-token", "password",
}


def mask_headers(headers: dict) -> dict:
    """Mask sensitive header values."""
    return {
        k: "****REDACTED****" if k.lower() in SENSITIVE_HEADERS else v
        for k, v in headers.items()
    }


class VAPTProxyAddon:
    """mitmproxy addon that captures and forwards traffic to VAPT backend."""

    def __init__(self):
        self._request_times: dict = {}
        self._client = None

    def _get_client(self):
        if not self._client:
            self._client = httpx.Client(timeout=5.0)
        return self._client

    def request(self, flow: HTTPFlow):
        """Record request start time."""
        self._request_times[flow.id] = time.monotonic()

    def response(self, flow: HTTPFlow):
        """Capture complete request/response and send to backend."""
        if not VAPT_TARGET_ID:
            return

        req = flow.request
        resp = flow.response

        start_time = self._request_times.pop(flow.id, time.monotonic())
        duration_ms = (time.monotonic() - start_time) * 1000

        # Skip internal traffic
        if req.host in ("backend", "localhost") and req.port in (8000, 9000):
            return

        try:
            req_body = req.content
            resp_body = resp.content if resp else b""

            payload = {
                "target_id": VAPT_TARGET_ID,
                "scan_id": VAPT_SCAN_ID or None,
                "method": req.method,
                "url": req.pretty_url,
                "host": req.host,
                "path": req.path,
                "query_string": req.query_string or None,
                "scheme": req.scheme,
                "port": req.port,
                "http_version": req.http_version,
                "request_headers": mask_headers(dict(req.headers)),
                "request_body": req_body.decode("utf-8", errors="replace")[:50000] if req_body else None,
                "request_body_size": len(req_body) if req_body else 0,
                "response_status": resp.status_code if resp else None,
                "response_headers": mask_headers(dict(resp.headers)) if resp else {},
                "response_body": resp_body.decode("utf-8", errors="replace")[:50000] if resp_body else None,
                "response_body_size": len(resp_body) if resp_body else 0,
                "response_content_type": resp.headers.get("content-type") if resp else None,
                "duration_ms": duration_ms,
                "source": "proxy",
                "captured_at": datetime.utcnow().isoformat(),
            }

            client = self._get_client()
            client.post(
                f"{BACKEND_URL}/api/v1/proxy/capture",
                json=payload,
                headers={"Authorization": f"Bearer {VAPT_API_TOKEN}"} if VAPT_API_TOKEN else {},
            )
        except Exception as e:
            ctx.log.warning(f"vapt_proxy_send_failed: {e}")

    def done(self):
        if self._client:
            self._client.close()


addons = [VAPTProxyAddon()]
