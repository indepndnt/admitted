from __future__ import annotations
import json
from string import Template
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl
from typing import Any, Iterable
from selenium.common.exceptions import JavascriptException
from ._constants import DEFAULT_WINDOW_ATTRIBUTES
from .models import Response

FETCH_SCRIPT = """
const r = await fetch('${url}', ${options}).catch(e => e);
if (typeof r.clone !== 'function') return {error: {name: e.name, message: e.message}};
const headers = [];
for ([h, v] of r.headers.entries()) {headers.push([h, v])};
const body = new Uint8Array(await r.clone().arrayBuffer().catch(e => null));
const text = await r.clone().text().catch(e => null);
const json = await r.clone().json().catch(e => null);
return {url: r.url, status: r.status, reason: r.statusText, headers, body, text, json};
"""


class Window:
    """Class to manage accessing global variables from the Chrome console.

    Example:
      local_storage = site.window["localStorage"]  # get all values from the current site's local storage

    Methods:
      run: Shortcut to WebDriver.execute_script.
      new_keys: List the difference between default Chrome `window` attributes and current `window` attributes.
      scroll_to_top: Scroll the window to the top of the page.
      fetch: Make an http request from the current page in Chrome with credentials if same origin.
    """

    _fetch_script = Template(FETCH_SCRIPT)

    def __init__(self, driver):
        # shortcut to enable e.g. chrome.window.run("javascript", arg=val)
        self.run = driver.execute_script

    def __getitem__(self, item: str) -> Any:
        """Return global variables from the current page."""
        variable = item if item.startswith("[") else f".{item}"
        try:
            value = self.run(f"return window{variable};")
        except JavascriptException:
            value = None
        return value

    def new_keys(self) -> Iterable[str]:
        """List the difference between default Chrome `window` attributes and current `window` attributes."""
        attribs = set(self.run("return Object.keys(window);"))
        added = attribs.difference(DEFAULT_WINDOW_ATTRIBUTES)
        return sorted(added)

    def scroll_to_top(self) -> None:
        """Scroll the window to the top of the page."""
        self.run("window.scrollTo(0, 0);")

    def fetch(
        self,
        method: str,
        url: str,
        payload: dict | list | str | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Make a fetch request from the current page in Chrome with credentials (site cookies, etc).

        Args:
          method: The HTTP request verb; e.g. "GET", "POST", etc.
          url: The URL to send the request to.
          payload: The request body or parameters.
          headers: Additional headers; e.g. {"Content-Type": "application/json"}.

        Returns:
          A Response object.
        """
        method = method.upper()
        options = {"method": method, "cache": "no-store", "credentials": "include", "headers": headers or {}}
        if method in ("POST", "PUT", "PATCH"):
            options["headers"]["Content-Type"] = "application/json"
            options["body"] = json.dumps(payload)
        elif payload is not None:
            if isinstance(payload, list):
                query = payload
            elif isinstance(payload, dict):
                query = list(payload.items())
            else:
                query = []
            split = urlsplit(url)
            if split.query:
                query.extend(parse_qsl(split.query))
            url_query = urlencode(payload) if len(query) == 0 else urlencode(query)
            url = urlunsplit((split.scheme, split.netloc, split.path, url_query, split.fragment))
        script = self._fetch_script.safe_substitute({"options": json.dumps(options), "url": url})
        response = self.run(script)
        # for debugging, script available as `response._fetch_raw_response["script"]`
        response["script"] = script
        return Response.from_fetch(response)
