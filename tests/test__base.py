import pytest
from admitted._base import BasePage
from admitted.exceptions import NavigationError


def test_instantiate_base(chromedriver):
    # Antecedent: BasePage is imported and arguments established
    retries = 5
    debug = False

    # Behavior: BasePage is instantiated
    instance = BasePage(chromedriver(), retries=retries, debug=debug)

    # Consequence: instance has public attributes and methods
    public_attrs = ("browser", "window", "direct_request", "css", "xpath", "switch_id", "current_url")
    assert all((hasattr(instance, attr) for attr in public_attrs))


def test_css_finder(chromedriver):
    # Antecedent: BasePage is instantiated
    instance = BasePage(chromedriver())
    selector = '.test, [method="css"]'

    # Behavior: finder method is called
    element = instance.css(selector, True, False, None)

    # Consequence: returns the result of BasePage.css, in this case our MockElement exposing the selector
    # noinspection PyUnresolvedReferences
    assert element.by == "css selector"
    # noinspection PyUnresolvedReferences
    assert element.target == selector


def test_xpath_finder(chromedriver):
    # Antecedent: BasePage is instantiated
    instance = BasePage(chromedriver())
    xpath = "//[contains(@class,'test') and @method='xpath']"

    # Behavior: finder method is called
    element, *_ = instance.xpath(xpath, True, True, None)

    # Consequence: returns the result of BasePage.xpath, in this case our MockElement exposing the selector
    assert element.by == "xpath"
    assert element.target == xpath


def test_current_url(chromedriver, urls):
    # Antecedent: BasePage is instantiated
    instance = BasePage(chromedriver())

    # Behavior: read current_url property
    url = instance.current_url

    # Consequence: returns result of call to property method instance.browser.current_url
    assert url == urls.origin


def test_navigate_chrome_success(chromedriver, urls):
    # Antecedent: BasePage is instantiated
    instance = BasePage(chromedriver())

    # noinspection PyUnusedLocal
    def callback(retry: int):
        # noinspection PyUnresolvedReferences
        instance.browser.callback_counter += 1
        return True

    # Behavior: call _navigate method
    instance._navigate(urls.test, callback=callback, retry_wait=0, retries_override=0, enforce_url=True)

    # Consequence: succeeded without reaching the pre-pause callback
    # noinspection PyUnresolvedReferences
    assert instance.browser.callback_counter == 0


def test_navigate_chrome_mismatch_success(chromedriver, urls):
    # Antecedent: BasePage is instantiated
    instance = BasePage(chromedriver())

    # Behavior: call _navigate method
    instance._navigate(urls.change, retry_wait=0, retries_override=0, enforce_url=False)

    # Consequence: url mismatch but succeeded because enforce_url is False


def test_navigate_chrome_callback_success(chromedriver, urls):
    # Antecedent: BasePage is instantiated
    instance = BasePage(chromedriver())

    # noinspection PyUnusedLocal
    def callback(retry: int):
        # noinspection PyUnresolvedReferences
        instance.browser.callback_counter += 1
        return True

    # Behavior: call _navigate method
    instance._navigate(urls.change, callback=callback, retry_wait=0, retries_override=1, enforce_url=True)

    # Consequence: failed due to url mismatch then received success from the pre-pause callback
    # noinspection PyUnresolvedReferences
    assert instance.browser.callback_counter == 1


def test_navigate_chrome_fail(chromedriver, urls):
    # Antecedent: BasePage is instantiated
    instance = BasePage(chromedriver())

    # noinspection PyUnusedLocal
    def callback(retry: int):
        # noinspection PyUnresolvedReferences
        instance.browser.callback_counter += 1
        return False

    # Behavior: call _navigate method
    with pytest.raises(NavigationError, match=r"^Failed after \d tries navigating to .*"):
        instance._navigate(urls.fail, callback=callback, retry_wait=0, retries_override=2, enforce_url=False)

    # Consequence: exception was raised after pre-pause callback was called after each attempt
    # noinspection PyUnresolvedReferences
    assert instance.browser.callback_counter == 3


def test_navigate_chrome_mismatch(chromedriver, urls):
    # Antecedent: BasePage is instantiated
    instance = BasePage(chromedriver())

    # Behavior: call _navigate method
    with pytest.raises(NavigationError, match=r"^Failed after \d tries navigating to .*"):
        instance._navigate(urls.change, retry_wait=0, retries_override=0, enforce_url=True)

    # Consequence: exception was raised as expected
