import os
import json
from dotenv import load_dotenv
# OLD:
# try:
#     from IPython.display import Markdown, display, update_display
# except ImportError:  # Allows running outside notebooks
#     Markdown = None
#     display = None
#     update_display = None
try:
    from IPython.display import Markdown, display, update_display
    from IPython import get_ipython
except ImportError:  # Allows running without IPython installed
    Markdown = None
    display = None
    update_display = None
    get_ipython = None
import openai
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scraper import fetch_website_links, fetch_website_contents

load_dotenv()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

client = openai.OpenAI(base_url=OLLAMA_BASE_URL, api_key=os.getenv("OLLAMA_API_KEY", "none"))


def _running_in_jupyter_notebook() -> bool:
    """
    IPython exists in terminals too. Only ZMQ shells (Jupyter) reliably render Markdown via display().
    """
    if get_ipython is None:
        return False
    try:
        ip = get_ipython()
        return ip is not None and ip.__class__.__name__ == "ZMQInteractiveShell"
    except Exception:
        return False

link_system_prompt = """
You are provided with a list of links found on a webpage.
You are able to decide which of the links would be most relevant to include in a brochure about the company,
such as links to an About page, or a Company page, or Careers/Jobs pages.
You should respond in JSON as in this example:

{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}
"""
brochure_system_prompt = """
You are an assistant that analyzes the contents of several relevant pages from a company website
and creates a short brochure about the company for prospective customers, investors and recruits.
Respond in markdown without code blocks.
Include details of company culture, customers and careers/jobs if you have the information.
"""

# Or uncomment the lines below for a more humorous brochure - this demonstrates how easy it is to incorporate 'tone':

# brochure_system_prompt = """
# You are an assistant that analyzes the contents of several relevant pages from a company website
# and creates a short, humorous, entertaining, witty brochure about the company for prospective customers, investors and recruits.
# Respond in markdown without code blocks.
# Include details of company culture, customers and careers/jobs if you have the information.
# """

def get_links_user_prompt(url):
    user_prompt = f"""
Here is the list of links on the website {url} -
Please decide which of these are relevant web links for a brochure about the company, 
respond with the full https URL in JSON format.
Do not include Terms of Service, Privacy, email links.

Links (some might be relative links):

"""

    links = fetch_website_links(url)
    user_prompt += "\n".join(links)
    return user_prompt

def select_relevant_links(url):
    print(f"Selecting relevant links for {url} by calling {OLLAMA_MODEL}")
    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(url)}
        ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content or "{}"
    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        parsed = {}

    links = parsed.get("links", [])
    if not isinstance(links, list):
        links = []

    cleaned: list[dict] = []
    for item in links:
        if not isinstance(item, dict):
            continue
        url_value = item.get("url")
        if isinstance(url_value, str) and url_value.startswith(("http://", "https://")):
            cleaned.append({"type": str(item.get("type", "relevant page")), "url": url_value})

    print(f"Found {len(cleaned)} relevant links")
    return {"links": cleaned}

def fetch_page_and_all_relevant_links(url, *, max_links: int = 8):
    cache: dict[str, str] = {}

    def get_contents(u: str) -> str:
        if u not in cache:
            cache[u] = fetch_website_contents(u)
        return cache[u]

    contents = get_contents(url)
    relevant_links = select_relevant_links(url)
    result = f"## Landing Page:\n\n{contents}\n\n## Relevant Links:\n"
    for link in relevant_links.get("links", [])[:max_links]:
        result += f"\n\n### Link: {link.get('type', 'relevant page')}\n\n"
        result += get_contents(link["url"])
    return result
def get_brochure_user_prompt(company_name, url):
    user_prompt = f"""
You are looking at a company called: {company_name}
Here are the contents of its landing page and other relevant pages;
use this information to build a short brochure of the company in markdown without code blocks.\n\n
"""
    user_prompt += fetch_page_and_all_relevant_links(url, max_links=int(os.getenv("MAX_RELEVANT_LINKS", "8")))
    user_prompt = user_prompt[:5_000]
    return user_prompt

def stream_brochure(company_name, url):
    stream = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": brochure_system_prompt},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
          ],
        stream=True
    )    
    response = ""
    # OLD:
    # if display is None or update_display is None or Markdown is None:
    # In IPython terminals, display(Markdown(...)) often prints "<...Markdown object>" instead of rendering.
    if display is None or update_display is None or Markdown is None or not _running_in_jupyter_notebook():
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            response += delta
            print(delta, end="", flush=True)
        print()
        return

    display_handle = display(Markdown(""), display_id=True)
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        response += delta
        if hasattr(display_handle, "update"):
            display_handle.update(Markdown(response))
        else:
            display_id = "brochure_stream"
            # Ensure the placeholder exists for this display_id
            display(Markdown(""), display_id=display_id)
            update_display(Markdown(response), display_id=display_id)

if __name__ == "__main__":
    stream_brochure("Bajaj life insurance", "https://bajajlifeinsurance.com")