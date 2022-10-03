import pytest
from webfetch import site, page


class SiteTest(site.Site):
    def __init__(self, browser):
        self.browser = browser
        self.login_url = "https://www.example.com/login"
        self.credentials = {"username": "tester", "password": "secret"}
        self.retries = 1
        self._init_login()

    def _init_login(self):
        self.browser._authenticated = False

    def _do_login(self) -> "SiteTest":
        self.browser._authenticated = True
        return self

    # we override _navigate only to ensure retry_wait is zero so tests don't take forever
    def _navigate(self, url, callback=None, *, retry_wait=2, **kwargs):
        super()._navigate(url, callback, retry_wait=0, **kwargs)

    # we put an _authenticated flag in the mock chromebrowser to simulate non-auth redirects.
    def is_authenticated(self) -> bool:
        return self.browser._authenticated is True


class PageTest(page.Page):
    def _init_page(self) -> None:
        self.status = "test"

    # use the overridden _navigate we defined in SiteTest
    @property
    def _navigate(self):
        return self.site._navigate


def test_login(chromedriver):
    # Antecedent: objects instantiated
    s = SiteTest(chromedriver)
    p = PageTest(s)

    # Behavior: call the login method
    s.login()

    # Consequence: site._do_login has been called
    assert p.site.is_authenticated() is True


def test_no_login(chromedriver):
    # Antecedent: objects instantiated
    s = SiteTest(chromedriver)
    p = PageTest(s)

    # Behavior: exists

    # Consequence: site._do_login has not been called
    assert p.site.is_authenticated() is False


def test_page_login(chromedriver):
    # Antecedent: objects instantiated
    s = SiteTest(chromedriver)
    p = PageTest(s)

    # Behavior: navigate to a url
    p.navigate("https://www.example.com/secret")

    # Consequence: site._do_login and page._init_page have been called
    assert s.is_authenticated() is True
    assert p.status == "test"


def test_base_site_methods_not_implemented():
    # Antecedent: Site instance created
    s = object.__new__(site.Site)

    # Behavior: call abstract methods
    with pytest.raises(NotImplementedError):
        s._init_login()
    with pytest.raises(NotImplementedError):
        s._do_login()
    with pytest.raises(NotImplementedError):
        s.is_authenticated()

    # Consequence: NotImplementedError raised


def test_base_page_methods_not_implemented():
    # Antecedent: Page instance created
    p = object.__new__(page.Page)

    # Behavior: call abstract methods
    with pytest.raises(NotImplementedError):
        p._init_page()

    # Consequence: NotImplementedError raised
