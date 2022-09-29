import io
import urllib3
from webfetch import _outside


class MockResponse:
    def __init__(self, data: bytes):
        self.data = data

    def stream(self, chunk_size):
        return [self.data[:chunk_size]]


def mock_request(method, url, fields=None, headers=None, **kwargs):
    return kwargs["test"]


def test_json_response():
    # Antecedent
    urllib3.PoolManager.request = mock_request
    test_response = MockResponse(b'{"data": "test data"}')

    # Behavior
    response = _outside.outside_request("GET", "https://www.example.com", "json", test=test_response)

    # Consequence
    assert response["data"] == "test data"


def test_text_response():
    # Antecedent
    urllib3.PoolManager.request = mock_request
    test_response = MockResponse(b"test data")

    # Behavior
    response = _outside.outside_request("GET", "https://www.example.com", "text", test=test_response)

    # Consequence
    assert response == "test data"


def test_raw_response():
    # Antecedent
    urllib3.PoolManager.request = mock_request
    test_response = MockResponse(b"test data")

    # Behavior
    response = _outside.outside_request("GET", "https://www.example.com", "raw", test=test_response)

    # Consequence
    assert response == b"test data"


def test_stream_response():
    # Antecedent
    urllib3.PoolManager.request = mock_request
    test_response = MockResponse(b"test data")

    # Behavior
    fp = _outside.outside_request("GET", "https://www.example.com", io.BytesIO(), test=test_response)
    fp.seek(0)
    data = fp.read(999)
    fp.close()

    # Consequence
    assert data == b"test data"
