from __future__ import annotations
import time
from selenium.webdriver.remote.webelement import WebElement
from . import _locator


class Element(WebElement, _locator.Locator):
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

    def scroll_to(self) -> None:
        self.parent.execute_script("arguments[0].scrollIntoView();", self)
        # for chaining we'd need to re-find the element bc the instance doesn't update the position
