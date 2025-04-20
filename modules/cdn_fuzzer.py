from typing import Dict, Any
import aiohttp
import asyncio
from itertools import product
import string
import random
from .base import BaseEnumerator

class CDNFuzzer(BaseEnumerator):
    CDN_DOMAINS = [
        'cdn.discordapp.com',
        'media.discordapp.net',
        'images.discordapp.net'
    ]
    
    CDN_ENDPOINTS = [
        'attachments',
        'avatars',
        'icons',
        'banners',
        'splashes',
        'emojis',
        'stickers'
    ]
    
    IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif', 'webp']
    
    async def enumerate(self) -> Dict[str, Any]:
        results = {
            'cdn_endpoints': {},
            'vulnerable_patterns': [],
            'interesting_findings': [],
            'rate_limits': {},
            'metadata': {}
        }
        
        # Test basic CDN endpoint patterns
        for domain in self.CDN_DOMAINS:
            results['cdn_endpoints'][domain] = await self._test_cdn_endpoints(domain)
            
        # Fuzz CDN paths with various patterns
        fuzz_results = await self._fuzz_cdn_paths()
        results['vulnerable_patterns'].extend(fuzz_results['vulnerable'])
        results['interesting_findings'].extend(fuzz_results['interesting'])
        
        # Test metadata extraction
        metadata_results = await self._test_metadata_extraction()
        results['metadata'] = metadata_results
        
        return results
    
    async def _test_cdn_endpoints(self, domain: str) -> Dict[str, Any]:
        """
        Test basic CDN endpoint functionality and security
        """
        endpoint_results = {}
        
        for endpoint in self.CDN_ENDPOINTS:
            # Generate test paths
            test_paths = [
                f'https://{domain}/{endpoint}/123456789',
                f'https://{domain}/{endpoint}/../../etc/passwd',  # Path traversal test
                f'https://{domain}/{endpoint}/%00test',  # Null byte test
                f'https://{domain}/{endpoint}/{"A" * 1000}'  # Buffer test
            ]
            
            endpoint_results[endpoint] = []
            
            for path in test_paths:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(path, headers=self._get_headers()) as response:
                            result = {
                                'path': path,
                                'status': response.status,
                                'headers': dict(response.headers),
                                'size': len(await response.read())
                            }
                            endpoint_results[endpoint].append(result)
                            
                            # Check for interesting responses
                            if response.status not in [404, 403]:
                                self.logger.info(f"Interesting response from {path}: {response.status}")
                except Exception as e:
                    self.logger.error(f"Error testing path {path}: {str(e)}")
                    
        return endpoint_results
    
    async def _fuzz_cdn_paths(self) -> Dict[str, list]:
        """
        Fuzz CDN paths with various patterns to find potential vulnerabilities
        """
        results = {
            'vulnerable': [],
            'interesting': []
        }
        
        # Generate random IDs and paths
        test_ids = [''.join(random.choices(string.hexdigits, k=16)) for _ in range(5)]
        
        patterns = [
            '{id}',
            '{id}.{ext}',
            '{id}/original',
            '{id}?size=1024',
            '{id}?width=100&height=100',
            '{endpoint}/{id}',
            'avatars/{id}/{id}',
        ]
        
        for domain in self.CDN_DOMAINS:
            for pattern in patterns:
                for test_id in test_ids:
                    for ext in self.IMAGE_EXTENSIONS:
                        path = pattern.format(
                            id=test_id,
                            ext=ext,
                            endpoint=random.choice(self.CDN_ENDPOINTS)
                        )
                        url = f'https://{domain}/{path}'
                        
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.head(url, headers=self._get_headers()) as response:
                                    if response.status not in [404, 403]:
                                        results['interesting'].append({
                                            'url': url,
                                            'status': response.status,
                                            'headers': dict(response.headers)
                                        })
                                        
                                    # Check for potential vulnerabilities
                                    if any(h.lower() in ['x-cache', 'x-cache-hits', 'x-served-by']
                                           for h in response.headers):
                                        results['vulnerable'].append({
                                            'url': url,
                                            'type': 'information_disclosure',
                                            'headers': dict(response.headers)
                                        })
                        except Exception as e:
                            self.logger.error(f"Error fuzzing URL {url}: {str(e)}")
                            
        return results
    
    async def _test_metadata_extraction(self) -> Dict[str, Any]:
        """
        Test for metadata extraction capabilities and potential information leakage
        """
        metadata_results = {}
        
        # Test various image sizes and formats
        test_sizes = ['16', '32', '64', '128', '256', '512', '1024', '2048', '4096']
        test_formats = ['png', 'jpg', 'webp', 'gif']
        
        for domain in self.CDN_DOMAINS:
            metadata_results[domain] = {}
            
            for size, fmt in product(test_sizes, test_formats):
                url = f'https://{domain}/avatars/123456789/test.{fmt}?size={size}'
                
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.head(url, headers=self._get_headers()) as response:
                            metadata_results[domain][f'{size}_{fmt}'] = {
                                'status': response.status,
                                'headers': dict(response.headers)
                            }
                except Exception as e:
                    self.logger.error(f"Error testing metadata for {url}: {str(e)}")
                    
        return metadata_results 