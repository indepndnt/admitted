from __future__ import annotations
import logging
from ._base import BasePage

logger = logging.getLogger(__name__)


class Page(BasePage):
    """Represents a page on a web site."""

    def __init__(self, site):
        """Initialize Page instance attributes as member of `site`.

        Args:
          site (Site): Instance of a Site subclass.
        """
        super().__init__(browser=site.browser)
        self.site = site
        self._init_page()

    def navigate(self, url: str) -> "Page":
        """Load the page, repeating login if necessary.

        Args:
          url: The URL to navigate to.

        Returns:
          The current class instance.
        """

        def try_login(retry: int):
            # we'll detour to login only the first time
            if retry == 1:
                # if we're already logged in, don't risk redirecting to login page
                if not self.site.is_authenticated():
                    # try to log back in and return False to retry navigating to our page
                    self.site.login()
            # returning True would override the failure status that resulted in this being called - if we
            # succeeded logging in, we still want another retry to get to where we were originally navigating
            return False

        self._navigate(url=url, callback=try_login)
        return self

    def _init_page(self) -> None:
        """Define the page object."""
        raise NotImplementedError
