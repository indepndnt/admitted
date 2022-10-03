from __future__ import annotations
from http import HTTPStatus
import json
from typing import BinaryIO
from lxml import html
from lxml.etree import _Element  # noqa=PyProtectedMember
import urllib3
from urllib3._collections import HTTPHeaderDict  # noqa=PyProtectedMember


class Response:
    """HTTP Response object to give a consistent API whether from window.fetch or outside_request."""

    def __init__(self, url: str, status: int, reason: str, headers: HTTPHeaderDict):
        self.url = url
        self.status_code = status
        self.reason = reason
        self.headers = headers
        self.ok: bool = 200 <= status < 300
        self._content: bytes | None = None
        self._text: str | None = None
        self._html: _Element | None = None
        self._json: dict | list | None = None
        self._fetch_raw_response: dict | None = None
        self._urllib3_http_response: urllib3.HTTPResponse | None = None

    @classmethod
    def from_fetch(cls, fetch: dict) -> "Response":
        if "error" in fetch:
            reason = f"{fetch['error']['name']}: {fetch['error']['message']}"
            headers = None
        else:
            reason = fetch["reason"] or HTTPStatus(fetch["status"]).name
            headers = HTTPHeaderDict(fetch.get("headers", []))
        instance = cls(url=fetch.get("url", ""), status=fetch.get("status", 0), reason=reason, headers=headers)
        instance._fetch_raw_response = fetch
        instance._content = bytes(fetch.get("body", []))
        instance._text = fetch.get("text")
        instance._json = fetch.get("json")
        return instance

    @classmethod
    def from_urllib3(cls, response: urllib3.HTTPResponse) -> "Response":
        instance = cls(url=response.geturl(), status=response.status, reason=response.reason, headers=response.headers)
        instance._urllib3_http_response = response
        return instance

    @property
    def content(self) -> bytes:
        if self._content is not None:
            return self._content
        if self._urllib3_http_response:
            self._content = self._urllib3_http_response.data or b""
            return self._content
        if self._text:
            self._content = self._text.encode("utf8")
            return self._content
        return b""

    @property
    def text(self) -> str:
        if self._text is None:
            self._text = self.content.decode("utf8")
        return self._text

    @property
    def html(self) -> _Element | None:
        if self._html is None:
            sample = self.text[:256].lower()
            if sample.startswith("<!doctype html") or "<html" in sample:
                self._html = html.fromstring(self.text)
        return self._html

    @property
    def json(self) -> dict | list | None:
        if self._json is None:
            try:
                self._json = json.loads(self.content)
            except json.JSONDecodeError:
                pass
        return self._json

    def write_stream(self, destination: BinaryIO, chunk_size: int = 1024) -> BinaryIO:
        if self._urllib3_http_response:
            for chunk in self._urllib3_http_response.stream(chunk_size):
                destination.write(chunk)
        else:
            destination.write(self.content)
        return destination
