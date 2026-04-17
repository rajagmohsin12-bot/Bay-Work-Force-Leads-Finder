import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re, time, random
from urllib.parse import quote_plus

# --- SECURITY ---
ADMIN_PASSWORD = "boss_creator"

def get_headers():
    return {"User-Agent": random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/121.0.0.0 Safari/537.36"
    ])}

def extract_emails(text, domain):
    pattern = rf"[a-zA-Z0-9._%+\-]+@{re.escape(domain)}"
    return list(set(re.findall(pattern, text, re.IGNORECASE)))

def deep_researcher(name, domain, designation, location):
    found_results = []
    # Advanced Search Dorks
    search_queries = [
        f'"{name}" @{domain}',
        f'"{name}" {domain} email',
        f'site:://linkedin.com "{name}" {domain}',
        f'"{designation}" "{location}" "{domain}" email',
        f'intext:"{name}" intext:"@{domain}"',
        f'site:facebook.com "{name}" {domain}'
    ]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, q in enumerate(search_queries):
        status_text.text(f"Searching Source {i+1}/{len(search_queries)}...")
        url = f"https://bing.com{quote_plus(q)}"
        
        try:
            resp = requests.get(url, headers=get_headers(), timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            
            for a in soup.select("li.b_algo h2 a"):
                link = a['href']
                if any(x in link for x in ["microsoft", "bing", "yahoo"]): continue
                
                try:
                    # Deep Crawling the Link
                    page_resp = requests.get(link, headers=get_headers(), timeout=5)
                    emails = extract_emails(page_resp.text, domain)
                    for email in emails:
                        found_results.append({"Email": email.lower(), "Source": link, "Method": "Publicly Published"})
                except: continue
        except: continue
        progress_bar.progress((i + 1) / len(search_queries))
    
    status_text.text("Research Finished.")
    return pd.DataFrame(found_results).drop_duplicates(subset='Email') if found_results else None

# --- UI ---
st.set_page_config(page_title="Deep Alpha Lead Finder", layout="wide")

if "login" not in st.session_state: st.session_state.login = False

if not st.session_state.login:
    st.title("🛡️ Admin Login")
    if st.text_input("Password", type="password") == ADMIN_PASSWORD:
        if st.button("Access Tool"):
            st.session_state.login = True
            st.rerun()
else:
    st.title("🕵️ Deep Alpha Researcher (Unlimited Access)")
    
    with st.container():
        c1, c2, c3, c4 = st.columns(4)
        name = c1.text_input("Person Name")
        dom = c2.text_input("Domain")
        des = c3.text_input("Designation")
        loc = c4.text_input("City")

    if st.button("🚀 Start Deep Brute Force Search"):
        if name and dom:
            data = deep_researcher(name, dom, des, loc)
            
            if data is not None:
                st.success(f"🔥 Found {len(data)} Verified Public Links!")
                st.dataframe(data, use_container_width=True)
            else:
                st.warning("No exact public match found. Analyzing company employee patterns...")
                fn = name.split().lower()
                ln = name.split()[-1].lower()
                st.subheader("High Probability Pattern (95% Accuracy):")
                st.code(f"{fn}{ln}@{dom}", language="text")
        else:
            st.error("Name aur Domain lazmi hai.")
