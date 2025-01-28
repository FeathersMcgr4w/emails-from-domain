#!/bin/python3

import requests
import re
import time
import random
import signal
import sys
from pwn import *

def exit_handler(sig, frame):
    print("\n\n[!] Exiting...\n")
    sys.exit(1)

# Ctrl+C
signal.signal(signal.SIGINT, exit_handler)

if len(sys.argv) != 2:
    log.failure("Use: %s your-domain.com" % sys.argv[0])
    sys.exit(1)

# Validate that the argument is a valid domain
domain = sys.argv[1]
domain_pattern = re.compile(
    r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.[A-Za-z]{2,6}(\.[A-Za-z]{2,6})?$'
)

if not domain_pattern.match(domain):
    log.failure(f"The argument entered '{domain}' does not appear to be a valid domain.")
    log.failure("Use: %s your-domain.com" % sys.argv[0])
    sys.exit(1)

# Random time
def random_delay():
    x = random.uniform(2, 5)
    return round(x)

# Key words for search
keywords = ["email", "contacto", "correo electrónico", "linkedin"]

# Google Custom Search API configuration
API_KEY = ""
SEARCH_ENGINE_ID = ""
base_url = "https://www.googleapis.com/customsearch/v1"

filtered_results = []

for keyword in keywords:  # Iterate over keywords
    query = f'"{keyword}" "@{domain}"'  # Dynamic query

    # Request to Google API
    params = {
        "key": API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": query,
        "num": 20 # results per page
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])

        for item in items:
            snippet = item.get("snippet", "")

            # Filter emails by regex: example@domain.com.ar
            regex_simple = fr'[\w\.\-]+@{re.escape(domain)}'
            matches_simple = re.findall(regex_simple, snippet)
            filtered_results.extend(matches_simple)

            # Filter emails by regex: example@example.domain.com.ar
            regex_nested = fr'[\w\.\-]+@[\w\.\-]+\.{re.escape(domain)}'
            matches_nested = re.findall(regex_nested, snippet)
            filtered_results.extend(matches_nested)

    else:
        log.failure(f"Error in API request: {response.status_code}")

    # Generate a random delay before the next request
    delay = random_delay()
    print("[*] Wait, looking for emails...")

    time.sleep(delay)

# Save results in a txt file
output_file = "emails_employees.txt"
with open(output_file, "a") as file:
    for result in filtered_results:
        file.write(result + "\n")

print("\n\n[*] Results saved in '{output_file}'. Bye!")
