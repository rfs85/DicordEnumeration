#!/usr/bin/env python3
import asyncio
import argparse
import logging
import json
from typing import Dict, Any
from datetime import datetime
from colorama import init, Fore, Style
from concurrent.futures import ThreadPoolExecutor
import time
from tqdm import tqdm

# Import modules
from modules.asn_enum import ASNEnumerator
from modules.dns_enum import DNSEnumerator
from modules.services_enum import ServicesEnumerator
from modules.cdn_fuzzer import CDNFuzzer
from modules.server_enum import ServerEnumerator

# Initialize colorama
init()

class DiscordEnumerator:
    def __init__(self, token: str = None, mode: str = 'unauth'):
        self.token = token
        self.mode = mode
        self.logger = self._setup_logger()
        self.executor = ThreadPoolExecutor(max_workers=10)
        
    def _setup_logger(self) -> logging.Logger:
        """
        Set up logging configuration
        """
        logger = logging.getLogger('DiscordEnumerator')
        logger.setLevel(logging.INFO)
        
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(ch)
        
        return logger
    
    async def enumerate_all(self) -> Dict[str, Any]:
        """
        Run all enumeration modules with improved performance
        """
        results = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'mode': self.mode,
                'authenticated': bool(self.token),
                'execution_time': {}
            },
            'results': {}
        }
        
        # Initialize all enumerators
        enumerators = {
            'asn': ASNEnumerator(self.token),
            'dns': DNSEnumerator(self.token),
            'services': ServicesEnumerator(self.token),
            'cdn': CDNFuzzer(self.token),
            'servers': ServerEnumerator(self.token)
        }
        
        # Create progress bar
        pbar = tqdm(total=len(enumerators), desc="Enumerating modules", unit="module")
        
        # Run enumerators concurrently
        async def run_enumerator(name: str, enumerator: Any):
            start_time = time.time()
            try:
                async with enumerator:  # Use context manager for proper cleanup
                    print(f"\n{Fore.CYAN}[*] Running {name} enumeration...{Style.RESET_ALL}")
                    results['results'][name] = await enumerator.enumerate()
                    execution_time = time.time() - start_time
                    results['metadata']['execution_time'][name] = execution_time
                    print(f"{Fore.GREEN}[+] {name} enumeration completed in {execution_time:.2f}s{Style.RESET_ALL}")
            except Exception as e:
                self.logger.error(f"Error in {name} enumeration: {str(e)}")
                results['results'][name] = {'error': str(e)}
                print(f"{Fore.RED}[-] Error in {name} enumeration: {str(e)}{Style.RESET_ALL}")
            finally:
                pbar.update(1)
        
        # Run all enumerators concurrently
        tasks = [run_enumerator(name, enumerator) for name, enumerator in enumerators.items()]
        await asyncio.gather(*tasks)
        
        pbar.close()
        return results
    
    async def enumerate_module(self, module: str) -> Dict[str, Any]:
        """
        Run a specific enumeration module with improved performance
        """
        results = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'mode': self.mode,
                'authenticated': bool(self.token),
                'module': module,
                'execution_time': 0
            },
            'results': {}
        }
        
        enumerators = {
            'asn': ASNEnumerator,
            'dns': DNSEnumerator,
            'services': ServicesEnumerator,
            'cdn': CDNFuzzer,
            'servers': ServerEnumerator
        }
        
        if module not in enumerators:
            raise ValueError(f"Invalid module: {module}")
        
        start_time = time.time()
        try:
            enumerator = enumerators[module](self.token)
            async with enumerator:  # Use context manager for proper cleanup
                print(f"\n{Fore.CYAN}[*] Running {module} enumeration...{Style.RESET_ALL}")
                results['results'] = await enumerator.enumerate()
                execution_time = time.time() - start_time
                results['metadata']['execution_time'] = execution_time
                print(f"{Fore.GREEN}[+] {module} enumeration completed in {execution_time:.2f}s{Style.RESET_ALL}")
        except Exception as e:
            self.logger.error(f"Error in {module} enumeration: {str(e)}")
            results['results'] = {'error': str(e)}
            print(f"{Fore.RED}[-] Error in {module} enumeration: {str(e)}{Style.RESET_ALL}")
        
        return results

def save_results(results: Dict[str, Any], output_file: str):
    """
    Save results to a JSON file with improved formatting
    """
    class CustomEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, set):
                return list(obj)
            return super().default(obj)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4, cls=CustomEncoder)
    print(f"\n{Fore.GREEN}[+] Results saved to {output_file}{Style.RESET_ALL}")

async def main():
    parser = argparse.ArgumentParser(description='Discord Infrastructure Enumerator')
    parser.add_argument('--token', help='Discord authentication token')
    parser.add_argument('--mode', choices=['auth', 'unauth'], default='unauth',
                      help='Enumeration mode (auth/unauth)')
    parser.add_argument('--module', choices=['all', 'asn', 'dns', 'services', 'cdn', 'servers'],
                      default='all', help='Specific module to run')
    parser.add_argument('--output', default='discord_enum_results.json',
                      help='Output file for results')
    parser.add_argument('--threads', type=int, default=10,
                      help='Number of threads for parallel processing')
    parser.add_argument('--delay', type=float, default=0.5,
                      help='Delay between requests in seconds')
    
    args = parser.parse_args()
    
    print(f"""{Fore.CYAN}
╔══════════════════════════════════════════╗
║     Discord Infrastructure Enumerator    ║
║            Bug Bounty Edition           ║
╚══════════════════════════════════════════╝
{Style.RESET_ALL}""")
    
    # Print configuration
    print(f"{Fore.YELLOW}[*] Configuration:{Style.RESET_ALL}")
    print(f"    Mode: {args.mode}")
    print(f"    Module: {args.module}")
    print(f"    Threads: {args.threads}")
    print(f"    Request Delay: {args.delay}s")
    
    enumerator = DiscordEnumerator(args.token, args.mode)
    
    try:
        start_time = time.time()
        if args.module == 'all':
            results = await enumerator.enumerate_all()
        else:
            results = await enumerator.enumerate_module(args.module)
        
        total_time = time.time() - start_time
        results['metadata']['total_execution_time'] = total_time
        
        save_results(results, args.output)
        print(f"\n{Fore.GREEN}[+] Total execution time: {total_time:.2f}s{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"{Fore.RED}[-] Error: {str(e)}{Style.RESET_ALL}")
        return 1
    
    return 0

if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Enumeration interrupted by user{Style.RESET_ALL}")
        exit(1) 