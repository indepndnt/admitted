from webfetch import element, _locator


def test_css_finder(monkeypatch, chromedriver):
    # Antecedent
    instance = element.Element(chromedriver, "test_css")
    monkeypatch.setattr(_locator, "find_any", instance.parent.find_any)
    selector = '.test, [method="css"]'

    # Behavior
    el = instance.css(selector, False, None)

    # Consequence: returns the result of find_any, in this case our monkeypatch
    assert el.by == "css selector"
    assert el.target == selector


def test_xpath_finder(monkeypatch, chromedriver):
    # Antecedent
    instance = element.Element(chromedriver, "test_xpath")
    monkeypatch.setattr(_locator, "find_any", instance.parent.find_any)
    xpath = "//[contains(@class,'test') and @method='xpath']"

    # Behavior
    el = instance.xpath(xpath, True, None)

    # Consequence: returns the result of find_any, in this case our monkeypatch
    assert el.by == "xpath"
    assert el.target == xpath
