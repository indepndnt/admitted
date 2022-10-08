import pytest
from selenium.common.exceptions import WebDriverException

# noinspection PyProtectedMember
from admitted._manager import ChromeManager

URL = "https://www.example.com"


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
def urls():
    class URLs:
        origin = URL
        naked = URL.replace("s://www.", "://")
        sub = URL.replace("www.", "www.sub.")
        login = f"{URL}/login"
        # noinspection HardcodedPassword
        secret = f"{URL}/secret"
        test = f"{URL}/test"
        fail = f"{URL}/fail"
        change = f"{URL}/change"

    return URLs()


class MockElement:
    def __init__(self, _driver, _by, _target, _multiple, _mapping):
        self.id = "id_one"
        self.driver = _driver
        self.by = _by
        self.target = _target
        self.multiple = _multiple
        self.mapping = _mapping
        self.callback_counter = 0

    def get_property(self, item):
        if item != "id":
            raise TypeError("I think you wrote this test wrong.")
        return self.id


@pytest.fixture()
def find_any():
    """Find a mocked WebElement that exposes the details of the find_any call and a callback counter."""

    def func(driver, by, target, multiple, wait, mapping):
        if multiple:
            return [MockElement(driver, by, target, multiple, mapping)]
        return MockElement(driver, by, target, multiple, mapping)

    return func


@pytest.fixture()
def chromedriver():
    class Mock(ChromeManager):
        # noinspection PyUnusedLocal,PyMissingConstructor
        def __init__(self, timeout=0, debug=False):
            self._current_url = URL
            self.session_id = "test_driver"
            self.callback_counter = 0
            self.script_counter = 0
            self.last_execute_command = None
            self._authenticated = None
            self._is_remote = False

        # noinspection PyPep8Naming
        class wait:
            @staticmethod
            def until(method):
                return method

        # noinspection PyUnusedLocal
        def _execute(self, command, params):
            self.script_counter += 1
            self.last_execute_command = command
            return

        execute = _execute

        def execute_script(self, *a, **kw):
            self.script_counter += 1
            return

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

        def find_element(self, by=None, value=None):
            return MockElement(self, by, value, False, None)

        def find_elements(self, by=None, value=None):
            return [MockElement(self, by, value, True, None)]

    return Mock
