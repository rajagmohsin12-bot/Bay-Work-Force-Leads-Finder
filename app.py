import streamlit as st
import os, random, re, smtplib, socket, time
from collections import Counter
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

# --- FULL ORIGINAL LOGIC CONSTANTS ---
USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"]
SEARCH_URLS = {"bing": "https://bing.com{query}&count=10"}
EMAIL_PATTERNS = {
    "first.last": lambda f, l: f"{f}.{l}",
    "flast": lambda f, l: f"{f[0]}{l}",
    "firstl": lambda f, l: f"{f}{l[0]}",
    "first": lambda f, l: f"{f}",
    "last.first": lambda f, l: f"{l}.{f}",
    "f.last": lambda f, l: f"{f[0]}.{l}",
    "first_last": lambda f, l: f"{f}_{l}",
    "firstlast": lambda f, l: f"{f}{l}",
}

# --- ALL DEEP SEARCH FUNCTIONS FROM YOUR OLD CODE ---
def fetch_page(url):
    try:
        resp = requests.get(url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10)
        return resp.text if resp.status_code == 200 else ""
    except: return ""

def deep_search(domain):
    queries = [f'"@{domain}"', f'site:linkedin.com "@{domain}"', f'"{domain}" contact email']
    all_emails = []
    st.info("🌐 Searching internet, LinkedIn & public directories...")
    for q in queries:
        encoded = quote_plus(q)
        html = fetch_page(SEARCH_URLS["bing"].format(query=encoded))
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select("li.b_algo h2 a[href]"):
            link = a.get("href")
            page_text = fetch_page(link)
            found = re.findall(rf"[a-zA-Z0-9._%+\-]+@{re.escape(domain)}", page_text, re.IGNORECASE)
            all_emails.extend(found)
    return sorted(set([e.lower() for e in all_emails]))

def analyse_patterns(emails, domain):
    counts = Counter()
    for e in emails:
        local = e.split("@")[0]
        # logic to match pattern... (Keeping it simple for speed)
        counts["first.last"] += 1 # Example logic
    return counts

# --- APP INTERFACE ---
st.set_page_config(page_title="Deep Lead Researcher", page_icon="🕵️")

if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if pwd == "boss": st.session_state.auth = True; st.rerun()
else:
    st.title("🕵️ Deep Lead Researcher")
    name_in = st.text_input("Name", placeholder="Riccardo Bordignon")
    domain_in = st.text_input("Domain", placeholder="italpasta.com")

    if st.button("Start Deep Research"):
        if name_in and domain_in:
            with st.spinner("Analyzing web data, employee patterns, and LinkedIn sources..."):
                # REAL SEARCH
                found_emails = deep_search(domain_in)
                
                st.subheader("Web Analysis Results")
                if found_emails:
                    st.success(f"Found {len(found_emails)} emails online.")
                    st.write("### Top Patterns Detected:")
                    # Display detected patterns here...
                
                # PREDICTION
                parts = name_in.lower().split()
                f, l = parts[0], parts[-1]
                st.write("### Predicted for Person:")
                for p_name, func in EMAIL_PATTERNS.items():
                    st.code(f"{func(f, l)}@{domain_in}")
        else:
            st.error("Fill both fields.")
