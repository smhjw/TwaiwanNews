from __future__ import annotations

import base64
import hashlib
import hmac
import time
import urllib.parse
from typing import Any

import requests


class DingTalkBot:
    def __init__(self, webhook: str, secret: str = "", timeout: int = 10):
        self._webhook = webhook
        self._secret = secret
        self._timeout = timeout
        self._session = requests.Session()

    def _signed_webhook(self) -> str:
        if not self._secret:
            return self._webhook
        timestamp = str(round(time.time() * 1000))
        to_sign = f"{timestamp}\n{self._secret}"
        sign_bytes = hmac.new(
            self._secret.encode("utf-8"),
            to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(sign_bytes))
        sep = "&" if "?" in self._webhook else "?"
        return f"{self._webhook}{sep}timestamp={timestamp}&sign={sign}"

    def send_markdown(self, title: str, text: str) -> dict[str, Any]:
        payload = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": text},
        }
        resp = self._session.post(
            self._signed_webhook(), json=payload, timeout=self._timeout
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"DingTalk HTTP {resp.status_code}: {resp.text}")
        data = resp.json()
        if str(data.get("errcode", "0")) != "0":
            raise RuntimeError(f"DingTalk API error: {data}")
        return data
