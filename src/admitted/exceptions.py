class AdmittedError(Exception):
    """Base Exception for the admitted package"""


class ChromeDriverVersionError(AdmittedError):
    """Problem during setup of ChromeDriver"""


class NavigationError(AdmittedError):
    """Problem navigating to a new page"""
