from __future__ import annotations
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from . import _locator


class Element(WebElement):
    """Version of WebElement that returns self from click, clear, and send_keys."""

    def click(self) -> "Element":
        super().click()
        return self

    def clear(self) -> "Element":
        super().clear()
        # allow element to settle down before following up with a send_keys or other action
        time.sleep(0.1)
        return self

    def send_keys(self, *value) -> "Element":
        super().send_keys(*value)
        return self

    def css(
        self,
        selector: str,
        multiple: bool = False,
        mapping: dict[str, str] | None = None,
    ) -> "Element" | list["Element"]:
        """Return the element with the given CSS selector relative to this element.

        Args:
          selector: The css selector identifying the element.
          multiple: If true, return a list of all matching elements.
          mapping: If set, will be used to expand template values in selector.

        Returns:
          An Element object of the discovered element.

        Raises:
          TimeoutException: No element matching the specified selector was found.
        """
        return _locator.find_any(self.parent, By.CSS_SELECTOR, selector, multiple, mapping)

    def xpath(
        self,
        path: str,
        multiple: bool = False,
        mapping: dict[str, str] | None = None,
    ) -> "Element" | list["Element"]:
        """Return the element with the given XPath.

        Args:
          path: The XPath identifying the element.
          multiple: If true, return a list of all matching elements.
          mapping: If set, will be used to expand template values in path.

        Returns:
          An Element object of the discovered element.

        Raises:
          TimeoutException: No element matching the specified XPath was found.
        """
        return _locator.find_any(self.parent, By.XPATH, path, multiple, mapping)

    def scroll_to(self) -> None:
        self.parent.execute_script("arguments[0].scrollIntoView();", self)
        # for chaining we'd need to re-find the element bc the instance doesn't update the position
