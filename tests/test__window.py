from webfetch import _window

URL = "https://www.example.com"


def get_instance_with_mock_run(return_value):
    class Driver:
        def execute_script(self, script, *args, **kwargs):
            if isinstance(return_value, dict):
                return dict(script=script, args=args, kwargs=kwargs, **return_value)
            return return_value

    instance = _window.Window(Driver())
    return instance


def test_get_item():
    # Antecedent
    instance = get_instance_with_mock_run("test_result")

    # Behavior
    value = instance["value"]

    # Consequence
    assert value == "test_result"


def test_new_keys():
    # Antecedent
    instance = get_instance_with_mock_run(["onkeypress", "test_result"])

    # Behavior
    value = instance.new_keys()

    # Consequence
    assert value == ["test_result"]


def test_scroll_to_top():
    # Antecedent
    instance = get_instance_with_mock_run(None)

    # Behavior
    instance.scroll_to_top()

    # Consequence: did not raise exception
    assert True


def test_fetch_get_dict():
    # Antecedent
    fetch_value = {
        "url": URL,
        "status": 200,
        "reason": "OK",
        "headers": [],
        "body": b'{"data": ""}',
        "text": '{"data": ""}',
        "json": {"data": ""},
    }
    instance = get_instance_with_mock_run(fetch_value)

    # Behavior
    response = instance.fetch("get", URL, {"q": "test"}, None)

    # Consequence
    assert response.json == {"data": ""}
    assert response.reason == "OK"
    assert f"{URL}?q=test" in response._fetch_raw_response["script"]


def test_fetch_get_list():
    # Antecedent
    fetch_value = {
        "url": URL,
        "status": 200,
        "reason": "OK",
        "headers": [],
        "body": b'["data", ""]',
        "text": '["data": ""]',
        "json": ["data", ""],
    }
    instance = get_instance_with_mock_run(fetch_value)

    # Behavior
    response = instance.fetch("get", URL, [("q", "test")], None)

    # Consequence
    assert response.json == ["data", ""]
    assert response.reason == "OK"
    assert f"{URL}?q=test" in response._fetch_raw_response["script"]


def test_fetch_get_html():
    # Antecedent
    html = """<!DOCTYPE html>
<html><head></head><body>
<h1>Test Page</h1><p>Success!</p>
</body></html>"""
    fetch_value = {
        "url": URL,
        "status": 200,
        "reason": "OK",
        "headers": [],
        "body": html.encode(),
        "text": html,
        "json": None,
    }
    instance = get_instance_with_mock_run(fetch_value)

    # Behavior
    response = instance.fetch("get", "https://www.example.com", None, None)

    # Consequence
    assert response.html.xpath("/html/body/h1")[0].text == "Test Page"
    assert response.html.xpath("/html/body/p")[0].text == "Success!"


def test_fetch_post():
    # Antecedent
    fetch_value = {
        "url": URL,
        "status": 200,
        "reason": "OK",
        "headers": [],
        "body": b"",
        "text": "",
        "json": None,
    }
    instance = get_instance_with_mock_run(fetch_value)

    # Behavior
    response = instance.fetch("post", "url", {"key": "value"}, {"x-header": "test-value"})

    # Consequence
    assert '"Content-Type": "application/json"' in response._fetch_raw_response["script"]
    assert '"x-header": "test-value"' in response._fetch_raw_response["script"]
