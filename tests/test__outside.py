import io
import urllib3
from webfetch import _outside


def mock_request(method, url, _, headers=None, **kwargs):
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


def test_json_response():
    # Antecedent
    urllib3.PoolManager.request = mock_request
    test_response = b'{"data": "test data"}'

    # Behavior
    response = _outside.outside_request("GET", "https://www.example.com", test=test_response)

    # Consequence
    assert response.json.get("data") == "test data"


def test_text_response():
    # Antecedent
    urllib3.PoolManager.request = mock_request
    test_response = b"test data"

    # Behavior
    response = _outside.outside_request("GET", "https://www.example.com", test=test_response)

    # Consequence
    assert response.text == "test data"


def test_raw_response():
    # Antecedent
    urllib3.PoolManager.request = mock_request
    test_response = b"test data"

    # Behavior
    response = _outside.outside_request("GET", "https://www.example.com", test=test_response)

    # Consequence
    assert response.content == b"test data"


def test_stream_response():
    # Antecedent
    urllib3.PoolManager.request = mock_request
    test_response = io.BytesIO(b"test data")
    test_response.seek(0)

    # Behavior
    response = _outside.outside_request("GET", "https://www.example.com", stream=True, test=test_response)
    fp = response.write_stream(io.BytesIO())
    data = fp.getvalue()
    fp.close()

    # Consequence
    assert data == b"test data"
