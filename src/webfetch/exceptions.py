class WebFetchError(Exception):
    """Base Exception for the webfetch package"""


class ChromeDriverVersionError(WebFetchError):
    """Problem during setup of ChromeDriver"""


class NavigationError(WebFetchError):
    """Problem navigating to a new page"""
