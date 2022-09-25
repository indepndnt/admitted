from __future__ import annotations
from lxml import html
from selenium.webdriver.support import expected_conditions as ec

from .manager import ChromeManager, Element

BY_XPATH = "xpath"
BY_NAME = "name"  # -> css, '[name="{name}"]'
BY_TAG = "tag name"
BY_CLASS = "class name"  # -> css, '.{class}'
BY_CSS = "css selector"


class Browser(ChromeManager):
    def request(
        self,
        method: str,
        url: str,
        payload: dict | list | str | None = None,
        headers: dict[str, str] | None = None,
    ):
        """Make a fetch request with credentials on the current page

        Args:
          method: Uppercase HTTP request verb; e.g. "GET", "POST", etc.
          url: The URL to send the request to.
          payload: The request body.
          headers: Additional headers; e.g. {"Content-Type": "application/json"}.

        Returns:
          A dictionary with the keys:
            status: The HTTP response status code.
            url: The URL ended up on after the request.
            data: Either the parsed JSON response or text content of the response body.
            html: The parsed HTML tree of the response content if an HTML document was detected.
        """
        options = {
            "cache": "no-cache",
            "mode": "no-cors",
            "credentials": "include",
            "headers": headers,
        }
        body = payload if method in ("POST", "PUT", "PATCH") else None
        script = (
            "const body = arguments[3] && JSON.stringify(arguments[3]);"
            "const opt = {method: arguments[0], ...arguments[2], body};"
            "const resp = await fetch(arguments[1], opt);"
            "const data = await resp.clone().json().catch(e => resp.text());"
            "return {data, status: resp.status, url: resp.url};"
        )
        response = self.window.run(script, method, url, options, body)
        if isinstance(response["data"], str) and response["data"].startswith("<!doctype html>"):
            response["html"] = html.parse(response["data"])
        else:
            response["html"] = None
        return response

    def css(self, selector: str, multiple: bool = False) -> Element | list[Element]:
        """Return the element with the given CSS selector.

        Args:
          selector: The css selector identifying the element.
          multiple: If true, return a list of all matching elements.

        Returns:
          An Element object of the discovered element.

        Raises:
          TimeoutException: No element matching the specified selector was found.
        """
        locator = (BY_CSS, selector)
        self.wait.until(ec.presence_of_element_located(locator))
        if multiple:
            return self.driver.find_elements(*locator)
        return self.driver.find_element(*locator)

    def xpath(self, path: str, multiple: bool = False) -> Element | list[Element]:
        """Return the element with the given XPath.

        Args:
          path: The XPath identifying the element.
          multiple: If true, return a list of all matching elements.

        Returns:
          An Element object of the discovered element.

        Raises:
          TimeoutException: No element matching the specified XPath was found.
        """
        locator = (BY_XPATH, path)
        self.wait.until(ec.presence_of_element_located(locator))
        if multiple:
            return self.driver.find_elements(*locator)
        return self.driver.find_element(*locator)

    def switch_id(self, *ids: str) -> Element:
        """Wait for any of several elements to become available and return the first one found.

        Args:
          ids: List of element IDs to watch for.

        Returns:
          The discovered WebElement.

        Raises:
          TimeoutException: No element with one of the specified IDs was found within the allotted time.
        """
        return self.css(", ".join([f'[id="{id_}"]' for id_ in ids]))
