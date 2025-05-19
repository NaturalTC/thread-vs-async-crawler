# Thread vs Async Crawler Benchmark

This project compares three Python web crawling approaches on the same workload:
- **Single-threaded** (sequential requests)
- **ThreadPoolExecutor** (thread-based concurrency)
- **asyncio + aiohttp** (event-driven concurrency)

And stores the webscraped data from www.wikipedia.org into a MongoDB.

## Requirements

- Python 3.8+
- `aiohttp`
- `requests`
- `beautifulsoup4`
- `python-dotenv`
- `pymongo`
- `matplotlib`
  
Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

**Run the benchmark script:**

```bash
python benchmark.py
```

## Results

![alt text](/results/benchmark_plot.png)

## Conclusion

Our findings show that the async crawler generally outperforms the threaded crawler in terms of speed and resource efficiency, especially when handling a large number of I/O-bound tasks. Threading can be simpler for small-scale tasks, but asynchronous programming provides better scalability for high-concurrency workloads. While storing data wescraped into a MongoDB.

## License

MIT License

## Author

Jose
