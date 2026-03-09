from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urldefrag, urlparse


# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit
    """
    # OLD:
    # response = requests.get(url, headers=headers)
    # soup = BeautifulSoup(response.content, "html.parser")
    try:
        response = requests.get(url, headers=headers, timeout=(5, 20))
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
    except requests.RequestException:
        return "No title found\n\n"
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]


def fetch_website_links(url):
    """
    Return the links on the webiste at the given url
    I realize this is inefficient as we're parsing twice! This is to keep the code in the lab simple.
    Feel free to use a class and optimize it!
    """
    # OLD:
    # response = requests.get(url, headers=headers)
    # soup = BeautifulSoup(response.content, "html.parser")
    # links = [link.get("href") for link in soup.find_all("a")]
    # return [link for link in links if link]
    try:
        response = requests.get(url, headers=headers, timeout=(5, 20))
        response.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    raw_links = [a.get("href") for a in soup.find_all("a") if a.get("href")]

    normalized: list[str] = []
    for href in raw_links:
        href = href.strip()
        if not href:
            continue
        if href.startswith(("mailto:", "tel:", "javascript:")):
            continue

        absolute = urljoin(url, href)
        absolute, _frag = urldefrag(absolute)
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            continue
        normalized.append(absolute)

    # Preserve order, dedupe
    return list(dict.fromkeys(normalized))
