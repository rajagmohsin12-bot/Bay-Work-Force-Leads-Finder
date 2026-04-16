import streamlit as st

# Purana simple password
PASSWORD = "boss"

st.set_page_config(page_title="Old Lead Finder", page_icon="🔍")

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Login")
    pwd = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if pwd == PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Invalid Password")
else:
    st.title("🔍 Simple Lead Finder (Old Version)")
    name = st.text_input("Person Name")
    domain = st.text_input("Domain")
    if st.button("Find Email"):
        st.write(f"Searching for {name} at {domain}...")
        st.code(f"{name.split()[0].lower()}{name.split()[-1].lower()}@{domain}")
