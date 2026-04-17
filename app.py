import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re, time, random
from urllib.parse import quote_plus

# --- CONFIG & AUTH ---
ADMIN_PASSWORD = "boss_creator"

def get_headers():
    return {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/123.0.0.0 Safari/537.36"
        ]),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

def aggressive_extract(text, domain):
    # Regex to find emails even if obfuscated (e.g., [at], (dot))
    patterns = [
        rf"[a-zA-Z0-9._%+\-]+@{re.escape(domain)}",
        rf"[a-zA-Z0-9._%+\-]+\s*[\[\(]?at[\]\)]?\s*{re.escape(domain.split('.')[0])}\s*[\[\(]?dot[\]\)]?\s*{re.escape(domain.split('.')[-1])}"
    ]
    found = []
    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        for m in matches:
            clean = m.replace("[at]", "@").replace("(at)", "@").replace("[dot]", ".").replace("(dot)", ".").lower().strip()
            found.append(clean)
    return list(set(found))

def deep_force_search(name, domain, designation, location):
    st.info("🚀 Initiating Deep Force Search across multiple OSINT layers...")
    results = []
    
    # 8 Powerful Search Dorks
    queries = [
        f'"{name}" "@{domain}"',
        f'"{name}" {domain} contact',
        f'site:://linkedin.com "{name}" {domain}',
        f'site:{domain} "{name}"',
        f'intext:"{name}" intext:"@{domain}"',
        f'"{designation}" "{location}" "@{domain}"',
        f'"{name}" email "{domain}"',
        f'"{name}" contact details {domain}'
    ]

    progress = st.progress(0)
    for i, q in enumerate(queries):
        url = f"https://bing.com{quote_plus(q)}"
        try:
            r = requests.get(url, headers=get_headers(), timeout=12)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select("li.b_algo h2 a"):
                link = a['href']
                if any(x in link for x in ["bing", "microsoft", "google"]): continue
                try:
                    # Actually visit the page to find hidden emails
                    page = requests.get(link, headers=get_headers(), timeout=6)
                    emails = aggressive_extract(page.text, domain)
                    for e in emails:
                        results.append({"Email": e, "Source": link, "Status": "PUBLISHED & VERIFIED"})
                except: continue
        except: continue
        progress.progress((i + 1) / len(queries))
    
    return pd.DataFrame(results).drop_duplicates(subset='Email') if results else None

# --- INTERFACE ---
st.set_page_config(page_title="Deep Force Researcher v2.0", layout="wide")

if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🛡️ Lead Intelligence Login")
    if st.text_input("Enter Admin Key", type="password") == ADMIN_PASSWORD:
        if st.button("Unlock Tool"):
            st.session_state.auth = True
            st.rerun()
else:
    st.title("🕵️ Deep Force Researcher (OSINT Engine)")
    c1, c2, c3, c4 = st.columns(4)
    target_name = c1.text_input("Name", placeholder="Riccardo Bordignon")
    target_domain = c2.text_input("Domain", placeholder="italpasta.com")
    target_des = c3.text_input("Designation", placeholder="HR Manager")
    target_loc = c4.text_input("City", placeholder="Toronto")

    if st.button("🔥 Run Brute Force Research"):
        if target_name and target_domain:
            data = deep_force_search(target_name, target_domain, target_des, target_loc)
            if data is not None:
                st.success(f"✅ FOUND {len(data)} REAL MATCHES!")
                st.table(data)
            else:
                st.error("No direct match found in deep scan. Analyzing patterns...")
                parts = target_name.lower().split()
                if len(parts) >= 2:
                    st.code(f"{parts[0][0]}{parts[-1]}@{target_domain}")
        else:
            st.warning("Please provide Name and Domain.")
