# Thread vs Async Crawler

This project compares the performance and implementation of web crawlers using threading and asynchronous programming in Python.

## Features

- **Threaded Crawler:** Uses Python's `threading` module.
- **Async Crawler:** Uses `asyncio` and `aiohttp`.
- Performance benchmarking and comparison.
- Simple, extensible codebase.

## Requirements

- Python 3.8+
- `aiohttp`
- `requests`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the threaded crawler:

```bash
python threaded_crawler.py
```

Run the async crawler:

```bash
python async_crawler.py

```

## Results

![alt text](/results/benchmark_plot.png)

## Conclusion

Our findings show that the async crawler generally outperforms the threaded crawler in terms of speed and resource efficiency, especially when handling a large number of I/O-bound tasks. Threading can be simpler for small-scale tasks, but asynchronous programming provides better scalability for high-concurrency workloads.

## License

MIT License

## Author

Jose
