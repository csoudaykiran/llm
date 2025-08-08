import requests
from bs4 import BeautifulSoup
from lxml import html
import lxml.html.clean
import markdownify
from playwright.sync_api import sync_playwright

def get_page_source_with_js(url):
    """
    Fetches the full page source after JavaScript has executed.
    Uses Playwright for browser automation.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, wait_until='networkidle', timeout=60000)  # Wait for network to be idle, meaning most content is loaded
            html_content = page.content()
            browser.close()
        return html_content
    except Exception as e:
        print(f"Error with Playwright: {e}")
        return None

def extract_main_content(html_content):
    """
    Identifies and extracts the main content section of a webpage.
    This uses a heuristics-based approach to find the most likely content area.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Common selectors for main content
    main_selectors = [
        'main',
        'article',
        '.main',
        '#main',
        '.content',
        '#content'
    ]

    main_div = None
    for selector in main_selectors:
        main_div = soup.select_one(selector)
        if main_div:
            break
            
    if not main_div:
        # Fallback to body if no main content area is found
        main_div = soup.find('body')
        
    return str(main_div) if main_div else None

def clean_html(html_string):
    """
    Cleans up the HTML by removing noise like scripts, styles, and other non-content tags.
    """
    if not html_string:
        return ""
    
    cleaner = lxml.html.clean.Cleaner(
        style=True,
        links=True,
        add_nofollow=True,
        page_structure=False,
        safe_attrs_only=False
    )
    
    # Use lxml to clean, then re-parse with BeautifulSoup for consistency
    tree = html.fromstring(html_string)
    cleaned_tree = cleaner.clean_html(tree)
    return html.tostring(cleaned_tree, pretty_print=True, encoding='unicode')

def convert_to_markdown_with_details(html_string):
    """
    Converts a cleaned HTML string to a rich Markdown format, preserving links,
    bold, and italic text.
    """
    if not html_string:
        return ""
        
    # markdownify is a great tool for this, as it handles formatting
    md_converter = markdownify.MarkdownConverter(
        escape_underscores=False,
        substitutions=[
            ('h1', '##'), ('h2', '###'), ('h3', '####'),
            ('h4', '#####'), ('h5', '######'), ('h6', '#######')
        ]
    )
    
    markdown_output = md_converter.convert(html_string)
    
    return markdown_output

def scrape_robustly(url):
    """
    Orchestrates the entire scraping process.
    """
    # 1. Fetch the page with JS execution
    print("Fetching page with Playwright...")
    html_with_js = get_page_source_with_js(url)
    if not html_with_js:
        return "Failed to fetch content."

    # 2. Identify the main content area
    print("Identifying main content area...")
    main_content_html = extract_main_content(html_with_js)
    if not main_content_html:
        return "Could not identify main content."

    # 3. Clean the HTML
    print("Cleaning HTML...")
    cleaned_html = clean_html(main_content_html)

    # 4. Convert the cleaned HTML to rich Markdown
    print("Converting to Markdown...")
    markdown_content = convert_to_markdown_with_details(cleaned_html)
    
    return markdown_content

# Example usage:
url = 'https://en.wikipedia.org/wiki/Python_(programming_language)' # A modern site with JS
scraped_data = scrape_robustly(url)

# Save to file
if scraped_data:
    with open('robust_scraped_content.md', 'w', encoding='utf-8') as f:
        f.write(scraped_data)
    print("\nContent saved to robust_scraped_content.md")
else:
    print("No content to save.")