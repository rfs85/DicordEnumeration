from typing import Dict, Any
import aiohttp
import asyncio
from .base import BaseEnumerator

class ServicesEnumerator(BaseEnumerator):
    DISCORD_API_VERSION = 9
    BASE_URL = f"https://discord.com/api/v{DISCORD_API_VERSION}"
    
    ENDPOINTS = [
        '/gateway',
        '/gateway/bot',
        '/voice/regions',
        '/applications/public',
        '/oauth2/applications/@me',
        '/users/@me',
        '/users/@me/guilds',
        '/users/@me/connections'
    ]

    SERVICES = {
        'gateway': 'wss://gateway.discord.gg',
        'cdn': 'https://cdn.discordapp.com',
        'media': 'https://media.discordapp.net',
        'status': 'https://status.discord.com',
        'support': 'https://support.discord.com',
        'developer': 'https://discord.com/developers',
        'application': 'https://discord.com/api/applications'
    }

    async def enumerate(self) -> Dict[str, Any]:
        results = {
            'api_endpoints': {},
            'services_status': {},
            'gateway_info': None,
            'voice_regions': None,
            'rate_limits': {}
        }

        # Check services availability and response headers
        for service_name, url in self.SERVICES.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=self._get_headers()) as response:
                        results['services_status'][service_name] = {
                            'status': response.status,
                            'headers': dict(response.headers),
                            'url': url
                        }
            except Exception as e:
                self.logger.error(f"Error checking service {service_name}: {str(e)}")
                results['services_status'][service_name] = {
                    'status': 'error',
                    'error': str(e),
                    'url': url
                }

        # Enumerate API endpoints
        for endpoint in self.ENDPOINTS:
            try:
                url = f"{self.BASE_URL}{endpoint}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=self._get_headers()) as response:
                        results['api_endpoints'][endpoint] = {
                            'status': response.status,
                            'headers': dict(response.headers)
                        }
                        
                        if response.status == 200:
                            try:
                                data = await response.json()
                                results['api_endpoints'][endpoint]['data'] = data
                                
                                # Store specific information
                                if endpoint == '/gateway':
                                    results['gateway_info'] = data
                                elif endpoint == '/voice/regions':
                                    results['voice_regions'] = data
                            except:
                                results['api_endpoints'][endpoint]['data'] = 'Unable to parse JSON'
                        
                        # Track rate limits
                        if 'X-RateLimit-Limit' in response.headers:
                            results['rate_limits'][endpoint] = {
                                'limit': response.headers.get('X-RateLimit-Limit'),
                                'remaining': response.headers.get('X-RateLimit-Remaining'),
                                'reset': response.headers.get('X-RateLimit-Reset')
                            }
                            
            except Exception as e:
                self.logger.error(f"Error enumerating endpoint {endpoint}: {str(e)}")
                results['api_endpoints'][endpoint] = {
                    'status': 'error',
                    'error': str(e)
                }

        # Additional checks for authenticated endpoints if token is provided
        if self.token:
            auth_results = await self._check_authenticated_endpoints()
            results.update(auth_results)

        return results

    async def _check_authenticated_endpoints(self) -> Dict[str, Any]:
        """
        Additional checks for authenticated endpoints
        """
        auth_results = {
            'authenticated_endpoints': {},
            'permissions': {},
            'features': {}
        }

        auth_endpoints = [
            '/users/@me',
            '/users/@me/guilds',
            '/users/@me/connections'
        ]

        for endpoint in auth_endpoints:
            try:
                url = f"{self.BASE_URL}{endpoint}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=self._get_headers()) as response:
                        if response.status == 200:
                            data = await response.json()
                            auth_results['authenticated_endpoints'][endpoint] = data
            except Exception as e:
                self.logger.error(f"Error checking authenticated endpoint {endpoint}: {str(e)}")

        return auth_results 