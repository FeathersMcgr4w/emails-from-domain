#!/usr/bin/env python3

import requests
import re
import time
import random
import signal
import sys
import os
from pwn import *

def exit_handler(sig, frame):
    print("\n\n[!] Exiting...\n")
    sys.exit(1)

# ctrl+c (Interrupt)
signal.signal(signal.SIGINT, exit_handler)

# banner
def banner():
    print(r"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~  ____  _               ____             _                     ~
~ / ___|| |__   ___ _ __|  _ \  ___  _ __| | __                 ~
~ \___ \| '_ \ / _ \ '__| | | |/ _ \| '__| |/ /     /\   /\     ~
~  ___) | | | |  __/ |  | |_| | (_) | |  |   <     /  \ /  \    ~
~ |____/|_| |_|\___|_|  |____/ \___/|_|  |_|\_\   /    .    \   ~
~ | | | | ___ | |_ __ ___   ___  ___             /___________\  ~
~ | |_| |/ _ \| | '_ ` _ \ / _ \/ __|           --------------- ~
~ |  _  | (_) | | | | | | |  __/\__ \               _     _     ~
~ |_| |_|\___/|_|_| |_| |_|\___||___/            '-(_)---(_)-'  ~
~                                                               ~
~ Author: FeathersMcgr4w                                        ~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """)

if len(sys.argv) != 2:
    banner()
    log.failure("Use: python3 %s your-domain.com" % sys.argv[0])
    sys.exit(1)

# verify valid domain (argument)
domain = sys.argv[1]
domain_pattern = re.compile(
    r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.[A-Za-z]{2,6}(\.[A-Za-z]{2,6})?$'
)

if not domain_pattern.match(domain):
    log.failure(f"The argument entered '{domain}' does not appear to be a valid domain.")
    log.failure("Use: python3 %s your-domain.com" % sys.argv[0])
    sys.exit(1)

# random time
def random_delay():
    return round(random.uniform(2, 5))

# keywords for search
keywords = ["email", "contacto", "correo electrónico", "linkedin"]

# load credentials
def load_credentials(filepath):
    credentials = {}
    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and ":" in line:
                    key, value = line.split(":", 1)
                    credentials[key.strip()] = value.strip()
    except FileNotFoundError:
        log.failure(f"Credentials file not found at: {filepath}")
        sys.exit(1)
    return credentials

credentials_path = os.path.join(os.path.dirname(__file__), "../credentials/your_api_credentials.txt")
creds = load_credentials(credentials_path)

# Google Custom Search API configuration
API_KEY = creds.get("googleApi")
SEARCH_ENGINE_ID = creds.get("googleId")
base_url = "https://www.googleapis.com/customsearch/v1"

if not API_KEY or not SEARCH_ENGINE_ID:
    log.failure("Missing 'googleApi' or 'googleId' in credentials file.")
    sys.exit(1)

filtered_results = set()  # filter duplicate results
pages = 5  # pages to query (10 results per page)

log.info(f"Starting research for related emails to: {domain}")

for keyword in keywords:
    query = f'"{keyword}" "@{domain}"'
    log.info(f"Searching: {query}")

    for page in range(pages):
        start = 1 + (page * 10)

        params = {
            "key": API_KEY,
            "cx": SEARCH_ENGINE_ID,
            "q": query,
            "num": 10,
            "start": start
        }

        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])

            for item in items:
                snippet = item.get("snippet", "")

                # Regex simple: ejemplo@dominio.com
                regex_simple = fr'[\w\.\-]+@{re.escape(domain)}'
                matches_simple = re.findall(regex_simple, snippet)
                filtered_results.update(matches_simple)

                # Regex nested: ejemplo@algo.dominio.com
                regex_nested = fr'[\w\.\-]+@[\w\.\-]+\.{re.escape(domain)}'
                matches_nested = re.findall(regex_nested, snippet)
                filtered_results.update(matches_nested)

        elif response.status_code == 429:
            log.failure("Error 429: Too Many Requests.")
            log.failure("API quota may have been exceeded. Free plan allows 100 requests per day.")
            sys.exit(1)

        else:
            log.failure(f"Error in API request: {response.status_code}")
            continue

        delay = random_delay()
        log.info(f"[Page {page+1}/5] Gathering information, please wait...")
        time.sleep(delay)

# save results
output_file = "emails_employees.txt"
with open(output_file, "a") as file:
    for result in sorted(filtered_results):
        file.write(result + "\n")

log.success(f"{len(filtered_results)} emails found.")
log.info(f"Results saved in 'your_domain.com/emails/{output_file}'. Blessed Hacking!")
