class AdmittedError(Exception):
    """Base Exception for the admitted package"""


class ChromeDriverVersionError(AdmittedError):
    """Problem during setup of ChromeDriver"""


class ChromeDriverServiceError(AdmittedError):
    """Problem with the ChromeDriver Service instance"""


class NavigationError(AdmittedError):
    """Problem navigating to a new page"""
