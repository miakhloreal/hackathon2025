# bvdl (Python Version)

This is a Python port of the [original bvdl tool](https://github.com/joelkoen/bvdl) written in Rust. It provides the same functionality for scraping product information from Bazaarvoice APIs.

## Installation

### From source

```bash
# Clone the repository
git clone https://github.com/yourusername/bvdl
cd bvdl

# Install with pip
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Using pip (when published to PyPI)

```bash
pip install bvdl
```

## Usage

bvdl requires a deployment ID or passkey and will print raw JSON data on individual lines. You'll need to find a deployment ID or passkey by inspecting network requests. bvdl can use a deployment ID to find a passkey for you.

```txt
https://apps.bazaarvoice.com/deployments/[CLIENT_NAME]/[SITE_NAME]/production/[LOCALE]/bv.js
https://display.ugc.bazaarvoice.com/static/[CLIENT_NAME]/[SITE_NAME]/[LOCALE]/bvapi.js
    -> CLIENT_NAME/SITE_NAME/LOCALE

  OR

https://api.bazaarvoice.com/data/[...].json?passkey=[PASSKEY]
   -> PASSKEY
```

### Examples

**Scraping Products:**
```bash
# Using a deployment ID (will resolve to passkey automatically)
bvdl main lenovo-au/main_site/en_AU > lenovo-au.jsonl

# Using a passkey directly
bvdl main capxgdWJRBjQt4SmgzkMVZPiinJsxVDEIfrtpsf4CfrEw > lenovo-au.jsonl
```

**Scraping Reviews:**
```bash
# Get all reviews (requires product ID filter for most Bazaarvoice setups)
bvdl reviews PASSKEY --product-id PRODUCT_ID > reviews.jsonl

# Example with real product ID
bvdl reviews caWJuNyYsn660UOOYFJFZgtXmIgCfxu0iqSHOj0GCAUIo --product-id ASK09 > reviews.jsonl
```

**Other Commands:**
```bash
# View help
bvdl --help

# Check version
bvdl --version

# Get help for specific commands
bvdl main --help
bvdl reviews --help
```

### Progress monitoring

When scraping a large amount of data, you can use pv to see progress:

```bash
# For products
bvdl main lenovo-au/main_site/en_AU | pv -albt > lenovo-au.jsonl

# For reviews  
bvdl reviews PASSKEY --product-id PRODUCT_ID | pv -albt > reviews.jsonl
```

### Important Notes for Reviews

**Review API Requirements:**
- Most Bazaarvoice review APIs require filtering by ProductId, AuthorId, CategoryAncestorId, SubmissionId, or Id
- Use `--product-id` to specify which product's reviews to fetch
- Without proper filtering, you may get "ERROR_PARAM_INVALID_FILTER_ATTRIBUTE" errors

**Finding Product IDs:**
```bash
# First get product IDs from the products API
bvdl main PASSKEY | jq -r '.id' | head -10

# Then use those IDs to get reviews
bvdl reviews PASSKEY --product-id PRODUCT_ID
```

## Development

### Setup development environment

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

### Running tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=bvdl

# Run specific test file
pytest tests/test_client.py -v
```

### Code quality tools

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## Architecture

The Python version maintains the same functionality as the original Rust implementation:

- **Async/Concurrent**: Uses `asyncio` and `aiohttp` for concurrent API requests (up to 10 simultaneous)
- **Smart pagination**: Handles Bazaarvoice's 300,000 item limit by switching sort order
- **Deployment ID resolution**: Automatically fetches passkeys from deployment IDs
- **JSONL output**: Outputs one JSON object per line for easy streaming and processing

### Key differences from Rust version

- Uses `aiohttp` instead of `reqwest` for HTTP requests
- Uses `asyncio` instead of Tokio for async runtime
- Uses `pydantic` for data validation instead of serde
- Uses `typer` for CLI instead of clap

## Performance

The Python version should have comparable performance for typical use cases:
- I/O bound operations (API requests) are the bottleneck, not CPU
- Async implementation ensures efficient concurrent requests
- For very large datasets, consider using `orjson` for faster JSON parsing

## License

MIT License (same as original project)

## Credits

Original Rust implementation by Joel Koen. Python port maintains API compatibility.