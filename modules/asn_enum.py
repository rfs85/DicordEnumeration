from typing import Dict, Any
import aiohttp
from ipwhois import IPWhois
import socket
from .base import BaseEnumerator

class ASNEnumerator(BaseEnumerator):
    DISCORD_DOMAINS = [
        'discord.com',
        'discordapp.com',
        'discord.gg',
        'cdn.discordapp.com',
        'media.discordapp.net'
    ]

    async def enumerate(self) -> Dict[str, Any]:
        results = {
            'asn_info': [],
            'ip_ranges': [],
            'organization_info': {}
        }

        for domain in self.DISCORD_DOMAINS:
            try:
                # Get IP address for the domain
                ip_address = socket.gethostbyname(domain)
                
                # Get ASN information
                whois = IPWhois(ip_address)
                asn_info = whois.lookup_rdap()
                
                asn_data = {
                    'domain': domain,
                    'ip_address': ip_address,
                    'asn': asn_info.get('asn'),
                    'asn_description': asn_info.get('asn_description'),
                    'network': asn_info.get('network', {}).get('cidr')
                }
                
                results['asn_info'].append(asn_data)
                
                # Add IP ranges if not already present
                for network in asn_info.get('network', {}).get('cidr', []):
                    if network not in results['ip_ranges']:
                        results['ip_ranges'].append(network)
                
                # Add organization info if not already present
                org_info = asn_info.get('network', {}).get('name')
                if org_info:
                    results['organization_info'][asn_info['asn']] = org_info
                
            except Exception as e:
                self.logger.error(f"Error enumerating ASN for {domain}: {str(e)}")
                continue

        return results

    async def _get_ip_ranges(self, asn: str) -> list:
        """
        Get IP ranges for a specific ASN
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.bgpview.io/asn/{asn}/prefixes") as response:
                if response.status == 200:
                    data = await response.json()
                    return [prefix['prefix'] for prefix in data.get('data', {}).get('ipv4_prefixes', [])] 