import pytest
from selenium.common.exceptions import WebDriverException
from webfetch._manager import ChromeManager


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    """Remove request method for all tests so we don't make network requests from tests."""
    monkeypatch.delattr("urllib3.request.RequestMethods.request")


@pytest.fixture(autouse=True)
def no_chromedriver(monkeypatch):
    """Remove request method for all tests so we don't make network requests from tests."""
    monkeypatch.delattr("selenium.webdriver.common.service.Service.start")


@pytest.fixture(autouse=True)
def no_subprocess(monkeypatch):
    """Remove run method for all tests so we don't make network requests from tests."""
    monkeypatch.delattr("subprocess.run")


@pytest.fixture()
def chromedriver():
    class Mock(ChromeManager):
        def __init__(self):
            self._current_url = "https://www.example.com"
            self.session_id = "test"
            self.callback_was_called = 0
            self._authenticated = None

        class wait:
            @staticmethod
            def until(method):
                return method

        def _execute(self, command, params):
            return

        def execute_script(self, **kwargs):
            return kwargs

        @property
        def current_url(self):
            return self._current_url

        def get(self, url):
            if url.endswith("fail"):
                raise WebDriverException
            if url.endswith("change"):
                self._current_url = url.replace("change", "new")
            elif url.endswith("secret") and not self._authenticated:
                self._current_url = url.replace("secret", "blocked")
            else:
                self._current_url = url

        def find_any(self, driver, by, target, multiple, mapping):
            return self.MockElement(driver, by, target, multiple, mapping)

        class MockElement:
            def __init__(self, driver, by, target, multiple, mapping):
                self.id = "id_one"
                self.driver = driver
                self.by = by
                self.target = target
                self.multiple = multiple
                self.mapping = mapping

            def get_property(self, item):
                if item != "id":
                    raise TypeError("I think you wrote this test wrong.")
                return self.id

    return Mock()
