import streamlit as st
from serpapi import GoogleSearch
import re

# --- CONFIG ---
SERP_API_KEY = "25c6b3cd22779a3bdacb0a7f4c899db1252f1dbd7f44cfd9714d382352b0991e"
ADMIN_PASSWORD = "boss_creator"

def find_verified_emails(name, domain):
    # Asali Google Dorking jo published emails nikaalti hai
    queries = [
        f'"{name}" @{domain}',
        f'"{name}" email "{domain}"',
        f'site:://linkedin.com "{name}" "{domain}"'
    ]
    found_emails = []
    
    for q in queries:
        try:
            search = GoogleSearch({
                "q": q,
                "api_key": SERP_API_KEY,
                "engine": "google"
            })
            result = search.get_dict()
            
            if "organic_results" in result:
                for res in result["organic_results"]:
                    # Snippet aur Title dono scan karna
                    text = res.get("snippet", "") + " " + res.get("title", "")
                    emails = re.findall(rf"[a-zA-Z0-9._%+-]+@{re.escape(domain)}", text, re.IGNORECASE)
                    found_emails.extend(emails)
        except Exception as e:
            st.error(f"Search Error: {e}")
                
    return list(set(found_emails))

# --- UI ---
st.set_page_config(page_title="Ultra Lead Finder", page_icon="🚀")
st.title("🚀 Ultra Verified Lead Finder")

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pw = st.text_input("Admin Password", type="password")
    if st.button("Unlock"):
        if pw == ADMIN_PASSWORD:
            st.session_state.auth = True
            st.rerun()
else:
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"auth": False}))
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Person Name", placeholder="e.g. Riccardo Bordignon")
    with col2:
        domain = st.text_input("Domain", placeholder="e.g. italpasta.com")
    
    if st.button("Deep Search"):
        if name and domain:
            with st.spinner("Google se verified data nikaal raha hoon..."):
                results = find_verified_emails(name, domain)
                if results:
                    st.success(f"✅ Found {len(results)} Published Email(s):")
                    for e in results:
                        st.code(e)
                else:
                    st.error("Google par koi published email nahi mili.")
                    st.info("Tip: Iska matlab hai ye email publicly internet par majood nahi hai.")
        else:
            st.warning("Naam aur Domain likhein.")
