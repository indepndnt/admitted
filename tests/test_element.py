# noinspection PyProtectedMember
from admitted import element, _locator


def test_css_finder(monkeypatch, chromedriver, find_any):
    # Antecedent: Element is instantiated
    instance = element.Element(chromedriver, "test_css")
    monkeypatch.setattr(_locator, "find_any", find_any)
    selector = '.test, [method="css"]'

    # Behavior
    el = instance.css(selector, False, None)

    # Consequence: returns the result of find_any, in this case our monkeypatch
    # noinspection PyUnresolvedReferences
    assert el.by == "css selector"
    # noinspection PyUnresolvedReferences
    assert el.target == selector


def test_xpath_finder(monkeypatch, chromedriver, find_any):
    # Antecedent: Element is instantiated
    instance = element.Element(chromedriver, "test_xpath")
    monkeypatch.setattr(_locator, "find_any", find_any)
    xpath = "//[contains(@class,'test') and @method='xpath']"

    # Behavior
    el, *_ = instance.xpath(xpath, True, None)

    # Consequence: returns the result of find_any, in this case our monkeypatch
    assert el.by == "xpath"
    assert el.target == xpath
