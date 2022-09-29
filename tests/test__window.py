from webfetch import _window


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
    instance = get_instance_with_mock_run({"data": ""})

    # Behavior
    value = instance.fetch("get", "https://www.example.com", {"q": "test"}, None)

    # Consequence
    assert value["data"] == ""
    assert value["args"][0] == "GET"
    assert value["args"][1] == "https://www.example.com?q=test"


def test_fetch_get_list():
    # Antecedent
    instance = get_instance_with_mock_run({"data": ""})

    # Behavior
    value = instance.fetch("get", "https://www.example.com", [("q", "test")], None)

    # Consequence
    assert value["data"] == ""
    assert value["args"][0] == "GET"
    assert value["args"][1] == "https://www.example.com?q=test"


def test_fetch_get_html():
    # Antecedent
    html = """<!DOCTYPE html>
<html><head></head><body>
<h1>Test Page</h1><p>Success!</p>
</body></html>"""
    instance = get_instance_with_mock_run({"data": html})

    # Behavior
    value = instance.fetch("get", "https://www.example.com", None, None)

    # Consequence
    assert value["html"].xpath("/html/body/h1")[0].text == "Test Page"
    assert value["html"].xpath("/html/body/p")[0].text == "Success!"


def test_fetch_post():
    # Antecedent
    instance = get_instance_with_mock_run({"status": 0, "url": "", "data": "", "html": None})

    # Behavior
    value = instance.fetch("post", "url", {"key": "value"}, {"x-header": "test-value"})

    # Consequence
    assert value["args"][2]["headers"]["Content-Type"] == "application/json"
    assert value["args"][2]["headers"]["x-header"] == "test-value"
