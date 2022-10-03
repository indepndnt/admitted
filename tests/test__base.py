import pytest
from webfetch import _locator
from webfetch._base import BasePage
from webfetch.exceptions import NavigationError


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
    # Antecedent: BasePage is instantiated
    instance = BasePage(chromedriver)
    monkeypatch.setattr(_locator, "find_any", instance.browser.find_any)
    selector = '.test, [method="css"]'

    # Behavior: finder method is called
    element = instance.css(selector, False, None)

    # Consequence: returns the result of find_any, in this case our monkeypatch
    assert element.by == "css selector"
    assert element.target == selector


def test_xpath_finder(monkeypatch, chromedriver):
    # Antecedent: BasePage is instantiated
    instance = BasePage(chromedriver)
    monkeypatch.setattr(_locator, "find_any", instance.browser.find_any)
    xpath = "//[contains(@class,'test') and @method='xpath']"

    # Behavior: finder method is called
    element = instance.xpath(xpath, True, None)

    # Consequence: returns the result of find_any, in this case our monkeypatch
    assert element.by == "xpath"
    assert element.target == xpath


def test_switch_finder(monkeypatch, chromedriver):
    # Antecedent: BasePage is instantiated
    instance = BasePage(chromedriver)
    monkeypatch.setattr(_locator, "find_any", instance.browser.find_any)

    def callback(el):
        instance.browser.callback_was_called += 1
        return el

    # Behavior: finder method is called
    element = instance.switch_id({"id_one": callback, "id_two": callback})

    # Consequence: method locator is as expected and called one of the callbacks
    assert instance.browser.callback_was_called == 1
    assert element.by == "css selector"
    assert element.target == '[id="id_one"], [id="id_two"]'


def test_current_url(chromedriver):
    # Antecedent: BasePage is instantiated
    instance = BasePage(chromedriver)

    # Behavior: read current_url property
    url = instance.current_url

    # Consequence: returns result of call to property method instance.browser.current_url
    assert url == "https://www.example.com"


def test_navigate_chrome_success(chromedriver):
    # Antecedent: BasePage is instantiated
    instance = BasePage(chromedriver)

    def callback(retry: int):
        instance.browser.callback_was_called += 1
        return True

    # Behavior: call _navigate method
    instance._navigate("https://www.example.com/test", callback, retry_wait=0, retries_override=0, enforce_url=True)

    # Consequence: succeeded without reaching the pre-pause callback
    assert instance.browser.callback_was_called == 0


def test_navigate_chrome_fail(chromedriver):
    # Antecedent: BasePage is instantiated
    instance = BasePage(chromedriver)

    def callback(retry: int):
        instance.browser.callback_was_called += 1
        return False

    # Behavior: call _navigate method
    with pytest.raises(NavigationError, match=r"^Failed after \d tries navigating to .*"):
        instance._navigate(
            "https://www.example.com/fail", callback, retry_wait=0, retries_override=2, enforce_url=False
        )

    # Consequence: exception was raised after pre-pause callback was called after each attempt
    assert instance.browser.callback_was_called == 3


def test_navigate_chrome_mismatch(chromedriver):
    # Antecedent: BasePage is instantiated
    instance = BasePage(chromedriver)

    # Behavior: call _navigate method
    with pytest.raises(NavigationError, match=r"^Failed after \d tries navigating to .*"):
        instance._navigate("https://www.example.com/change", None, retry_wait=0, retries_override=0, enforce_url=True)

    # Consequence: exception was raised as expected
