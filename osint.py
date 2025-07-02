import json
import os
import time
from pathlib import Path
from typing import Dict, Union, List, Any

from duckduckgo_search import DDGS
import dns.resolver
import whois
import requests

# FIX: Dynamically determine RAW_DIR based on the new BASE_DIR from memory.py
# Assuming memory.py is imported and its BASE_DIR is the source of truth
import memory
RAW_DIR = memory.BASE_DIR / "raw_hits"
RAW_DIR.mkdir(parents=True, exist_ok=True) # Ensure this directory exists

def _save_result_to_file(prefix: str, data: Union[Dict, List, str], extension: str = ".json") -> str:
    """
    Saves data to a file in the RAW_DIR with a timestamp and specified extension.
    Handles both JSON (dict/list) and plain text (str) content.
    """
    ts = int(time.time())
    file_name = f"{prefix}_{ts}{extension}"
    path = RAW_DIR / file_name

    try:
        if extension == ".json":
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        elif extension == ".txt":
            with open(path, 'w', encoding='utf-8') as f:
                f.write(str(data)) # Ensure data is string for text file
        else:
            print(f"Warning: Unsupported file extension '{extension}'. Saving as .json by default.")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            path = RAW_DIR / f"{prefix}_{ts}.json" # Adjust path if defaulted
        
        print(f"Saved {file_name} to {path.parent}")
        return str(path)
    except Exception as e:
        print(f"Error saving file {file_name}: {e}")
        return ""

# Existing _dump_result now calls the more flexible _save_result_to_file
def _dump_result(prefix: str, data: Union[Dict, List]) -> str:
    """Performs OSINT on a given username across various platforms."""
    return _save_result_to_file(prefix, data, extension=".json")


def recon_username(u: str) -> Dict:
    """Performs OSINT on a given username across various platforms."""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(u, max_results=10):
            results.append(r)
    # This will still use _dump_result which defaults to .json
    return {"results": results, "path": _dump_result(f"user_{u}", results)}


def recon_email(e: str) -> Dict:
    """Performs OSINT on a given email address."""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(e, max_results=10):
            results.append(r)
    return {"results": results, "path": _dump_result(f"email_{e}", results)}


def recon_person(name: str, loc: str) -> Dict:
    """Performs OSINT on a person given their their name and location."""
    query = f"\"{name}\" {loc}"
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=10):
            results.append(r)
    return {"results": results, "path": _dump_result(f"person_{name}_{loc}", results)}


def recon_vehicle(vin: str) -> Dict:
    """Performs OSINT on a vehicle given its VIN."""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(vin, max_results=10):
            results.append(r)
    return {"results": results, "path": _dump_result(f"vehicle_{vin}", results)}


def recon_domain(dom: str) -> Dict:
    """Performs OSINT on a domain, including WHOIS and DNS records."""
    try:
        w = whois.whois(dom)
    except Exception:
        w = {}
    dns_records = {}
    try:
        for rtype in ['A', 'MX', 'NS']:
            try:
                dns_records[rtype] = [str(r) for r in dns.resolver.resolve(dom, rtype)]
            except Exception:
                dns_records[rtype] = []
    except Exception:
        dns_records = {}
    data = {"whois": str(w), "dns": dns_records}
    return data | {"path": _dump_result(f"domain_{dom}", data)}


def recon_ip(ip: str) -> Dict:
    """Performs OSINT on an IP address."""
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}")
        info = r.json()
    except Exception:
        info = {}
    return {"info": info, "path": _dump_result(f"ip_{ip}", info)}


def spiderfoot_scan(target: str) -> str:
    """Initiates a SpiderFoot scan and returns the path to the JSON report."""
    # Placeholder stub for SpiderFoot integration.
    # In a real scenario, this would trigger a SpiderFoot scan
    # and then parse/save its JSON report.
    data = {"target": target, "status": "scan_initiated", "report_id": f"SF-{int(time.time())}"}
    return _dump_result(f"spiderfoot_scan_{target}", data)
