from webfetch import site, page


class SiteTest(site.Site):
    def __init__(self, browser):
        self.browser = browser
        self.login_url = "https://www.example.com/login"
        self.credentials = {"username": "tester", "password": "secret"}
        self._init_login()

    def _init_login(self):
        self._authenticated = False

    def _do_login(self) -> "SiteTest":
        self._authenticated = True
        return self

    def is_authenticated(self) -> bool:
        return self._authenticated

    def _navigate(self, url, callback=None, retry_wait=10, retries_override=0, enforce_url=False) -> None:
        return


class PageTest(page.Page):
    def _init_page(self) -> None:
        self.status = "test"

    def _navigate(self, url, callback=None, retry_wait=10, retries_override=0, enforce_url=False) -> None:
        if callback:
            callback()
        return


def test_login(chromedriver):
    # Antecedent
    s = SiteTest(chromedriver)
    p = PageTest(s)

    # Behavior
    s.login()

    # Consequence
    assert p.site.is_authenticated() is True


def test_no_login(chromedriver):
    # Antecedent
    s = SiteTest(chromedriver)
    p = PageTest(s)

    # Behavior

    # Consequence
    assert p.site.is_authenticated() is False


def test_page_login(chromedriver):
    # Antecedent
    s = SiteTest(chromedriver)
    p = PageTest(s)

    # Behavior
    p.navigate("https://www.example.com/secret")

    # Consequence
    assert s.is_authenticated() is True
    assert p.status == "test"
