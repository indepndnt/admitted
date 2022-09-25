from __future__ import annotations
import time
from selenium.common.exceptions import WebDriverException
from .browser import Browser
from .exceptions import NavigationError


class BasePage:
    """Represents a page on a web site."""


class Site(BasePage):
    """Represents a particular web site."""

    def __init__(self, login_url: str, credentials: dict[str, str]):
        self.browser = Browser()
        self.browser.navigate(login_url)
        self.login_url = login_url
        self.credentials = credentials
        self._init_login()

    def _init_login(self):
        """Define the login page object.

        Example:
          self.username_selector = "#username"
          self.password_selector = "#password"
          self.submit_selector = "#login-button"
        """
        raise NotImplementedError

    def login(self) -> "Page":
        """Authenticate to the site.

        Example:
          self.browser.css(self.username_selector).clear().send_keys(self.credentials['username'])
          self.browser.css(self.password_selector).clear().send_keys(self.credentials['password'])
          self.browser.css(self.submit_selector).click()
          return Page(self)
        """
        raise NotImplementedError

    def is_authenticated(self) -> bool:
        """Check if authentication is current.

        Example:
          return self.browser.window["localStorage.accessToken"] is not None
        """
        raise NotImplementedError


class Page(BasePage):
    """Represents a page on a web site."""

    def __init__(self, site: Site, url: str):
        self.site = site
        self.original_url = url
        self._navigate(url=url)
        self._init_page()

    def _navigate(self, url: str):
        """Load the page, repeating login if necessary."""
        retry = 0
        last_exception = None
        while True:
            # load the url
            try:
                self.site.browser.driver.get(url)
            except WebDriverException as exc:
                last_exception = exc
            # if we got where we were going, we're done!
            if self.site.browser.driver.current_url.startswith(url):
                break
            # if we've exhausted retries, raise the error
            if retry >= 2:
                raise NavigationError(f"Failed navigating to {url}") from last_exception
            # check if we're logged in, and log back in if not
            if not self.site.is_authenticated():
                self.site.login()
            # pause with exponential backoff
            retry += 1
            pause = 3 * (retry**2)
            time.sleep(pause)

    def _init_page(self):
        """Define the page object."""
        raise NotImplementedError
