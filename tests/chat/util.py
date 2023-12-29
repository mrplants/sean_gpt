from sean_gpt.util.describe import describe

@describe(
""" Blocks and yields a streaming http response.

Args:
    request_type (str):  The request type.
    url (str):  The request URL.
    request_kwargs (dict):  Keyword arguments to pass to the client.
    client: The httpx client.
    
Yields:
    Chunks of text from the body of the response.
""")
def stream_response(request_type, url, request_kwargs, client):
    request_function = {
        "post": client.post,
        "get": client.get,
        "put": client.put,
        "delete": client.delete,
    }[request_type.lower()]
    with request_function(url, **request_kwargs, stream=True) as response:
        for chunk in response.iter_bytes():
            if chunk:  # Skip empty chunks
                yield chunk.decode('utf-8')