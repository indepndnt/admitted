from __future__ import annotations
import re
import string
import time
from typing import TYPE_CHECKING
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

if TYPE_CHECKING:
    from admitted._executables._manager import ChromeManager
    from admitted.element import Element

# noinspection RegExpRedundantEscape
template_pattern = re.compile(r"\$\{\w+\}")


class Locator:
    def __init__(self):
        raise NotImplementedError

    @property
    def parent(self) -> "ChromeManager":
        raise NotImplementedError

    def css(
        self,
        selector: str,
        wait: float = 15.0,
        multiple: bool = False,
        mapping: dict[str, str] | None = None,
    ) -> Element | list[Element] | None:
        """Return the element with the given CSS selector.

        Args:
          selector: The css selector identifying the element.
          wait: Watch for element to be present for up to {wait} seconds.
          multiple: If true, return a list of all matching elements.
          mapping: If set, will be used to expand template values in selector.

        Returns:
          An Element object of the discovered element.

        Raises:
          TimeoutException: No element matching the specified selector was found.
        """
        locator = (By.CSS_SELECTOR, expand_locator(selector, mapping))
        return self._find(locator, wait, multiple)

    def xpath(
        self,
        path: str,
        wait: float = 15.0,
        multiple: bool = False,
        mapping: dict[str, str] | None = None,
    ) -> Element | list[Element] | None:
        """Return the element with the given XPath.

        Args:
          path: The XPath identifying the element.
          wait: Watch for element to be present for up to {wait} seconds.
          multiple: If true, return a list of all matching elements.
          mapping: If set, will be used to expand template values in path.

        Returns:
          An Element object of the discovered element.

        Raises:
          TimeoutException: No element matching the specified XPath was found.
        """
        locator = (By.XPATH, expand_locator(path, mapping))
        return self._find(locator, wait, multiple)

    def _find(self, locator: tuple[str, str], timeout: float, multiple: bool) -> Element | list[Element] | None:
        """Process find options common between `css` and `xpath`"""
        elements = self._find_maybe_wait(locator, timeout)
        if multiple:
            # if we wanted multiple we return the list of zero or longer length
            return elements
        # if we wanted a single element with zero wait, we return None if it's not found
        return elements[0] if elements else None

    def _find_maybe_wait(self, locator: tuple[str, str], timeout: float) -> list[Element]:
        """Wait for matching elements to be found or raise TimeoutException"""
        # if `self` has `find_elements` then we're an Element, otherwise we are a BasePage
        finder = getattr(self, "find_elements", self.parent.find_elements)
        if timeout <= 0:
            # returns Element, not WebElement, because _web_element_cls is set on the ChromeManager class.
            # noinspection PyTypeChecker
            return finder(*locator)
        end_time = time.monotonic() + timeout
        while True:
            elements = finder(*locator)
            if elements:
                # noinspection PyTypeChecker
                return elements
            time.sleep(0.2)
            if time.monotonic() > end_time:
                raise TimeoutException(f"Time expired waiting for {locator[0]} '{locator[1]}'.")

    def css_checkbox(self, target_selector: str, input_selector: str, value: bool, *, timeout: float = 15.0) -> None:
        """Set a checkbox `checked` property.

        Args:
          target_selector: CSS selector for the element to click to toggle the checkbox.
          input_selector: CSS selector for the `input` element to read the current value.
          value: Desired status of the `checked` attribute.
          timeout: Number of seconds to continue trying to set the checkbox.

        Raises:
          TimeoutException: Failed to set the checkbox.
        """
        end_time = time.monotonic() + timeout
        while True:
            checked_attr = self.css(input_selector).get_attribute("checked")
            is_checked = checked_attr == "true"
            if is_checked is value:
                return
            if time.monotonic() > end_time:
                raise TimeoutException(f"Time expired {'' if value else 'un-'}checking '{input_selector}'.")
            self.css(target_selector).click()
            time.sleep(0.2)

    def xpath_checkbox(self, target_path: str, input_path: str, value: bool, *, timeout: float = 15.0) -> None:
        """Set a checkbox `checked` property.

        Args:
          target_path: XPath for the element to click to toggle the checkbox.
          input_path: XPath for the `input` element to read the current value.
          value: Desired status of the `checked` attribute.
          timeout: Number of seconds to continue trying to set the checkbox.

        Raises:
          TimeoutException: Failed to set the checkbox.
        """
        end_time = time.monotonic() + timeout
        while True:
            checked_attr = self.xpath(input_path).get_attribute("checked")
            is_checked = checked_attr == "true"
            if is_checked is value:
                return
            if time.monotonic() > end_time:
                raise TimeoutException(f"Time expired {'un-' if value else ''}checking '{input_path}'.")
            self.xpath(target_path).click()
            time.sleep(0.2)

    def css_input(
        self,
        target_selector: str,
        input_selector: str | None,
        value: str,
        *,
        timeout: float = 30.0,
        scroll_first: bool = True,
        click_first: bool | str = True,
        clear_first: bool | str = False,
        ignore_zeroes: bool = False,
        send_after: str = "",
    ) -> None:
        """Set the value of an input field.

        Args:
          target_selector: CSS selector for the element to send key presses to.
          input_selector: CSS selector for the `input` element to read the current value.
          value: Desired content of the `input` element.
          timeout: Number of seconds to continue trying to enter the value.
          scroll_first: True to scroll to the element before entering value.
          click_first: True to click target element (or another specified css selector) before entering value.
          clear_first: True to clear input element (or another specified css selector) before entering value.
          ignore_zeroes: Whether to accept e.g. "1.70" == "1.7" as success.
          send_after: Text or keystrokes to send after completing the value input.

        Raises:
          TimeoutException: Failed to set the checkbox.
        """
        if not input_selector:
            input_selector = target_selector
        actions = [
            (scroll_first, input_selector, "scroll_to"),
            (click_first, target_selector, "click"),
            (clear_first, input_selector, "clear"),
            (target_selector, "send_keys", value),
            (target_selector, "send_keys", send_after),
            (input_selector, value, ignore_zeroes),
        ]
        self._element_input(By.CSS_SELECTOR, actions, timeout)

    def xpath_input(
        self,
        target_path: str,
        input_path: str | None,
        value: str,
        *,
        timeout: float = 30.0,
        scroll_first: bool = True,
        click_first: bool | str = True,
        clear_first: bool | str = False,
        ignore_zeroes: bool = False,
        send_after: str = "",
    ) -> None:
        """Set the value of an input field.

        Args:
          target_path: XPath for the element to send key presses to.
          input_path: XPath for the `input` element to read the current value.
          value: Desired content of the `input` element.
          timeout: Number of seconds to continue trying to enter the value.
          scroll_first: True to scroll to the element before entering value.
          click_first: True to click target element (or another specified XPath) before entering value.
          clear_first: True to clear input element (or another specified XPath) before entering value.
          ignore_zeroes: Whether to accept e.g. "1.70" == "1.7" as success.
          send_after: Text or keystrokes to send after completing the value input.

        Raises:
          TimeoutException: Failed to set the checkbox.
        """
        if not input_path:
            input_path = target_path
        actions = [
            (scroll_first, input_path, "scroll_to"),
            (click_first, target_path, "click"),
            (clear_first, input_path, "clear"),
            (target_path, "send_keys", value),
            (target_path, "send_keys", send_after),
            (input_path, value, ignore_zeroes),
        ]
        self._element_input(By.XPATH, actions, timeout)

    def _element_input(self, by: str, actions: list[tuple], timeout) -> None:
        end_time = time.monotonic() + timeout
        while True:
            self._element_action(by, *actions[0])
            if self._input_compare(by, *actions[5]):
                return
            if time.monotonic() > end_time:
                raise TimeoutException(f"Time expired setting '{actions[5][0]}' to '{actions[5][1]}'.")
            self._element_action(by, *actions[1])
            self._element_action(by, *actions[2])
            self._element_action(by, True, *actions[3])
            if actions[4][2]:
                time.sleep(0.05)
                self._element_action(by, True, *actions[4])
            time.sleep(0.2)

    def _element_action(self, by: str, enable_or_target: bool | str, target: str, method: str, arg=None):
        if enable_or_target is True:
            pass
        elif isinstance(enable_or_target, str):
            target = enable_or_target
        else:
            return
        element = self._find((by, target), 10.0, False)
        func = getattr(element, method)
        if arg is None:
            func()
        else:
            func(arg)
        time.sleep(0.2)

    def _input_compare(self, by: str, target: str, expected_value: str, ignore_zeroes: bool) -> bool:
        current_value = self._find((by, target), 10.0, False).text
        if current_value == expected_value:
            return True
        if ignore_zeroes is True:
            int_part, _, frac_part = expected_value.partition(".")
            short_value = ".".join((int_part.lstrip("0"), frac_part.rstrip("0")))
            if current_value == short_value:
                return True
        return False


def expand_locator(target: str, mapping: dict[str, str] | None) -> str:
    """Get XPath or selector, expanding templated strings where necessary"""
    if mapping is None:
        return target
    match = template_pattern.search(target)
    if match:
        target = string.Template(target).substitute(mapping)
    return target
