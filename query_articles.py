from googlesearch import search
from newspaper import Article
from urllib.parse import urlparse
from time import sleep
import logging


def fetch_urls_generator(query):
    """
    A generator function to yield an unlimited number of articles using googlesearch.

    Parameters:
    - query: Search query string.

    Yields:
    - URLs of search results (articles).
    """
    while True:
        # Fetch search results using googlesearch
        fetched_urls = set()
        try:
            logging.info("query:", query)
            results = search(query, num_results=10, lang="en")

            # Yield each result
            for result in results:
                site = urlparse(result).hostname
                if site not in fetched_urls:
                    query += f" -site:{site}"
                    fetched_urls.add(site)
                    yield result

            # Move to the next batch of results
            sleep(2.0)

        except Exception as e:
            logging.error(f"Error occurred during search: {e}")
            break


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
        logging.info(f"Failed to fetch article from {url}: {e}")


def query_articles(claim, num_results=3):
    logging.info(f"Fetching URLs for query: {claim}")

    # Fetch URLs
    query = f'"{claim}" + ("article" OR "news" OR "opinion" OR "editorial") -pdf -site:reddit.com'
    urls_generator = fetch_urls_generator(query)

    articles = []

    for url, i in enumerate(urls_generator):
        if i >= 100:
            break  # safety measure to limit the number of scraped article
        if len(articles) >= num_results:
            break
        logging.info(f"\nScraping {url}...")
        article = scrape_article(url)
        if article:
            logging.info("\nScraped Content (First 500 characters):")
            logging.info(article["content"][:500])
            articles.append(article)
        else:
            logging.info("\nFailed to scrape content.")

    return articles
