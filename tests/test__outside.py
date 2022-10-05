import io
import urllib3

# noinspection PyProtectedMember
from admitted import _outside


# noinspection PyUnusedLocal
def mock_request(method, url, fields=None, headers=None, **kwargs):
    response = urllib3.HTTPResponse(
        body=kwargs["test"],
        headers=headers,
        status=200,
        reason="OK",
        request_method=method,
        request_url=url,
        preload_content=kwargs.get("preload_content", True),
    )
    return response


def test_json_response(urls):
    # Antecedent
    urllib3.PoolManager.request = mock_request
    test_response = b'{"data": "test data"}'

    # Behavior
    response = _outside.outside_request("GET", urls.origin, test=test_response)

    # Consequence
    assert response.json.get("data") == "test data"


def test_text_response(urls):
    # Antecedent
    urllib3.PoolManager.request = mock_request
    test_response = b"test data"

    # Behavior
    response = _outside.outside_request("GET", urls.origin, test=test_response)

    # Consequence
    assert response.text == "test data"


def test_raw_response(urls):
    # Antecedent
    urllib3.PoolManager.request = mock_request
    test_response = b"test data"

    # Behavior
    response = _outside.outside_request("GET", urls.origin, test=test_response)

    # Consequence
    assert response.content == b"test data"


def test_stream_response(urls):
    # Antecedent
    urllib3.PoolManager.request = mock_request
    test_response = io.BytesIO(b"test data")
    test_response.seek(0)

    # Behavior
    response = _outside.outside_request("GET", urls.origin, stream=True, test=test_response)
    fp = response.write_stream(io.BytesIO())
    # noinspection PyUnresolvedReferences
    data = fp.getvalue()
    fp.close()

    # Consequence
    assert data == b"test data"
