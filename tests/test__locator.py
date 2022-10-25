# noinspection PyProtectedMember
from admitted._locator import Locator


class LocatorForTest(Locator):
    def __init__(self, driver):
        self._parent = driver

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
    element = locator.css(selector=target, wait=True, multiple=multiple, mapping=mapping)

    # Consequence
    assert element.target == "target_one"


def test_find_any_multiple(chromedriver):
    # Antecedent
    locator = LocatorForTest(chromedriver())
    target = "target_many"
    multiple = True
    mapping = None

    # Behavior
    element, *_ = locator.xpath(path=target, wait=True, multiple=multiple, mapping=mapping)

    # Consequence
    assert element.target == target
