from typing import Dict, Any
import dns.resolver
import dns.zone
import dns.query
from dns.exception import DNSException
from .base import BaseEnumerator

class DNSEnumerator(BaseEnumerator):
    DISCORD_DOMAINS = [
        'discord.com',
        'discordapp.com',
        'discord.gg',
        'discord.media'
    ]

    RECORD_TYPES = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']

    async def enumerate(self) -> Dict[str, Any]:
        results = {
            'dns_records': {},
            'nameservers': {},
            'subdomains': {},
            'security_records': {}
        }

        for domain in self.DISCORD_DOMAINS:
            domain_results = {
                'records': {},
                'security': {}
            }

            # Enumerate DNS records
            for record_type in self.RECORD_TYPES:
                try:
                    answers = dns.resolver.resolve(domain, record_type)
                    domain_results['records'][record_type] = [str(rdata) for rdata in answers]
                except DNSException as e:
                    self.logger.debug(f"No {record_type} records found for {domain}: {str(e)}")
                    continue

            # Get nameservers
            try:
                ns_records = dns.resolver.resolve(domain, 'NS')
                results['nameservers'][domain] = [str(ns) for ns in ns_records]
            except DNSException as e:
                self.logger.error(f"Error getting nameservers for {domain}: {str(e)}")

            # Check for security records (SPF, DMARC, DKIM)
            try:
                # SPF
                spf_records = dns.resolver.resolve(domain, 'TXT')
                domain_results['security']['spf'] = [str(r) for r in spf_records if 'spf' in str(r).lower()]
                
                # DMARC
                dmarc_records = dns.resolver.resolve(f'_dmarc.{domain}', 'TXT')
                domain_results['security']['dmarc'] = [str(r) for r in dmarc_records]
            except DNSException:
                pass

            # Try zone transfer (usually blocked, but worth trying)
            try:
                nameservers = dns.resolver.resolve(domain, 'NS')
                for ns in nameservers:
                    try:
                        zone = dns.zone.from_xfr(dns.query.xfr(str(ns), domain))
                        domain_results['zone_transfer'] = [str(name) for name in zone.nodes.keys()]
                    except:
                        continue
            except DNSException:
                pass

            # Common subdomain enumeration
            common_subdomains = ['api', 'cdn', 'media', 'gateway', 'status', 'support', 
                               'developer', 'developers', 'canary', 'ptb', 'staging']
            found_subdomains = []
            
            for subdomain in common_subdomains:
                try:
                    full_domain = f'{subdomain}.{domain}'
                    answers = dns.resolver.resolve(full_domain, 'A')
                    found_subdomains.append({
                        'subdomain': full_domain,
                        'ip': [str(rdata) for rdata in answers]
                    })
                except DNSException:
                    continue

            results['subdomains'][domain] = found_subdomains
            results['dns_records'][domain] = domain_results

        return results 