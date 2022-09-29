import pytest
from selenium.common.exceptions import WebDriverException
from webfetch import _locator
from webfetch._base import BasePage
from webfetch.exceptions import NavigationError
from webfetch._manager import ChromeManager


class Mock(ChromeManager):
    def __init__(self):
        self._current_url = "https://www.example.com"
        self.callback_was_called = False

    def execute_script(self, **kwargs):
        return kwargs

    @property
    def current_url(self):
        return self._current_url

    def get(self, url):
        if url == "https://www.example.com/fail":
            raise WebDriverException

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


def test_instantiate_base(chromedriver):
    # Antecedent: BasePage is imported and arguments established
    retries = 5
    debug = False

    # Behavior: BasePage is instantiated
    instance = BasePage(chromedriver, retries, debug)

    # Consequence: instance has public attributes and methods
    public_attrs = ("browser", "window", "outside_request", "css", "xpath", "switch_id")
    assert all((hasattr(instance, attr) for attr in public_attrs))


def test_css_finder(monkeypatch, chromedriver):
    # Antecedent
    instance = BasePage(chromedriver)
    monkeypatch.setattr(_locator, "find_any", instance.browser.find_any)
    selector = '.test, [method="css"]'

    # Behavior
    element = instance.css(selector, False, None)

    # Consequence: returns the result of find_any, in this case our monkeypatch
    assert element.by == "css selector"
    assert element.target == selector


def test_xpath_finder(monkeypatch, chromedriver):
    # Antecedent
    instance = BasePage(chromedriver)
    monkeypatch.setattr(_locator, "find_any", instance.browser.find_any)
    xpath = "//[contains(@class,'test') and @method='xpath']"

    # Behavior
    element = instance.xpath(xpath, True, None)

    # Consequence: returns the result of find_any, in this case our monkeypatch
    assert element.by == "xpath"
    assert element.target == xpath


def test_switch_finder(monkeypatch, chromedriver):
    # Antecedent
    instance = BasePage(chromedriver)
    monkeypatch.setattr(_locator, "find_any", instance.browser.find_any)

    def callback(el):
        instance.browser.callback_was_called = True
        return el

    # Behavior
    element = instance.switch_id({"id_one": callback, "id_two": callback})

    # Consequence
    assert instance.browser.callback_was_called is True
    assert element.by == "css selector"
    assert element.target == '[id="id_one"], [id="id_two"]'


def test_current_url(chromedriver):
    # Antecedent
    instance = BasePage(chromedriver)

    # Behavior
    url = instance.current_url

    # Consequence: returns result of call to property method instance.browser.current_url
    assert url == "https://www.example.com"


def test_navigate_chrome_success(chromedriver):
    # Antecedent
    instance = BasePage(chromedriver)

    def callback():
        instance.browser.callback_was_called = True
        return True

    # Behavior
    instance._navigate("https://www.example.com/test", callback, 0, 0, False)

    # Consequence
    assert instance.browser.callback_was_called is True


def test_navigate_chrome_fail(chromedriver):
    # Antecedent
    instance = BasePage(chromedriver)

    # Behavior, Consequence
    with pytest.raises(NavigationError, match=r"^Failed after \d tries navigating to .*"):
        instance._navigate("https://www.example.com/fail", None, 0, 1, False)


def test_navigate_chrome_mismatch(chromedriver):
    # Antecedent
    instance = BasePage(chromedriver)

    # Behavior, Consequence
    with pytest.raises(NavigationError, match=r"^Failed after \d tries navigating to .*"):
        instance._navigate("https://www.example.com/unreachable", None, 0, 0, True)
