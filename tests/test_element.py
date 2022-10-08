# noinspection PyProtectedMember
from admitted import element, _locator


def test_css_finder(monkeypatch, chromedriver, find_any):
    # Antecedent: Element is instantiated
    instance = element.Element(chromedriver(), "test_css")
    monkeypatch.setattr(_locator, "find_any", find_any)
    selector = '.test, [method="css"]'

    # Behavior
    el = instance.css(selector, True, False, None)

    # Consequence: returns the result of find_any, in this case our monkeypatch
    # noinspection PyUnresolvedReferences
    assert el.by == "css selector"
    # noinspection PyUnresolvedReferences
    assert el.target == selector


def test_xpath_finder(monkeypatch, chromedriver, find_any):
    # Antecedent: Element is instantiated
    instance = element.Element(chromedriver(), "test_xpath")
    monkeypatch.setattr(_locator, "find_any", find_any)
    xpath = "//[contains(@class,'test') and @method='xpath']"

    # Behavior
    el, *_ = instance.xpath(xpath, True, True, None)

    # Consequence: returns the result of find_any, in this case our monkeypatch
    assert el.by == "xpath"
    assert el.target == xpath


def test_scroll_to(monkeypatch, chromedriver):
    # Antecedent: Element is instantiated
    instance = element.Element(chromedriver(), "test_scroll_to")

    # Behavior
    instance.scroll_to()

    # Consequence: execute_script was called
    assert instance.parent.script_counter == 1


def test_click(monkeypatch, chromedriver):
    # Antecedent: Element is instantiated
    driver = chromedriver()
    instance = element.Element(driver, "test_click")

    # Behavior
    result = instance.click()

    # Consequence: superclass method was called and instance returned
    assert driver.script_counter == 1
    assert driver.last_execute_command == "clickElement"
    assert result is instance


def test_clear(monkeypatch, chromedriver):
    # Antecedent: Element is instantiated
    driver = chromedriver()
    instance = element.Element(driver, "test_clear")

    # Behavior
    result = instance.clear()

    # Consequence: superclass method was called and instance returned
    assert driver.script_counter == 1
    assert driver.last_execute_command == "clearElement"
    assert result is instance


def test_send_keys(monkeypatch, chromedriver):
    # Antecedent: Element is instantiated
    driver = chromedriver()
    instance = element.Element(driver, "test_send_keys")

    # Behavior
    result = instance.send_keys("ok")

    # Consequence: superclass method was called and instance returned
    assert driver.script_counter == 1
    assert driver.last_execute_command == "sendKeysToElement"
    assert result is instance
