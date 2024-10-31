from __future__ import annotations
import logging
import time
from typing import Callable
from warnings import warn
from selenium.common.exceptions import WebDriverException
from . import _locator, _url, _window
from .element import Element
from .exceptions import NavigationError
from admitted._executables import _manager

logger = logging.getLogger(__name__)


class BasePage(_locator.Locator):
    """Represents a page on a web site."""

    # noinspection PyMissingConstructor
    def __init__(self, browser: _manager.ChromeManager, *, retries: int = 3, debug: bool = False):
        """Initialize common class attributes

        Args:
          browser: ChromeManager instance representing Chrome window.
          retries: Number of times the `navigate` method should try to open the requested URL.
          debug: If True, will output chromedriver.log on the desktop and suppress retries.
        """
        self.browser = browser
        self.window = _window.Window(self.browser)
        self.direct_request = _url.direct_request
        self.retries = 0 if debug else retries

    @property
    def parent(self):
        """Connect Locator methods to the WebDriver instance"""
        return self.browser

    def switch_id(self, options: dict[str, Callable[[Element], Element]]) -> Element:
        """Wait for any of several elements to become available and return the first one found.

        Args:
          options: Dictionary where keys are element IDs to watch for and values are the callback for when
            that key is found.

        Returns:
          The return value from the callback, which should be the discovered WebElement.

        Raises:
          TimeoutException: No element with one of the specified IDs was found within the allotted time.
        """
        warn("The method `switch_id` is being deprecated. Use CSS like '@{id}, @{id}'.", PendingDeprecationWarning, 2)
        ids = options.keys()
        selector = ", ".join([f'[id="{id_}"]' for id_ in ids])
        element = self.css(selector)
        found = element.get_property("id")
        return options[found](element)

    @property
    def current_url(self):
        """Return the current URL that Chrome is on."""
        return self.browser.current_url

    def _navigate(
        self,
        url: str,
        *,
        callback: Callable[[int], bool] | None = None,
        retry_wait: int = 2,
        retries_override: int | None = None,
        enforce_url: bool | str = True,
        abort_url: str | None = None,
        **match_kwargs,
    ) -> None:
        """Navigate Chrome to the specified URL, retrying with exponential back-off.

        Args:
          url: The URL to navigate to.
          callback: Function to call before pause and retry, return True if navigation complete.
            Receives the attempt counter which starts at 1.
          retry_wait: Number of seconds to wait for first retry if initial navigation fails.
          retries_override: Number of times to attempt navigation, if other than instance default required.
          enforce_url: True or the expected URL to consider it an error if current_url != url after navigation.
          match_kwargs: Additional arguments to modify URL enforcement; see _url.match_url.
        """
        retries = self.retries if retries_override is None else retries_override
        retry = 0
        while True:
            try:
                self.browser.get(url)
                # if we don't care where we end up, we're done!
                if not enforce_url:
                    break
                # if we got where we were going, we're done!
                expected_url = enforce_url if isinstance(enforce_url, str) else url
                if _url.match_url(self.current_url, expected_url, **match_kwargs):
                    break
                # give the user context in the traceback if we exhaust retries
                raise NavigationError(
                    f"Wrong destination: Expected URL {expected_url}; current URL is {self.current_url}."
                )
            except (WebDriverException, NavigationError) as exc:
                logger.debug("Error on try %s: %s.", retry, exc)
                last_exception = exc
            retry += 1
            # check if callback signals exit
            if callback is not None and callback(retry):
                break
            # check for short circuit
            if abort_url and _url.match_url(self.current_url, abort_url, **match_kwargs):
                break
            # if we've exhausted retries, raise the error
            if retry > retries:
                raise NavigationError(f"Failed after {retry} tries navigating to {url}.") from last_exception
            pause = retry_wait * (retry**2)
            time.sleep(pause)
