from crawl4ai import WebCrawler

crawler = WebCrawler()

def observe(url):
    result = crawler.run(
        url=url,
        extract_links=True,
        extract_text=True
    )
    return result.links
