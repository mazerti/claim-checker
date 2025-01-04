from googlesearch import search
from newspaper import Article
from urllib.parse import urlparse
from time import sleep


ignored_sites = ["reddit.com", "linkedin.com", "facebook.com"]


def build_query(claim):
    query = f'"{claim}" + ("article" OR "news" OR "opinion" OR "editorial") -pdf'
    for site in ignored_sites:
        query += " -site:" + site
    return query


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
        fetched_sites = set()
        start = 0
        try:
            print("query:", query)
            results = search(
                query,
                num_results=10,
                sleep_interval=start / 10,
                lang="en",
            )

            # Yield each result
            for result in results:
                site = urlparse(result).hostname
                if site not in fetched_sites:
                    query += f" -site:{site}"
                    fetched_sites.add(site)
                    yield result

            # Move to the next batch of results
            sleep(2.0)

        except Exception as e:
            print(f"Error occurred during search: {e}")
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
        print(f"Failed to fetch article from {url}: {e}")


def query_articles(claim, num_articles=3):
    print(f"Fetching URLs for query: {claim}")

    # Fetch URLs
    query = build_query(claim)
    urls_generator = fetch_urls_generator(query)

    articles = []

    for i, url in enumerate(urls_generator):
        if i >= 100:
            break  # safety measure to limit the number of scraped article
        if len(articles) >= num_articles:
            break
        print(f"\nScraping {url}...")
        article = scrape_article(url)
        if article:
            print("\nScraped Content (First 500 characters):")
            print(article["content"][:500])
            articles.append(article)
        else:
            print("\nFailed to scrape content.")

    return articles
