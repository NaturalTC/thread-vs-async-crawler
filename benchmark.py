import os
import time
import json
import asyncio
from collections import deque
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

import requests
import aiohttp
from bs4 import BeautifulSoup

from dotenv import load_dotenv
from pymongo import MongoClient

# ─── Configuration ─────────────────────────────────────────────────────────────

load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME   = os.getenv("MONGODB_DBNAME", "webCrawlerArchive")
RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# ─── Threaded Crawler ──────────────────────────────────────────────────────────

class ThreadedCrawler:
    def __init__(self, seed_url, max_pages=100):
        self.queue = deque([seed_url])
        self.visited = set()
        self.max_pages = max_pages
        self.start_time = None
        self.pages_crawled = 0

        self.db_client = MongoClient(MONGO_URI) if MONGO_URI else None
        if self.db_client:
            self.collection = self.db_client[DB_NAME].webpages
            self.collection.delete_many({})

    def fetch(self, url):
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            return r.text
        except:
            return ""

    def parse(self, url, html):
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title else ""
        body  = soup.body.get_text(" ", strip=True)[:500] if soup.body else ""

        if self.db_client:
            self.collection.insert_one({
                "url": url, "title": title, "content": body
            })

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http") and href not in self.visited:
                self.queue.append(href)

    def crawl_single(self):
        self.start_time = time.time()
        while self.queue and self.pages_crawled < self.max_pages:
            url = self.queue.popleft()
            self.visited.add(url)
            html = self.fetch(url)
            if html:
                self.parse(url, html)
                self.pages_crawled += 1
        return time.time() - self.start_time

    def crawl_threaded(self, max_workers=10):
        self.start_time = time.time()
        futures = []
        with ThreadPoolExecutor(max_workers=max_workers) as execu:
            # kickoff
            for _ in range(min(len(self.queue), max_workers)):
                url = self.queue.popleft()
                self.visited.add(url)
                futures.append(execu.submit(self.fetch_and_parse, url))

            while futures and self.pages_crawled < self.max_pages:
                done, _ = wait(futures, return_when=FIRST_COMPLETED)
                for fut in done:
                    fut.result()
                    self.pages_crawled += 1
                    futures.remove(fut)
                    if self.queue:
                        nxt = self.queue.popleft()
                        self.visited.add(nxt)
                        futures.append(execu.submit(self.fetch_and_parse, nxt))
        return time.time() - self.start_time

    def fetch_and_parse(self, url):
        html = self.fetch(url)
        if html:
            self.parse(url, html)

# ─── Asyncio Crawler ────────────────────────────────────────────────────────────

class AsyncCrawler:
    def __init__(self, seed_url, max_pages=100):
        self.queue = deque([seed_url])
        self.visited = set()
        self.max_pages = max_pages
        self.pages = 0

    async def fetch(self, session, url):
        try:
            async with session.get(url, timeout=5) as resp:
                return await resp.text()
        except:
            return ""

    async def parse(self, url, html):
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])
            if href.startswith("http") and href not in self.visited:
                self.queue.append(href)

    async def worker(self, session, sem):
        while self.pages < self.max_pages and self.queue:
            url = self.queue.popleft()
            self.visited.add(url)
            async with sem:
                html = await self.fetch(session, url)
            if html:
                await self.parse(url, html)
            self.pages += 1

    async def crawl(self, concurrency=10):
        start = time.time()
        sem = asyncio.Semaphore(concurrency)
        async with aiohttp.ClientSession() as session:
            tasks = [asyncio.create_task(self.worker(session, sem))
                     for _ in range(concurrency)]
            await asyncio.gather(*tasks)
        return time.time() - start

# ─── Benchmarking ───────────────────────────────────────────────────────────────

def time_fn(fn, repeats=3):
    results = []
    for _ in range(repeats):
        elapsed = fn()
        results.append(elapsed)
    return results

def main():
    seed      = "https://wikipedia.org/"
    max_pages = 100
    workers   = 20
    repeats   = 5

    tc = ThreadedCrawler(seed, max_pages)
    ac = AsyncCrawler(seed, max_pages)

    print("Running benchmarks, please wait…")

    results = {
        "single_thread": time_fn(tc.crawl_single, repeats),
        "thread_pool":   time_fn(lambda: tc.crawl_threaded(workers), repeats),
        "asyncio":       time_fn(lambda: asyncio.run(ac.crawl(workers)), repeats),
    }

    # save raw JSON
    with open(f"{RESULTS_DIR}/raw_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # plot
    import matplotlib.pyplot as plt
    plt.figure(figsize=(8,5))
    plt.boxplot(
        [results["single_thread"],
         results["thread_pool"],
         results["asyncio"]],
        labels=["Single", "Threads", "Asyncio"]
    )
    plt.ylabel("Seconds")
    plt.title("Crawler Performance Comparison")
    plt.grid(alpha=0.4, linestyle="--")
    plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/benchmark_plot.png")
    plt.close()

    print(f"\nDone! See:\n • {RESULTS_DIR}/raw_results.json\n • {RESULTS_DIR}/benchmark_plot.png")

if __name__ == "__main__":
    main()
