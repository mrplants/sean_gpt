import requests
from bs4 import BeautifulSoup
from tempfile import NamedTemporaryFile
import os
from tqdm import tqdm
from pathlib import Path

def find_pdf_links(url):
    """
    Finds and returns all the PDF links present in a webpage.

    Args:
    url (str): The URL of the webpage to scan for PDF links.

    Returns:
    list: A list of URLs (str) that are linked to PDF files.
    """
    # Send a GET request to the specified URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Failed to load page: {url}")

    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all anchor tags, then filter out those with href ending in '.pdf'
    pdf_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.pdf')]

    return pdf_links

def format_size(bytes, unit='MB'):
    """
    Formats the file size into a more readable format.

    Args:
    bytes (int): File size in bytes.
    unit (str): The unit to convert to ('KB', 'MB', or 'GB').

    Returns:
    str: Formatted file size.
    """
    factor = 1024
    if unit == 'KB':
        return f"{bytes / factor:.2f} KB"
    elif unit == 'MB':
        return f"{bytes / (factor ** 2):.2f} MB"
    elif unit == 'GB':
        return f"{bytes / (factor ** 3):.2f} GB"
    else:
        return f"{bytes} bytes"

def download_to_file(pdf_url, filepath):
    """
    Downloads a PDF from the given URL, saving it to the indicated filepath.

    Args:
    pdf_url (str): The URL from where to download the PDF.
    filepath (str): The filepath to save the PDF to.

    Returns:
    int: Updated total size of the downloaded PDF.
    """
    with requests.get(pdf_url, stream=True) as pdf_response:
        if pdf_response.status_code != 200:
            print(f"Failed to download PDF: {pdf_url}")
            return 0

        # Create a file to store the PDF
        with open(Path(filepath) / os.path.basename(pdf_url), 'wb') as f:
            for chunk in pdf_response.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)

            # Update total size
            total_size = f.tell()

    return total_size

if __name__ == '__main__':
    # Retrieve the PDF links from the Moltensalt website
    url = 'http://moltensalt.org/references/static/downloads/pdf/index.html'
    pdf_links = find_pdf_links(url)
    total_size = 0
    for pdf_link in tqdm(pdf_links):
        download_dir = os.path.dirname(__file__)+'/../datasets/moltensalt_org/pdf'
        total_size += download_to_file(pdf_link, download_dir)

    print(f'Total size of downloaded PDFs: {format_size(total_size)}')
