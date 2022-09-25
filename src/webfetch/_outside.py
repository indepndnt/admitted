from __future__ import annotations
import json
from typing import BinaryIO
import certifi
import urllib3


def outside_request(method: str, url: str, destination: str | BinaryIO, **kwargs):
    """Make an http request ignoring/bypassing Chrome.

    Args:
      method: The http request method.
      url: The address of the resource to return.
      destination: One of 'text', 'json', or 'raw' to return the response data, or a file pointer to stream to.
        Any other value (e.g. None or 'response') will return the urllib3.HTTPResponse object.
      kwargs: Additional arguments to pass to `urllib3.PoolManager.request`.

    Returns:
      Response data from the request, of the type `destination`, or the file pointer provided.
    """
    stream = hasattr(destination, "write")
    with urllib3.PoolManager(timeout=30, cert_reqs="CERT_REQUIRED", ca_certs=certifi.where()) as http:
        response = http.request(method, url, preload_content=not stream, **kwargs)
        if stream:
            for chunk in response.stream(1024):
                destination.write(chunk)
            return destination
        data = response.data
        if destination == "raw":
            return data
        if destination == "text":
            return data.decode()
        if destination == "json":
            return json.loads(data)
        return response
