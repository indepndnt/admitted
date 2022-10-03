from __future__ import annotations
import certifi
import urllib3
from .models import Response


def outside_request(method: str, url: str, stream: bool = False, **kwargs) -> Response:
    """Make an http request ignoring/bypassing Chrome.

    Args:
      method: The http request method.
      url: The address of the resource to return.
      stream: True to turn off `preload_content` so that the response may be streamed.
      kwargs: Additional arguments to pass to `urllib3.PoolManager.request`.

    Returns:
      A Response object.
    """
    with urllib3.PoolManager(timeout=30, cert_reqs="CERT_REQUIRED", ca_certs=certifi.where()) as http:
        response = http.request(method, url, preload_content=not stream, **kwargs)
        return Response.from_urllib3(response)
