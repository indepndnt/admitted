from __future__ import annotations
from urllib.parse import urlparse
import certifi
import urllib3
from .models import Request, Response


def match_url(url1: str, url2: str, *, ignore_query: bool = False, path_substr: bool = False) -> bool:
    """Report whether the domain, path, and query of both URLs match.

    Examples:
      These evaluate to True:
        match_url("https://www.example.com/home?q=1", "https://example.com/home?q=1")
        match_url("https://www.example.com/home", "https://example.com/home?q=1", ignore_query=True)
        match_url("https://example.com/app/home/page", "https://example.com/home", path_substr=True)

      These evaluate to False:
        match_url("https://www.example.com/home", "https://example.com/home?q=1")
        match_url("https://www.example.com", "https://example.com/home?q=1", ignore_query=True)
        match_url("https://example.com/app/page", "https://example.com/home", path_substr=True)
    """
    url_a = urlparse(url1)
    url_b = urlparse(url2)
    path_a, path_b = url_a.path, url_b.path
    if (path_substr is False and path_a != path_b) or (path_substr is True and path_b not in path_a):
        return False
    host_a = url_a.hostname.split(".")
    host_b = url_b.hostname.split(".")
    if host_a[-2:] != host_b[-2:]:
        return False
    return ignore_query or url_a.query == url_b.query


def direct_request(method: str, url: str, *, stream: bool = False, json_args: dict = None, **kwargs) -> Response:
    """Make an http request ignoring/bypassing Chrome.

    Args:
      method: The HTTP request verb; e.g. "GET", "POST", etc.
      url: The address of the resource to return.
      stream: True to turn off `preload_content` so that the response may be streamed.
      json_args: Arguments to pass to .json() or json.dumps() if payload requires serialization.
      kwargs: Additional arguments to pass to `urllib3.PoolManager.request`.

    Returns:
      A Response object.
    """
    request = Request(method=method, url=url, stream=stream, json_args=json_args, **kwargs)
    args = vars(request)
    with urllib3.PoolManager(timeout=30, cert_reqs="CERT_REQUIRED", ca_certs=certifi.where()) as http:
        response = http.request(args.pop("method"), args.pop("url"), **args)
        return Response.from_urllib3(response)
