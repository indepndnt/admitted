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

        def try_login():
            # check if we're logged in, and log back in if not
            self.site.login()
            return False

        self._navigate(url=url, callback=try_login, retry_wait=3, retries_override=2)
        return self

    def _init_page(self) -> None:
        """Define the page object."""
        raise NotImplementedError
