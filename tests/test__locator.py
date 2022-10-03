from webfetch._locator import find_any, match_url
from webfetch._manager import ChromeManager


class MockWait:
    def until(self, func):
        return


def get_test_driver(monkeypatch):
    monkeypatch.setattr(ChromeManager, "__init__", lambda _: None)
    monkeypatch.setattr(ChromeManager, "find_element", lambda *args: (1, *args))
    monkeypatch.setattr(ChromeManager, "find_elements", lambda *args: (2, *args))
    instance = ChromeManager()
    instance.wait = MockWait()
    return instance


def test_find_any_single(monkeypatch):
    # Antecedent
    driver = get_test_driver(monkeypatch)
    by = "find"
    target = "target_${index}"
    multiple = False
    mapping = {"index": "one"}

    # Behavior
    n, _, find_by, find_target = find_any(driver, by, target, multiple, mapping)

    # Consequence
    assert n == 1
    assert find_by == by
    assert find_target == "target_one"


def test_find_any_multiple(monkeypatch):
    # Antecedent
    driver = get_test_driver(monkeypatch)
    by = "find"
    target = "target_many"
    multiple = True
    mapping = None

    # Behavior
    n, _, find_by, find_target = find_any(driver, by, target, multiple, mapping)

    # Consequence
    assert n == 2
    assert find_by == by
    assert find_target == target


def test_match_url_success():
    # Antecedent
    one_url = "http://example.com/home"
    two_url = "https://www.sub.example.com/home"

    # Behavior
    result = match_url(one_url, two_url)

    # Consequence
    assert result is True


def test_match_url_ignoring_query():
    # Antecedent
    one_url = "http://example.com/home?ignored=false"
    two_url = "https://www.sub.example.com/home"

    # Behavior
    result = match_url(one_url, two_url, ignore_query=True)

    # Consequence
    assert result is True


def test_match_url_fail():
    # Antecedent
    one_url = "http://example.com/home"
    two_url = "http://example.com/home/dash"
    three_url = "http://example.net/home"

    # Behavior
    result1 = match_url(one_url, two_url)
    result2 = match_url(one_url, three_url)

    # Consequence
    assert result1 is False
    assert result2 is False
