import pytest
from selenium.common.exceptions import TimeoutException
from admitted._locator import Locator  # noqa protected member


class LocatorForTest(Locator):
    def __init__(self, driver):  # noqa no super()
        self._parent = driver
        self.find_elements = self._parent.find_elements

    @property
    def parent(self):
        return self._parent


def test_find_any_single(chromedriver):
    # Antecedent
    locator = LocatorForTest(chromedriver())
    target = "target_${index}"
    multiple = False
    mapping = {"index": "one"}

    # Behavior
    element = locator.css(selector=target, multiple=multiple, mapping=mapping)

    # Consequence
    assert element.target == "target_one"  # noqa attribute


def test_find_any_multiple(chromedriver):
    # Antecedent
    locator = LocatorForTest(chromedriver())
    target = "target_many"
    multiple = True
    mapping = None

    # Behavior
    element, *_ = locator.xpath(path=target, wait=0, multiple=multiple, mapping=mapping)

    # Consequence
    assert element.target == target


def test_find_any_failure(chromedriver):
    # Antecedent
    locator = LocatorForTest(chromedriver())
    target = "fail"
    multiple = True
    mapping = None

    # Behavior, Consequence
    with pytest.raises(TimeoutException):
        element, *_ = locator.xpath(path=target, wait=0.0001, multiple=multiple, mapping=mapping)


def test_checkboxes(chromedriver):
    # Antecedent
    locator = LocatorForTest(chromedriver())

    # Behavior
    locator.css_checkbox("#test_checkbox", "#test_checkbox", True)
    locator.xpath_checkbox("//input[@id='test_checkbox']", "//input[@id='test_checkbox']", True)

    # Consequence - ran without exception


def test_inputs(chromedriver):
    # Antecedent
    locator = LocatorForTest(chromedriver())
    css_input, css_value = "#test_input", "This is my CSS input!"
    xpath_input, xpath_value = "//input[@id='test_input']", "This is my XPATH input!"

    # Behavior
    locator.css_input(css_input, None, css_value)
    locator.xpath_input(xpath_input, None, xpath_value)

    # Consequence
    assert locator.css(css_input).text == css_value
    assert locator.xpath(xpath_input).text == xpath_value
