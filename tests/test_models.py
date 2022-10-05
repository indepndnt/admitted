import pytest
from admitted import models


def test_request_connect(urls):
    # CONNECT method raises TypeError
    with pytest.raises(TypeError):
        _ = models.Request("connect", urls.origin)


def test_request_bad_params(urls):
    # no-content method with invalid `payload` type raises TypeError
    with pytest.raises(TypeError):
        _ = models.Request("head", urls.origin, payload=b"invalid")


def test_request_bad_method(urls):
    # invalid method raises TypeError
    with pytest.raises(TypeError):
        _ = models.Request("output", urls.origin)


def test_request_pydantic_model(urls):
    # Antecedent: pydantic model payload
    class MockPayload:
        # noinspection PyMethodMayBeStatic
        def json(self, value):
            return value

    payload_value = b"test_body"
    payload = MockPayload()

    # Behavior: instantiate Request and specify json_args
    req = models.Request("put", urls.origin, payload, json_args={"value": payload_value})

    # Consequence: request body is the result of the call to the json method with specified arguments
    assert req.body == payload_value
    assert isinstance(repr(req), str)


def test_request_bytes_payload(urls):
    # Antecedent: bytes payload
    payload = b"test_body"

    # Behavior: instantiate Request
    req = models.Request("patch", urls.origin, payload=payload)

    # Consequence: request body is as specified
    assert req.body == payload


def test_request_combine_queries(urls):
    # Antecedent: request params
    url = f"{urls.test}?a=1&b=2"
    params = {"a": 3, "c": 4}

    # Behavior: instantiate Request
    req = models.Request("delete", url, payload=params)

    # Consequence: request url includes query params from both url and payload
    assert req.url == f"{urls.test}?a=3&c=4&a=1&b=2"


def test_response_fetch_error():
    # Antecedent: a window.fetch response with error content
    msg = "Fetch exception for test purposes."
    fetch_value = {"error": {"name": "TestError", "message": msg}}

    # Behavior: instantiate Response
    resp = models.Response.from_fetch(fetch_value)

    # Consequence: error message in reason attribute and fetch response contains original
    assert msg in resp.reason
    assert resp._fetch_raw_response == fetch_value


def test_response_json_error():
    # Antecedent: response data expected to be json
    response_body = b"{this is not valid json}"

    # Behavior: instantiate Response
    # noinspection PyTypeChecker
    resp = models.Response(url="", status=200, reason="OK", headers=None)
    resp._content = response_body
    data = resp.json

    # Consequence: JSONDecodeError is caught and returns None
    assert data is None
