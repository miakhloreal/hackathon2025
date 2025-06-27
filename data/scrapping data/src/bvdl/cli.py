"""Command-line interface for bvdl."""

import asyncio
import json
import sys
from typing import Annotated, Optional

import typer

from . import __version__
from .client import BazaarvoiceClient

app = typer.Typer(
    name="bvdl",
    help="Tool for scraping product information from Bazaarvoice.",
    add_completion=False,
)


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        typer.echo(f"bvdl {__version__}")
        raise typer.Exit()


@app.command()
def main(
    passkey: Annotated[
        str,
        typer.Argument(
            help="Bazaarvoice passkey or deployment ID (e.g., 'client/site/locale')"
        ),
    ],
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            help="Show version and exit",
        ),
    ] = False,
):
    """
    Download product data from Bazaarvoice API.
    
    The passkey can be either:
    - A direct passkey from API requests
    - A deployment ID in format 'client/site/locale'
    
    Output is in JSONL format (one JSON object per line).
    
    Examples:
        bvdl lenovo-au/main_site/en_AU > products.jsonl
        bvdl capxgdWJRBjQt4SmgzkMVZPiinJsxVDEIfrtpsf4CfrEw > products.jsonl
    """
    try:
        asyncio.run(download_products(passkey))
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrupted\n")
        raise typer.Exit(1)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        raise typer.Exit(1)


async def download_products(passkey: str):
    """Download products and output as JSONL."""
    async with BazaarvoiceClient() as client:
        async for product in client.fetch_products(passkey):
            # Output each product as a JSON line
            print(json.dumps(product, separators=(',', ':')))


@app.command()
def reviews(
    passkey: Annotated[
        str,
        typer.Argument(
            help="Bazaarvoice passkey or deployment ID (e.g., 'client/site/locale')"
        ),
    ],
    product_id: Annotated[
        Optional[str],
        typer.Option(
            "--product-id",
            "-p",
            help="Filter reviews for specific product ID",
        ),
    ] = None,
):
    """
    Download review data from Bazaarvoice API.
    
    The passkey can be either:
    - A direct passkey from API requests
    - A deployment ID in format 'client/site/locale'
    
    Output is in JSONL format (one JSON object per line).
    
    Examples:
        bvdl reviews lenovo-au/main_site/en_AU > reviews.jsonl
        bvdl reviews PASSKEY --product-id PROD123 > product-reviews.jsonl
    """
    try:
        asyncio.run(download_reviews(passkey, product_id))
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrupted\n")
        raise typer.Exit(1)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        raise typer.Exit(1)


async def download_reviews(passkey: str, product_id: Optional[str] = None):
    """Download reviews and output as JSONL."""
    async with BazaarvoiceClient() as client:
        async for review in client.fetch_reviews(passkey, product_id):
            # Output each review as a JSON line
            print(json.dumps(review, separators=(',', ':')))


if __name__ == "__main__":
    app()