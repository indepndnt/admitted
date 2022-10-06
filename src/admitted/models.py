from __future__ import annotations
from http import HTTPStatus
import json
from typing import BinaryIO, Any
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl
from lxml import html

# noinspection PyProtectedMember
from lxml.etree import _Element
import urllib3

# noinspection PyProtectedMember
from urllib3._collections import HTTPHeaderDict


class Request:
    """HTTP Request object to give a consistent API whether to window.fetch or outside_request.

    Args:
      method: The HTTP request verb; e.g. "GET", "POST", etc.
      url: The address of the resource to return.
      payload: The request body or query parameters.
      headers: Additional headers; e.g. {"Content-Type": "application/json"}.
      stream: Requestor intends to stream response. Not used for window.fetch.
      json_args: Arguments to pass to .json() or json.dumps() if payload requires serialization.
      kwargs: Additional arguments to pass to request method. Not used for window.fetch.
    """

    def __init__(
        self,
        method: str,
        url: str,
        payload: Any = None,
        headers: dict[str, str] | None = None,
        *,
        stream: bool = False,
        json_args: dict[str, Any] | None = None,
        **kwargs,
    ):
        self.method = method.upper()
        self.url = url
        self.headers = HTTPHeaderDict([] if headers is None else headers.items())
        json_args = {} if json_args is None else json_args
        if self.method in ("GET", "HEAD", "DELETE", "TRACE"):
            if payload is not None:
                if not any((isinstance(payload, t) for t in (dict, list))):
                    raise TypeError(f"Invalid payload type ({type(payload).__name__}) for {self.method} requests.")
                self._query_params(payload)
        elif self.method in ("POST", "PUT", "PATCH", "OPTIONS"):
            if payload is not None:
                self._request_body(payload, json_args)
        elif self.method in ("CONNECT",):
            raise TypeError("CONNECT is not supported by this method.")
        else:
            raise TypeError(f"Invalid HTTP verb '{self.method}'.")
        self.preload_content = not stream
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"<Request {vars(self)}>"

    def _request_body(self, payload: Any, kwargs: dict[str, Any]):
        if hasattr(payload, "json"):
            self.body = payload.json(**kwargs)
            content_type = "application/json"
        elif any((isinstance(payload, t) for t in (dict, list))):
            self.body = json.dumps(payload, **kwargs)
            content_type = "application/json"
        else:
            self.body = payload
            content_type = "text/plain" if isinstance(payload, str) else "application/octet-stream"
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = content_type

    def _query_params(self, query: dict | list) -> None:
        if isinstance(query, dict):
            query = list(query.items())
        split = urlsplit(self.url)
        if split.query:
            # noinspection PyTypeChecker
            query.extend(parse_qsl(split.query))
        url_query = urlencode(query)
        self.url = urlunsplit((split.scheme, split.netloc, split.path, url_query, split.fragment))


class Response:
    """HTTP Response object to give a consistent API whether from window.fetch or outside_request."""

    def __init__(self, *, url: str, status: int, reason: str, headers: HTTPHeaderDict):
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
        if self._content is None:
            self._content = getattr(self._urllib3_http_response, "data", None) or b""
        return self._content

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
