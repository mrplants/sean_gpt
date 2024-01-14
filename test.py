import httpx

def send_post_request():
    """
    Sends a POST request to the specified URL.

    Returns:
        Response: The response object from the server.
    """
    url = "http://localhost:8000/user/token"

    try:
        # If your request does not require sending JSON, use `data=data` instead of `json=data`
        response = httpx.get(url)  # verify=False is used to skip SSL verification
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        return response
    except httpx.HTTPError as e:
        print(f'An HTTP error occurred: {e}')
        return None

# Call the function
response = send_post_request()
if response:
    print(response.status_code)
    print(response.json())
