"""Async HTTP client for Bazaarvoice API."""

import asyncio
import json
import sys
from typing import AsyncIterator, Optional

import aiohttp

from .models import ApiPage


class BazaarvoiceClient:
    """Async client for interacting with Bazaarvoice APIs."""
    
    LIMIT = 100
    MAX_CONCURRENT = 10
    PASSKEY_START = ',passkey:"'
    PASSKEY_END = '",baseUrl'
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def resolve_passkey(self, deployment_id: str) -> str:
        """Resolve a deployment ID to a passkey."""
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        url = f"https://display.ugc.bazaarvoice.com/static/{deployment_id}/bvapi.js"
        async with self.session.get(url) as response:
            response.raise_for_status()
            js_content = await response.text()
        
        # Find passkey in JavaScript content
        start_idx = js_content.find(self.PASSKEY_START)
        if start_idx == -1:
            raise ValueError("Failed to find passkey start marker")
        
        start_idx += len(self.PASSKEY_START)
        end_idx = js_content.find(self.PASSKEY_END, start_idx)
        if end_idx == -1:
            raise ValueError("Failed to find passkey end marker")
        
        passkey = js_content[start_idx:end_idx]
        sys.stderr.write(f"Found passkey: {passkey}\n")
        return passkey
    
    async def fetch_page(self, url: str) -> ApiPage:
        """Fetch a single page from the API."""
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        async with self._semaphore:
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                return ApiPage(**data)
    
    async def fetch_products(self, passkey: str) -> AsyncIterator[dict]:
        """Fetch all products from Bazaarvoice API."""
        # Resolve passkey if it looks like a deployment ID
        if "/" in passkey:
            passkey = await self.resolve_passkey(passkey)
        
        base_url = (
            f"https://api.bazaarvoice.com/data/products.json"
            f"?apiVersion=5.5&passkey={passkey}&limit={self.LIMIT}"
        )
        
        # First fetch to get total count
        first_page = await self.fetch_page(f"{base_url}&offset=0&sort=id:asc")
        total = first_page.total_results
        sys.stderr.write(f"Fetching {total} products...\n")
        
        if total >= 600_000:
            sys.stderr.write(
                "This site has more than 600 000 products. Due to API restrictions, "
                "only the first and last 300 000 will be fetched.\n"
            )
        
        # Check for errors
        if first_page.errors:
            for error in first_page.errors:
                sys.stderr.write(f"error: {error.code} - {error.message}\n")
            raise RuntimeError("Received API errors")
        
        # Yield results from first page
        for item in first_page.results:
            yield item.model_dump(by_alias=False, exclude_unset=False)
        
        # Create tasks for remaining pages
        tasks = []
        offset = self.LIMIT
        
        while offset < total:
            # Handle API limit of 300,000 items per sort order
            if offset >= 300_000:
                url = f"{base_url}&offset={offset - 300_000}&sort=id:desc"
            else:
                url = f"{base_url}&offset={offset}&sort=id:asc"
            
            task = asyncio.create_task(self._fetch_with_offset(url, offset, total))
            tasks.append(task)
            offset += self.LIMIT
        
        # Process results as they complete
        for coro in asyncio.as_completed(tasks):
            results = await coro
            for item in results:
                yield item
    
    async def _fetch_with_offset(self, url: str, offset: int, total: int) -> list[dict]:
        """Fetch a page and handle the last page edge case."""
        page = await self.fetch_page(url)
        
        if page.errors:
            for error in page.errors:
                sys.stderr.write(f"error: {error.code} - {error.message}\n")
            raise RuntimeError("Received API errors")
        
        # Calculate how many items to return (handle last page)
        next_offset = offset + self.LIMIT
        ignore_last = max(0, next_offset - total) if next_offset >= total else 0
        max_items = len(page.results) - ignore_last
        
        return [
            item.model_dump(by_alias=False, exclude_unset=False)
            for i, item in enumerate(page.results)
            if i < max_items
        ]
    
    async def fetch_reviews(self, passkey: str, product_id: Optional[str] = None) -> AsyncIterator[dict]:
        """Fetch all reviews from Bazaarvoice API."""
        # Resolve passkey if it looks like a deployment ID
        if "/" in passkey:
            passkey = await self.resolve_passkey(passkey)
        
        base_url = (
            f"https://api.bazaarvoice.com/data/reviews.json"
            f"?apiVersion=5.5&passkey={passkey}&limit={self.LIMIT}"
        )
        
        # Add product filter if specified
        if product_id:
            base_url += f"&Filter=ProductId:{product_id}"
        
        # First fetch to get total count
        first_page = await self.fetch_page(f"{base_url}&offset=0&sort=SubmissionTime:desc")
        total = first_page.total_results
        
        if product_id:
            sys.stderr.write(f"Fetching {total} reviews for product {product_id}...\n")
        else:
            sys.stderr.write(f"Fetching {total} reviews...\n")
        
        if total >= 600_000:
            sys.stderr.write(
                "This site has more than 600 000 reviews. Due to API restrictions, "
                "only the first and last 300 000 will be fetched.\n"
            )
        
        # Check for errors
        if first_page.errors:
            for error in first_page.errors:
                sys.stderr.write(f"error: {error.code} - {error.message}\n")
            raise RuntimeError("Received API errors")
        
        # Yield results from first page
        for item in first_page.results:
            yield item.model_dump(by_alias=False, exclude_unset=False)
        
        # Create tasks for remaining pages
        tasks = []
        offset = self.LIMIT
        
        while offset < total:
            # Handle API limit of 300,000 items per sort order
            if offset >= 300_000:
                url = f"{base_url}&offset={offset - 300_000}&sort=SubmissionTime:asc"
            else:
                url = f"{base_url}&offset={offset}&sort=SubmissionTime:desc"
            
            task = asyncio.create_task(self._fetch_with_offset(url, offset, total))
            tasks.append(task)
            offset += self.LIMIT
        
        # Process results as they complete
        for coro in asyncio.as_completed(tasks):
            results = await coro
            for item in results:
                yield item