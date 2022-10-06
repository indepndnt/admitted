from __future__ import annotations
import re
import string
from urllib.parse import urlparse
from selenium.webdriver.support import expected_conditions as ec

template_pattern = re.compile(r"\$\{\w+\}")


def find_any(driver, by: str, target: str, multiple: bool, mapping: dict[str, str] | None):
    """Find element(s) globally or locally according to provided attributes.

    Args:
      driver: WebDriver (for global) or WebElement (for local) object to search.
      by: Instance of selenium.webdriver.common.by.By (or e.g. "css selector"/"xpath").
      target: The selector/path/etc as indicated by `by`.
      multiple: True to return a list of matching results, otherwise an error will be raised if no element found.
      mapping: A dictionary of template values to replace in `target` if templating is to be used.

    Example:
      To find an element like <div id="example">...</div> from within a Site or Page instance:
      element = find_any(self.browser, By.CSS, 'div[id="${div_id}"]', False, {"div_id": "example"})
    """
    if mapping is not None:
        locator = (by, expand_locator(target, mapping))
    else:
        locator = (by, target)
    driver.wait.until(ec.presence_of_element_located(locator))
    if multiple:
        return driver.find_elements(*locator)
    return driver.find_element(*locator)


def expand_locator(target: str, mapping: dict[str, str]) -> str:
    """Get XPath or selector, expanding templated strings where necessary"""
    match = template_pattern.search(target)
    if match:
        target = string.Template(target).substitute(mapping)
    return target


def match_url(url1: str, url2: str, ignore_query: bool = False, path_substr: bool = False) -> bool:
    """Report whether the domain, path, and query of both URLs match.

    Examples:
      These evaluate to True:
        match_url("https://www.example.com/home?q=1", "https://example.com/home?q=1")
        match_url("https://www.example.com/home", "https://example.com/home?q=1", ignore_query=True)
        match_url("https://example.com/app/home/page", "https://example.com/home", path_substr=True)

      These evaluate to False:
        match_url("https://www.example.com/home", "https://example.com/home?q=1")
        match_url("https://www.example.com", "https://example.com/home?q=1", ignore_query=True)
        match_url("https://example.com/app/page", "https://example.com/home", path_substr=True)
    """
    url_a = urlparse(url1)
    url_b = urlparse(url2)
    path_a, path_b = url_a.path, url_b.path
    if (path_substr is False and path_a != path_b) or (path_substr is True and path_b not in path_a):
        return False
    host_a = url_a.hostname.split(".")
    host_b = url_b.hostname.split(".")
    if host_a[-2:] != host_b[-2:]:
        return False
    return ignore_query or url_a.query == url_b.query
