# noinspection PyProtectedMember
from admitted._locator import find_any, match_url


def test_find_any_single(chromedriver):
    # Antecedent
    driver = chromedriver()
    by = "find"
    target = "target_${index}"
    multiple = False
    mapping = {"index": "one"}

    # Behavior
    element = find_any(driver=driver, by=by, target=target, multiple=multiple, mapping=mapping)

    # Consequence
    assert element.multiple is multiple
    assert element.by == by
    assert element.target == "target_one"


def test_find_any_multiple(chromedriver):
    # Antecedent
    driver = chromedriver()
    by = "find"
    target = "target_many"
    multiple = True
    mapping = None

    # Behavior
    element, *_ = find_any(driver=driver, by=by, target=target, multiple=multiple, mapping=mapping)

    # Consequence
    assert element.multiple is multiple
    assert element.by == by
    assert element.target == target


def test_match_url_success(urls):
    # Antecedent
    one_url = f"{urls.naked}/home"
    two_url = f"{urls.sub}/home"

    # Behavior
    result = match_url(one_url, two_url)

    # Consequence
    assert result is True


def test_match_url_ignoring_query(urls):
    # Antecedent
    one_url = f"{urls.naked}/home?ignored=false"
    two_url = f"{urls.sub}/home"

    # Behavior
    result = match_url(one_url, two_url, ignore_query=True)

    # Consequence
    assert result is True


def test_match_url_fail(urls):
    # Antecedent
    one_url = f"{urls.naked}/home"
    two_url = f"{urls.naked}/home/dash"
    three_url = f"{urls.naked.replace('com', 'net')}/home"

    # Behavior
    result1 = match_url(one_url, two_url)
    result2 = match_url(one_url, three_url)

    # Consequence
    assert result1 is False
    assert result2 is False
