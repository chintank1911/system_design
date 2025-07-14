import time
import requests
import sqlite3
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urljoin, urlparse
import socket
import urllib.robotparser
import ssl
from urllib.request import urlopen


def fetch_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.text
        page_size_bytes = len(html_content)

        # Convert to KB and MB
        page_size_kb = page_size_bytes / 1024  # 1 KB = 1024 bytes
        page_size_mb = page_size_kb / 1024  # 1 MB = 1024 KB

        print(f"Fetched {url} (Size: {page_size_bytes} bytes, {page_size_kb:.2f} KB, {page_size_mb:.2f} MB)")
        return html_content
    else:
        print(f"Failed to fetch {url}: {response.status_code}")
        return None


def check_robots_txt(url):
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

    # Create a robot parser object
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)

    # Create an unverified SSL context
    ssl_context = ssl._create_unverified_context()

    try:
        # Open robots.txt with the unverified SSL context
        with urlopen(robots_url, context=ssl_context) as response:
            rp.parse(response.read().decode("utf-8").splitlines())
        print(f"Robots.txt checked at {robots_url}")
    except Exception as e:
        print(f"Failed to access robots.txt for {url}: {e}")

    return rp


def save_html_to_db(html_content, url, conn):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO website_content (url, html)
        VALUES (?, ?)
    ''', (url, html_content))
    conn.commit()


def clear_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS website_content (
            id INTEGER PRIMARY KEY,
            url TEXT NOT NULL,
            html TEXT NOT NULL
        )
    ''')
    cursor.execute('DELETE FROM website_content')
    conn.commit()


def extract_links(html_content, url):
    soup = BeautifulSoup(html_content, "html.parser")
    links = set()

    base_domain = urlparse(url).netloc.replace("www.", "")
    for anchor in soup.find_all('a', href=True):
        link = urljoin(url, anchor['href'])
        link_domain = urlparse(link).netloc.replace("www.", "")

        if link_domain == base_domain:
            links.add(link)

    print(f"Extracted {len(links)} links from {url}")
    return links


def get_ip_address(url):
    hostname = urlparse(url).netloc
    ip_address = socket.gethostbyname(hostname)
    print(f"Resolved {hostname} to {ip_address}")
    return ip_address


def web_crawler():
    seed_urls = ["https://geeksforgeeks.org", "https://www.google.com/?hl=en", ]
    robot_map = {}

    for seed_url in seed_urls:
        robot_map[seed_url] = check_robots_txt(seed_url)

    print("\n-----------------------------------------------\n")

    frontier = deque([seed_url for seed_url in seed_urls])  # Initialize frontier queue
    visited = set()
    max_pages = 10

    conn = sqlite3.connect("web_crawler.db")
    clear_table(conn)

    while frontier and len(visited) < max_pages:
        url = frontier.popleft()  # Get the next URL to crawl

        # skip if already visited
        if url in visited:
            print(f"Already visited {url}")
            continue

        # Check if the URL is allowed by robots.txt before crawling
        parsed_url = urlparse(url)
        rp = robot_map.get(f"{parsed_url.scheme}://{parsed_url.netloc}", None)
        if rp and not rp.can_fetch("*", url):
            print(f"Skipping {url}: Disallowed by robots.txt")
            continue

        print(f"Starting to crawl {url} , Allowed by robots.txt")

        html_content = fetch_html(url)
        if html_content:
            save_html_to_db(html_content, url, conn)
            visited.add(url)
            new_links = extract_links(html_content, url)
            frontier.extend(new_links - visited)

        print("\n-----------------------------------------------\n")
        time.sleep(2)

    conn.close()


if __name__ == "__main__":
    web_crawler()
