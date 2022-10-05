import pytest
from admitted import site, page


class SiteTest(site.Site):
    def __init__(self, url, login_now=False):
        super().__init__(url, {"username": "tester", "password": "secret"}, immediate_login=login_now)

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
        # noinspection PyUnresolvedReferences,PyProtectedMember
        return self.browser._authenticated is True


class PageTest(page.Page):
    def _init_page(self) -> None:
        self.status = "test"

    # use the overridden _navigate we defined in SiteTest
    # noinspection PyMethodOverriding
    @property
    def _navigate(self):
        # noinspection PyProtectedMember
        return self.site._navigate


def test_login(chromedriver, urls):
    # Antecedent: set up environment
    SiteTest._chrome_manager_class = chromedriver

    # Behavior: instantiate and call the login method
    s = SiteTest(urls.login, login_now=True)
    p = PageTest(s)

    # Consequence: site._do_login has been called
    assert p.site.is_authenticated() is True


def test_skip_login(urls):
    # Antecedent: a Site instance
    # noinspection PyAbstractClass
    class SkipSite(site.Site):
        current_url = urls.origin

        # noinspection PyMissingConstructor
        def __init__(self):
            self.login_url = self.current_url
            self.test_authenticated = False

        def _do_login(self):
            self.test_authenticated = True
            return False

        def is_authenticated(self):
            return self.test_authenticated

    instance = SkipSite()

    # Behavior: call site.login() twice
    first_call = instance.login()
    second_call = instance.login()

    # Consequence: first call calls _do_login() (returning False), second call early-returns `self`
    assert first_call is False
    assert second_call is instance


def test_no_login(chromedriver, urls):
    # Antecedent: objects instantiated
    SiteTest._chrome_manager_class = chromedriver
    s = SiteTest(urls.login)
    p = PageTest(s)

    # Behavior: exists

    # Consequence: site._do_login has not been called
    assert p.site.is_authenticated() is False


def test_page_navigate_login(chromedriver, urls):
    # Antecedent: objects instantiated
    SiteTest._chrome_manager_class = chromedriver
    s = SiteTest(urls.login)
    p = PageTest(s)

    # Behavior: navigate to a url
    p.navigate(urls.secret)

    # Consequence: Page instantiated (page._init_page was called); failed to open protected page and redirected
    #   to login (site._do_login was called); then finally loaded to requested page
    assert p.status == "test"
    assert s.is_authenticated() is True
    # noinspection TimingAttack
    assert p.current_url == urls.secret


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

    # Consequence: NotImplementedError was raised


def test_base_page_methods_not_implemented():
    # Antecedent: Page instance created
    p = object.__new__(page.Page)

    # Behavior: call abstract methods
    with pytest.raises(NotImplementedError):
        p._init_page()

    # Consequence: NotImplementedError was raised
