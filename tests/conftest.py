import pytest
from selenium.common.exceptions import WebDriverException
from admitted._manager import ChromeManager  # noqa protected member

URL = "https://www.example.com"


class NoTime:
    current_time = 750000.0

    @classmethod
    def monotonic(cls) -> float:
        return cls.current_time

    @classmethod
    def sleep(cls, value: float) -> None:
        NoTime.current_time += value
        return


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr("time.sleep", NoTime.sleep)
    monkeypatch.setattr("time.monotonic", NoTime.monotonic)


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    """Remove request method for all tests so we don't make network requests from tests."""
    monkeypatch.delattr("urllib3.request")


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
    def __init__(self, _driver, _by, _target):
        self.id = "id_one"
        self.driver = _driver
        self.by = _by
        self.target = _target
        self.callback_counter = 0
        self.click_counter = 0
        self.text = ""

    def get_property(self, item):
        if item != "id":
            raise TypeError("I think you wrote this test wrong.")
        return self.id

    def get_attribute(self, item):
        if item == "checked":
            # we're checked on every third click!
            value = "true" if self.click_counter % 3 == 2 else "false"
            return value
        return item

    def scroll_to(self):
        return

    def click(self):
        self.click_counter += 1

    def clear(self):
        self.text = ""

    def send_keys(self, value):
        self.text += value


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
            self._elements = {}

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

        def find_elements(self, by=None, value=None):
            if value == "fail":
                return []
            if hasattr(self, "_elements"):
                # sometimes this is a monkeypatch over selenium.webdriver.remote.webelement.WebElement.find_elements
                # in which case `self` will not have the `_elements` attribute.
                locator = (by, value)
                if locator not in self._elements:
                    self._elements[locator] = MockElement(self, by, value)
                return [self._elements[locator]]
            return [MockElement(self, by, value)]

    return Mock
