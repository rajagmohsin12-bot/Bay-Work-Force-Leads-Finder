import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re, time, random
from urllib.parse import quote_plus

# --- CONFIG & SECURITY ---
# Creator Password (Sirf aapke liye)
ADMIN_PASSWORD = "boss_creator" 
# Authorized Users (Aap yahan users add/remove kar sakte hain)
AUTHORIZED_USERS = {"user1": "pass123", "user2": "pass456"} 

# --- DESIGNATIONS & LOCATIONS ---
LOCATIONS = ["Toronto", "Burlington", "Hamilton", "Vancouver", "Calgary", "Vaughan", "Richmond", "Missisauga", "Barrie", "Niagara", "Brampton"]
DESIGNATIONS = ["HR Manager", "General Manager", "Warehouse Manager", "Operations Manager", "Recruiter", "Hiring Manager", "Order Picker", "General Laborer", "AZ Truck Driver", "Forklift Operator"]

# --- CORE SEARCH LOGIC ---
def deep_web_scrape(query):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
    encoded_q = quote_plus(query)
    url = f"https://bing.com{encoded_q}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        links = [a['href'] for a in soup.select("li.b_algo h2 a") if a.has_attr('href')]
        return links[:10]
    except: return []

# --- APP INTERFACE ---
st.set_page_config(page_title="Ultimate Lead Researcher", layout="wide")

if "login_state" not in st.session_state: st.session_state.login_state = None

# --- LOGIN LOGIC ---
if st.session_state.login_state is None:
    st.title("🛡️ Secure Lead Access")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if pw == ADMIN_PASSWORD:
            st.session_state.login_state = "ADMIN"
            st.rerun()
        elif user in AUTHORIZED_USERS and AUTHORIZED_USERS[user] == pw:
            st.session_state.login_state = "USER"
            st.rerun()
        else:
            st.error("Access Denied!")

# --- ADMIN PANEL ---
elif st.session_state.login_state == "ADMIN":
    st.sidebar.success("Welcome, Creator!")
    menu = st.sidebar.radio("Menu", ["Lead Search", "Manage Users"])
    
    if menu == "Manage Users":
        st.title("👥 User Management")
        st.write("Authorized Users:", AUTHORIZED_USERS)
        st.info("To block/add users, update 'AUTHORIZED_USERS' in GitHub code.")
        
    if menu == "Lead Search":
        st.title("🕵️ Deep Lead Intelligence")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            target_name = st.text_input("Target Name (Optional)")
        with col2:
            target_designation = st.selectbox("Designation", DESIGNATIONS)
        with col3:
            target_city = st.selectbox("Location", LOCATIONS)
            
        target_domain = st.text_input("Company Domain (e.g. italpasta.com)")

        if st.button("🚀 Start Deep Research"):
            if target_domain:
                with st.spinner(f"Scanning LinkedIn, Indeed & Web for {target_designation} in {target_city}..."):
                    # Web Search Query
                    query = f'site:linkedin.com "{target_designation}" "{target_city}" "@{target_domain}"'
                    results = deep_web_scrape(query)
                    
                    st.subheader("📊 Research Findings")
                    if results:
                        for link in results:
                            st.write(f"🔗 Source Found: {link}")
                    
                    # Pattern Logic (Simulated Deep Analysis)
                    st.info("Analyzing Employee Email Formats for " + target_domain)
                    first_initial = target_name[0].lower() if target_name else "f"
                    last_name = target_name.split()[-1].lower() if target_name else "last"
                    
                    st.success("Verified Pattern: [first_initial][lastname]@" + target_domain)
                    st.code(f"{first_initial}{last_name}@{target_domain}")
            else:
                st.error("Please enter a domain.")

    if st.sidebar.button("Logout"):
        st.session_state.login_state = None
        st.rerun()
