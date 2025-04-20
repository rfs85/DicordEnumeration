# Discord Infrastructure Enumerator

A modular Python application for enumerating Discord infrastructure for bug bounty purposes.

## Features

- ASN Enumeration
- DNS Server Enumeration
- Subnet Discovery
- Discord Services Discovery
- Discord Server Enumeration
  - Public Server Discovery
  - Guild Information Gathering
  - Role and Permission Analysis
  - Channel Structure Mapping
  - Member Statistics
- Discord CDN Fuzzing
- Supports both authenticated and unauthenticated enumeration
- Performance Optimizations
  - Parallel Request Processing
  - Rate Limiting Protection
  - Automatic Retries
  - Progress Tracking

## Installation

1. Clone the repository:
```bash
git clone https://github.com/rfs85/discord-enumerator.git
cd discord-enumerator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main script with desired options:

```bash
python discord_enum.py [-h] [--token TOKEN] [--mode {auth,unauth}] 
                      [--module {all,asn,dns,subnet,services,servers,cdn}]
                      [--threads THREADS] [--delay DELAY] [--output OUTPUT]
```

### Arguments:

- `--token`: Discord authentication token (optional)
- `--mode`: Enumeration mode (auth/unauth)
- `--module`: Specific module to run (default: all)
- `--threads`: Number of threads for parallel processing (default: 10)
- `--delay`: Delay between requests in seconds (default: 0.5)
- `--output`: Output file for results (default: discord_enum_results.json)

### Examples:

1. Run all modules without authentication:
```bash
python discord_enum.py --mode unauth
```

2. Run specific module with authentication:
```bash
python discord_enum.py --mode auth --token YOUR_TOKEN --module servers
```

3. Run with custom performance settings:
```bash
python discord_enum.py --threads 20 --delay 0.2
```

## Module Details

### Server Enumeration
- Discovers public Discord servers across various categories
- Maps server structure and hierarchy
- Analyzes roles and permissions
- Gathers member statistics
- Identifies server features and settings
- Extracts invite links (when authorized)

### ASN Enumeration
- Maps Discord's ASN information
- Identifies IP ranges
- Discovers organization details

### DNS Enumeration
- Enumerates DNS records
- Discovers subdomains
- Checks security records (SPF, DMARC)
- Attempts zone transfers

### Services Enumeration
- Maps Discord API endpoints
- Tests service availability
- Monitors rate limits
- Supports authenticated enumeration

### CDN Fuzzing
- Tests CDN endpoints
- Fuzzes paths for vulnerabilities
- Extracts metadata
- Tests various image formats and sizes

## Performance Features

- **Parallel Processing**: Utilizes asyncio for concurrent operations
- **Rate Limiting**: Smart rate limit handling with automatic backoff
- **Progress Tracking**: Real-time progress bars and execution timing
- **Resource Management**: Efficient session and connection handling
- **Error Handling**: Robust error recovery with automatic retries

## Security Notice

This tool is intended for educational and bug bounty purposes only. Always ensure you have proper authorization before performing any security testing.

## Disclaimer

This tool is for educational purposes only. Users are responsible for complying with applicable laws and Discord's terms of service.