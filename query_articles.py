from googlesearch import search
from newspaper import Article
from urllib.parse import urlparse


def fetch_urls(query, num_results=3):
    return [url for url in search(query, num_results=num_results)]


def scrape_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        publisher = (
            urlparse(url).netloc.split(".")[-2].capitalize()
        )  # Extract publisher's name
        return {
            "title": article.title,
            "content": article.text,
            "url": url,
            "publisher": publisher,
        }
    except Exception as e:
        print(f"Failed to fetch article from {url}: {e}")


def query_articles(claim, num_results=3):
    print(f"Fetching URLs for query: {claim}")

    # Fetch URLs
    urls = fetch_urls(claim, num_results)
    print("Fetched URLs:")
    for url in urls:
        print(url)

    articles = []

    for url in urls:
        print(f"\nScraping {url}...")
        article = scrape_article(url)
        if article:
            print("\nScraped Content (First 500 characters):")
            print(article["content"][:500])
            articles.append(article)
        else:
            print("\nFailed to scrape content.")

    return articles
