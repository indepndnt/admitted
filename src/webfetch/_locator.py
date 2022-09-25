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


def match_url(url1: str, url2: str) -> bool:
    """Report whether the domain, path, and query of both URLs match."""
    url_a = urlparse(url1)
    url_b = urlparse(url2)
    if url_a.path != url_b.path:
        return False
    host_a = url_a.netloc.split(".")
    host_b = url_b.netloc.split(".")
    if host_a[-2:] != host_b[-2:]:
        return False
    return url_a.query == url_b.query
