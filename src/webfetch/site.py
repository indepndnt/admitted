from __future__ import annotations
import logging
from ._base import BasePage
from ._locator import match_url
from ._manager import ChromeManager

logger = logging.getLogger(__name__)


class Site(BasePage):
    """Represents a particular web site and one ChromeDriver instance."""

    def __init__(self, login_url: str, credentials: dict[str, str], timeout: int = 30, debug: bool = False):
        """Initialize ChromeDriver and Site instance attributes.

        Args:
          login_url: This site's login page.
          credentials: Dictionary defining credential values required by _do_login.
          timeout: Default timeout in seconds for wait operations.
          debug: If True, will output chromedriver.log on the desktop and suppress retries.
        """
        super().__init__(ChromeManager(timeout=timeout, debug=debug))
        self.login_url = login_url
        self.credentials = credentials
        self._init_login()
        self._navigate(url=login_url)

    def _init_login(self):
        """Define the login page object.

        Example:
          self.username_selector = "#username"
          self.password_selector = "#password"
          self.submit_selector = "#login-button"
        """
        raise NotImplementedError

    def _do_login(self) -> "Site":
        """Authenticate to the site.

        Example:
          self.css(self.username_selector).clear().send_keys(self.credentials['username'])
          self.css(self.password_selector).clear().send_keys(self.credentials['password'])
          self.css(self.submit_selector).click()
          return self
        """
        raise NotImplementedError

    def login(self) -> "Site":
        """Navigate to login page and authenticate to the site, unless already logged in."""
        if self.is_authenticated():
            return self
        # if domain and path match the login url assume we're where we need to be
        # ignoring subdomains and query means we could be sent to auth.example.com/login?returnTo=somePage
        # and we won't lose the redirect by navigating to the bare login page
        if not match_url(self.current_url, self.login_url, ignore_query=True):
            self._navigate(url=self.login_url)
        return self._do_login()

    def is_authenticated(self) -> bool:
        """Check if authentication is current.

        Example:
          return self.window["localStorage.accessToken"] is not None
        """
        raise NotImplementedError
