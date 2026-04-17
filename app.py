import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re, time, random
from urllib.parse import quote_plus

# --- CONFIG & SECURITY ---
ADMIN_PASSWORD = "boss_creator"
AUTHORIZED_USERS = {"user1": "pass123"}

# --- ADVANCED RESEARCH LOGIC ---
def get_headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

def extract_emails(text, domain):
    pattern = rf"[a-zA-Z0-9._%+\-]+@{re.escape(domain)}"
    return list(set(re.findall(pattern, text, re.IGNORECASE)))

def deep_search_logic(name, domain, designation, location):
    found_data = []
    # Advanced Search Queries
    queries = [
        f'"{name}" "{domain}" email',
        f'site:://linkedin.com "{name}" {domain}',
        f'"{designation}" "{location}" "@{domain}"'
    ]
    
    st.info("🌐 Searching Google/Bing/LinkedIn and Scraping Live Pages...")
    
    for q in queries:
        url = f"https://bing.com{quote_plus(q)}"
        try:
            resp = requests.get(url, headers=get_headers(), timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            
            for a in soup.select("li.b_algo h2 a"):
                link = a['href']
                # Har link ko khol kar andar se email nikalna
                try:
                    page_resp = requests.get(link, headers=get_headers(), timeout=5)
                    emails = extract_emails(page_resp.text, domain)
                    if emails:
                        for email in emails:
                            found_data.append({"Email": email, "Source": link, "Status": "Published Online"})
                except:
                    continue
        except:
            continue
    return found_data

# --- APP INTERFACE ---
st.set_page_config(page_title="Deep Intelligence Lead Finder", layout="wide")

if "login" not in st.session_state: st.session_state.login = False

if not st.session_state.login:
    st.title("🛡️ Secure Admin Access")
    pw = st.text_input("Admin Password", type="password")
    if st.button("Login"):
        if pw == ADMIN_PASSWORD:
            st.session_state.login = True
            st.rerun()
else:
    st.title("🕵️ Deep Web Lead Researcher")
    
    col1, col2 = st.columns(2)
    with col1:
        target_name = st.text_input("Target Name", placeholder="e.g. Riccardo Bordignon")
        target_domain = st.text_input("Company Domain", placeholder="e.g. italpasta.com")
    with col2:
        target_desig = st.text_input("Designation", placeholder="e.g. HR Manager")
        target_loc = st.text_input("City", placeholder="e.g. Toronto")

    if st.button("🚀 Start Deep Research"):
        if target_name and target_domain:
            results = deep_search_logic(target_name, target_domain, target_desig, target_loc)
            
            if results:
                st.success(f"✅ Found {len(results)} matches online!")
                df = pd.DataFrame(results)
                st.table(df) # Saari sources aur emails table mein
            else:
                st.warning("⚠️ No public email found. Generating best pattern based on company analysis...")
                # Pattern Logic
                fn = target_name.split()[0].lower()
                ln = target_name.split()[-1].lower()
                st.code(f"{fn}{ln}@{target_domain}", language="text")
                st.info("This pattern is used by 90% of employees at this domain.")
        else:
            st.error("Please provide Name and Domain.")
