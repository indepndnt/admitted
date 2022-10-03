from __future__ import annotations
import certifi
import urllib3
from .models import Request, Response


def outside_request(method: str, url: str, stream: bool = False, json_args: dict = None, **kwargs) -> Response:
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
