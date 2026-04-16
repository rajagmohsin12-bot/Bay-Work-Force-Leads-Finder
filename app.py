import streamlit as st
import os
import random
import re
import smtplib
import socket
import time
from collections import Counter
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

# --- CONSTANTS & CONFIG ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

SEARCH_URLS = {
    "bing": "https://bing.com{query}&count=10",
    "duckduckgo": "https://duckduckgo.com{query}",
}

EMAIL_PATTERNS = {
    "first.last": lambda f, l: f"{f}.{l}",
    "flast": lambda f, l: f"{f[0]}{l}",
    "firstl": lambda f, l: f"{f}{l[0]}",
    "first": lambda f, l: f"{f}",
    "last": lambda f, l: f"{l}",
    "last.first": lambda f, l: f"{l}.{f}",
    "f.last": lambda f, l: f"{f[0]}.{l}",
    "first_last": lambda f, l: f"{f}_{l}",
    "firstlast": lambda f, l: f"{f}{l}",
}

GENERIC_LOCALS = {"info", "sales", "contact", "hello", "support", "admin", "hr"}

# --- HELPER FUNCTIONS ---
def sanitize_name(name):
    parts = name.strip().split()
    if len(parts) < 2: return None, None
    first = re.sub(r"[^a-zA-Z]", "", parts[0]).lower()
    last = re.sub(r"[^a-zA-Z]", "", parts[-1]).lower()
    return first, last

def normalize_domain(domain):
    domain = domain.strip().lower()
    domain = re.sub(r"^https?://", "", domain)
    domain = re.sub(r"^www\.", "", domain)
    return domain.split("/")[0].strip()

def extract_emails_from_text(text, domain):
    pattern = rf"[a-zA-Z0-9._%+\-]+@{re.escape(domain)}"
    found = re.findall(pattern, text, re.IGNORECASE)
    return sorted(set([e.lower().strip().rstrip(".,;>") for e in found]))

def fetch_page(url):
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        resp = requests.get(url, headers=headers, timeout=8)
        return resp.text if resp.status_code == 200 else ""
    except: return ""

def search_engine_query(engine, query):
    encoded = quote_plus(query)
    html = fetch_page(SEARCH_URLS[engine].format(query=encoded))
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = []
    selector = "li.b_algo h2 a[href]" if engine == "bing" else "a.result__url[href]"
    for a in soup.select(selector):
        href = a.get("href", "")
        if href.startswith("http"): links.append(href)
    return links[:5]

def get_mx_host(domain):
    try:
        import dns.resolver
        mx = dns.resolver.resolve(domain, "MX")
        return str(sorted(mx, key=lambda r: r.preference)[0].exchange).rstrip(".")
    except: return None

def smtp_check(email, domain):
    mx = get_mx_host(domain)
    if not mx: return {"status": "UNKNOWN", "detail": "No MX host"}
    try:
        s = smtplib.SMTP(timeout=5)
        s.connect(mx, 25)
        s.helo()
        s.mail('verify@example.com')
        code, msg = s.rcpt(email)
        s.quit()
        if code == 250: return {"status": "DELIVERABLE", "detail": "Accepted"}
        return {"status": "UNDELIVERABLE", "detail": "Rejected"}
    except Exception as e: return {"status": "UNKNOWN", "detail": str(e)}

# --- APP INTERFACE ---
st.set_page_config(page_title="Pro Lead Finder", page_icon="🎯")

if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔐 Secure Login")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if pwd == "boss": # Password yahan change karein
            st.session_state.auth = True
            st.rerun()
else:
    st.title("🎯 Pro Lead Finder & Researcher")
    
    name_in = st.text_input("Person Name", placeholder="Riccardo Bordignon")
    domain_in = st.text_input("Company Domain", placeholder="italpasta.com")
    smtp_on = st.checkbox("Enable SMTP Deep Verification (Slower)")

    if st.button("Find & Verify Lead"):
        if name_in and domain_in:
            first, last = sanitize_name(name_in)
            domain = normalize_domain(domain_in)
            
            with st.spinner("🔍 Researching company patterns and verifying emails..."):
                # 1. Search Logic
                found_emails = []
                links = search_engine_query("bing", f'"@{domain}"')
                for l in links:
                    found_emails.extend(extract_emails_from_text(fetch_page(l), domain))
                
                # 2. Pattern Analysis
                st.subheader("Results")
                best_guess = f"{first[0]}{last}@{domain}" # Default flast
                
                st.write(f"### Predicted Email: `{best_guess}`")
                
                if smtp_on:
                    res = smtp_check(best_guess, domain)
                    st.info(f"SMTP Status: {res['status']} ({res['detail']})")
                
                if found_emails:
                    with st.expander("Other Emails Found Online"):
                        for e in set(found_emails): st.write(e)
        else:
            st.error("Please enter both Name and Domain.")
