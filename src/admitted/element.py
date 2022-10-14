from __future__ import annotations
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from . import _locator


class Element(WebElement):
    """Version of WebElement that returns self from click, clear, and send_keys."""

    # todo: handle `selenium.common.exceptions.ElementNotInteractableException: Message: element not interactable`,
    #   wait up to `wait` seconds? (apply to `clear`, `click`, and `send_keys`)
    def click(self, wait: int = 0) -> "Element":
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

    # todo: change `wait` to int, move wait here from `_manager` (apply to `css` and `xpath` here and on `BasePage`)
    def css(
        self,
        selector: str,
        wait: bool = True,
        multiple: bool = False,
        mapping: dict[str, str] | None = None,
    ) -> "Element" | list["Element"]:
        """Return the element with the given CSS selector relative to this element.

        Args:
          selector: The css selector identifying the element.
          wait: If true, wait for element to be present.
          multiple: If true, return a list of all matching elements.
          mapping: If set, will be used to expand template values in selector.

        Returns:
          An Element object of the discovered element.

        Raises:
          TimeoutException: No element matching the specified selector was found.
        """
        return _locator.find_any(self.parent, By.CSS_SELECTOR, selector, multiple, wait, mapping)

    def xpath(
        self,
        path: str,
        wait: bool = True,
        multiple: bool = False,
        mapping: dict[str, str] | None = None,
    ) -> "Element" | list["Element"]:
        """Return the element with the given XPath.

        Args:
          path: The XPath identifying the element.
          wait: If true, wait for element to be present.
          multiple: If true, return a list of all matching elements.
          mapping: If set, will be used to expand template values in path.

        Returns:
          An Element object of the discovered element.

        Raises:
          TimeoutException: No element matching the specified XPath was found.
        """
        return _locator.find_any(self.parent, By.XPATH, path, multiple, wait, mapping)

    # todo: add `switch_css` and `switch_xpath` here and on `BasePage`

    def scroll_to(self) -> None:
        self.parent.execute_script("arguments[0].scrollIntoView();", self)
        # for chaining we'd need to re-find the element bc the instance doesn't update the position
