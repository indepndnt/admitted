import io
import urllib3

# noinspection PyProtectedMember
from admitted import _url


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


def test_match_url_success(urls):
    # Antecedent
    one_url = f"{urls.naked}/home"
    two_url = f"{urls.sub}/home"

    # Behavior
    result = _url.match_url(one_url, two_url)

    # Consequence
    assert result is True


def test_match_url_ignoring_query(urls):
    # Antecedent
    one_url = f"{urls.naked}/home?ignored=false"
    two_url = f"{urls.sub}/home"

    # Behavior
    result = _url.match_url(one_url, two_url, ignore_query=True)

    # Consequence
    assert result is True


def test_match_url_fail(urls):
    # Antecedent
    one_url = f"{urls.naked}/home"
    two_url = f"{urls.naked}/home/dash"
    three_url = f"{urls.naked.replace('com', 'net')}/home"

    # Behavior
    result1 = _url.match_url(one_url, two_url)
    result2 = _url.match_url(one_url, three_url)

    # Consequence
    assert result1 is False
    assert result2 is False


def test_json_response(urls):
    # Antecedent
    urllib3.PoolManager.request = mock_request
    test_response = b'{"data": "test data"}'

    # Behavior
    response = _url.direct_request("GET", urls.origin, test=test_response)

    # Consequence
    assert response.json.get("data") == "test data"


def test_text_response(urls):
    # Antecedent
    urllib3.PoolManager.request = mock_request
    test_response = b"test data"

    # Behavior
    response = _url.direct_request("GET", urls.origin, test=test_response)

    # Consequence
    assert response.text == "test data"


def test_raw_response(urls):
    # Antecedent
    urllib3.PoolManager.request = mock_request
    test_response = b"test data"

    # Behavior
    response = _url.direct_request("GET", urls.origin, test=test_response)

    # Consequence
    assert response.content == b"test data"


def test_stream_response(urls):
    # Antecedent
    urllib3.PoolManager.request = mock_request
    test_response = io.BytesIO(b"test data")
    test_response.seek(0)

    # Behavior
    response = _url.direct_request("GET", urls.origin, stream=True, test=test_response)
    fp = response.write_stream(io.BytesIO())
    # noinspection PyUnresolvedReferences
    data = fp.getvalue()
    fp.close()

    # Consequence
    assert data == b"test data"
