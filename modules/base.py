from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

class BaseEnumerator(ABC):
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.rate_limit_delay = 0.5  # Default delay between requests
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self._get_headers())
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        self.executor.shutdown(wait=False)
    
    @abstractmethod
    async def enumerate(self) -> Dict[str, Any]:
        """
        Abstract method that all enumerator modules must implement.
        Returns a dictionary containing the enumeration results.
        """
        pass
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Returns headers for API requests with latest Chrome User-Agent
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        if self.token:
            headers['Authorization'] = self.token
        return headers
    
    async def _make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[Dict]:
        """
        Make an HTTP request with rate limiting and retry logic
        """
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self._get_headers())
            
        retries = 3
        while retries > 0:
            try:
                async with getattr(self.session, method.lower())(url, **kwargs) as response:
                    if response.status == 429:  # Rate limited
                        retry_after = float(response.headers.get('Retry-After', self.rate_limit_delay))
                        self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        retries -= 1
                        continue
                        
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        return None
                    else:
                        self.logger.error(f"Request failed with status {response.status}")
                        return None
                        
            except aiohttp.ClientError as e:
                self.logger.error(f"Request error: {str(e)}")
                retries -= 1
                if retries > 0:
                    await asyncio.sleep(1)
                    
        return None
    
    async def _parallel_requests(self, urls: list, method: str = 'GET', **kwargs) -> list:
        """
        Make multiple requests in parallel with rate limiting
        """
        tasks = []
        results = []
        
        async def fetch_with_delay(url):
            await asyncio.sleep(self.rate_limit_delay)
            return await self._make_request(url, method, **kwargs)
        
        # Create tasks for each URL
        for url in urls:
            tasks.append(asyncio.create_task(fetch_with_delay(url)))
            
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [r for r in results if not isinstance(r, Exception)]
    
    def run_in_executor(self, func, *args):
        """
        Run CPU-bound tasks in thread pool
        """
        return asyncio.get_event_loop().run_in_executor(self.executor, func, *args) 