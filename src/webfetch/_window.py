from __future__ import annotations
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl, urljoin
from typing import Any, Iterable
from lxml import html
from selenium.common.exceptions import JavascriptException
from ._constants import DEFAULT_WINDOW_ATTRIBUTES


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
    ):
        """Make a fetch request from the current page in Chrome with credentials (site cookies, etc).

        Args:
          method: The HTTP request verb; e.g. "GET", "POST", etc.
          url: The URL to send the request to.
          payload: The request body or parameters.
          headers: Additional headers; e.g. {"Content-Type": "application/json"}.

        Returns:
          A dictionary with the keys:
            status: The HTTP response status code.
            url: The URL ended up on after the request.
            data: Either the parsed JSON response or text content of the response body.
            html: The parsed HTML tree of the response content if an HTML document was detected.
        """
        method = method.upper()
        options = {"cache": "no-store", "credentials": "include", "headers": headers or {}}
        if method in ("POST", "PUT", "PATCH"):
            body = payload
            options["headers"]["Content-Type"] = "application/json"
        else:
            body = None
            if payload is not None:
                if isinstance(payload, list):
                    query = payload
                elif isinstance(payload, dict):
                    query = [(key, value) for key, value in payload]
                else:
                    query = []
                split = urlsplit(url)
                if split.query:
                    query.extend(parse_qsl(split.query))
                url_query = urlencode(payload) if len(query) == 0 else urlencode(query)
                url = urlunsplit((split.scheme, split.netloc, split.path, url_query, split.fragment))
        script = (
            "const opt = {method: arguments[0], ...arguments[2], body: arguments[3] && JSON.stringify(arguments[3])};"
            "const resp = await fetch(arguments[1], opt);"
            "const data = await resp.clone().json().catch(e => resp.text());"
            "return {data, status: resp.status, url: resp.url, html: null};"
        )
        response = self.run(script, method, url, options, body)
        if isinstance(response["data"], str):
            sample = response["data"][:256].lower()
            if sample.startswith("<!doctype html") or "<html" in sample:
                response["html"] = html.parse(response["data"])
        return response
