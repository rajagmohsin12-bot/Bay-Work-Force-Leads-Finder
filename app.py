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
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.0.0 Safari/537.36",
]

SEARCH_URLS = {
    "bing": "https://www.bing.com/search?q={query}&count=10",
    "duckduckgo": "https://html.duckduckgo.com/html/?q={query}",
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

GENERIC_LOCALS = {
    "info",
    "sales",
    "contact",
    "hello",
    "support",
    "admin",
    "hr",
    "jobs",
    "careers",
    "mail",
    "news",
    "marketing",
    "team",
    "privacy",
    "legal",
    "billing",
    "press",
    "media",
}


def sanitize_name(name):
    parts = name.strip().split()
    if len(parts) < 2:
        raise ValueError("Please enter both a first and last name.")
    first = re.sub(r"[^a-zA-Z]", "", parts[0]).lower()
    last = re.sub(r"[^a-zA-Z]", "", parts[-1]).lower()
    if not first or not last:
        raise ValueError("Name must contain alphabetic characters.")
    return first, last


def normalize_domain(domain):
    domain = domain.strip().lower()
    domain = re.sub(r"^https?://", "", domain)
    domain = re.sub(r"^www\.", "", domain)
    domain = domain.split("/")[0].strip()
    if not re.match(r"^[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}$", domain):
        raise ValueError("Enter a valid company domain, for example italpasta.com.")
    return domain


def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }


def extract_emails_from_text(text, domain):
    pattern_standard = rf"[a-zA-Z0-9._%+\-]+@{re.escape(domain)}"
    parts = domain.split(".")
    pattern_obfuscated = (
        rf"([a-zA-Z0-9._%+\-]+)\s*[\[\(]?\s*at\s*[\]\)]?\s*"
        rf"{re.escape(parts[0])}\s*[\[\(]?\s*dot\s*[\]\)]?\s*{re.escape(parts[-1])}"
    )
    found = re.findall(pattern_standard, text, re.IGNORECASE)
    for match in re.finditer(pattern_obfuscated, text, re.IGNORECASE):
        found.append(f"{match.group(1)}@{domain}")
    cleaned = []
    for email in found:
        email = email.lower().strip().rstrip(".,;>\"')")
        if re.match(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$", email):
            cleaned.append(email)
    return sorted(set(cleaned))


def fetch_page(url, timeout=8):
    try:
        response = requests.get(url, headers=get_random_headers(), timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            return response.text
        return ""
    except requests.RequestException:
        return ""


def search_engine_query(engine, query):
    encoded_query = quote_plus(query)
    html = fetch_page(SEARCH_URLS[engine].format(query=encoded_query))
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    links = []
    if engine == "bing":
        for h2 in soup.select("li.b_algo h2 a[href]"):
            href = h2.get("href", "")
            if href.startswith("http") and "bing.com" not in href:
                links.append(href)
    if engine == "duckduckgo":
        for a in soup.select("a.result__url[href], div.result a[href]"):
            href = a.get("href", "")
            if href.startswith("http") and "duckduckgo.com" not in href:
                links.append(href)
    unique = []
    seen = set()
    for link in links:
        if link not in seen:
            seen.add(link)
            unique.append(link)
    return unique[:8]


def search_for_company_emails(domain):
    company_name = domain.split(".")[0]
    queries = [
        f'"@{domain}"',
        f'site:{domain} email',
        f'"{company_name}" "@{domain}"',
        f'"{domain}" contact email address',
    ]
    all_emails = []
    visited_urls = set()
    sources = []
    engines = list(SEARCH_URLS.keys())
    for index, query in enumerate(queries):
        engine = engines[index % len(engines)]
        for url in search_engine_query(engine, query):
            if url in visited_urls:
                continue
            visited_urls.add(url)
            if any(skip in url for skip in ["youtube.com", "facebook.com", "twitter.com", "instagram.com", "tiktok.com"]):
                continue
            page_text = fetch_page(url)
            if page_text:
                emails = extract_emails_from_text(page_text, domain)
                if emails:
                    all_emails.extend(emails)
                    sources.append({"url": url, "count": len(emails)})
            time.sleep(0.25)
    for path in ["", "/contact", "/about", "/team", "/contact-us", "/about-us"]:
        company_url = f"https://{domain}{path}"
        if company_url in visited_urls:
            continue
        visited_urls.add(company_url)
        page_text = fetch_page(company_url)
        if page_text:
            emails = extract_emails_from_text(page_text, domain)
            if emails:
                all_emails.extend(emails)
                sources.append({"url": company_url, "count": len(emails)})
        time.sleep(0.15)
    return sorted(set(all_emails)), sources[:10]


def match_pattern_to_known(email, domain):
    local = email.replace(f"@{domain}", "").lower()
    if "." in local:
        parts = local.split(".")
        if len(parts) == 2:
            return "f.last" if len(parts[0]) == 1 else "first.last"
        return "first.last"
    if "_" in local:
        return "first_last"
    if len(local) <= 2:
        return None
    if len(local) <= 6:
        return "flast"
    return "firstlast"


def analyse_patterns(emails, domain):
    pattern_counts = Counter()
    for email in emails:
        local = email.split("@")[0].lower()
        if local in GENERIC_LOCALS:
            continue
        pattern = match_pattern_to_known(email, domain)
        if pattern:
            pattern_counts[pattern] += 1
    if not pattern_counts:
        return {}
    total = sum(pattern_counts.values())
    return {pattern: round(count / total * 100, 1) for pattern, count in pattern_counts.most_common()}


def generate_emails(first, last, domain, pattern_probs):
    results = []
    if pattern_probs:
        source = "Found from public company email patterns"
        patterns = pattern_probs.items()
    else:
        source = "Industry default estimate"
        patterns = {
            "first.last": 42.0,
            "flast": 28.0,
            "f.last": 10.0,
            "firstl": 5.0,
            "first": 5.0,
            "last": 3.0,
            "last.first": 3.0,
            "first_last": 2.0,
            "firstlast": 2.0,
        }.items()
    for pattern_name, probability in patterns:
        if pattern_name in EMAIL_PATTERNS:
            email = f"{EMAIL_PATTERNS[pattern_name](first, last)}@{domain}"
            results.append(
                {
                    "email": email,
                    "pattern": pattern_name,
                    "probability": probability,
                    "source": source,
                }
            )
    unique = []
    seen = set()
    for result in results:
        if result["email"] not in seen:
            seen.add(result["email"])
            unique.append(result)
    return unique


def syntax_check(email):
    return bool(re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._%+\-]{0,63}@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email))


def get_mx_host(domain):
    try:
        import dns.resolver

        mx_records = dns.resolver.resolve(domain, "MX")
        return str(sorted(mx_records, key=lambda r: r.preference)[0].exchange).rstrip(".")
    except Exception:
        return None


def check_domain_mail(domain):
    try:
        socket.setdefaulttimeout(5)
        socket.gethostbyname(domain)
    except socket.gaierror:
        return {"mx": False, "detail": "Domain does not resolve."}
    mx_host = get_mx_host(domain)
    if mx_host:
        return {"mx": True, "detail": f"Mail server found: {mx_host}"}
    return {"mx": True, "detail": "Domain resolves, but no MX record was found."}


def smtp_check(email, domain):
    mx_host = get_mx_host(domain)
    if not mx_host:
        return {"status": "UNKNOWN", "detail": "No MX host available for SMTP check."}
    try:
        smtp = smtplib.SMTP(timeout=8)
        smtp.connect(mx_host, 25)
        smtp.helo("email-checker.local")
        smtp.mail("verify@email-checker.local")
        random_test = f"test.{random.randint(10000, 99999)}.missing@{domain}"
        code_test, _ = smtp.rcpt(random_test)
        code_real, msg_real = smtp.rcpt(email)
        smtp.quit()
        if code_test == 250 and code_real == 250:
            return {"status": "CATCH_ALL", "detail": "Server accepts all addresses, so this cannot be confirmed."}
        if code_real == 250:
            return {"status": "DELIVERABLE", "detail": "Mail server accepted this address."}
        if code_real in (550, 551, 553):
            return {"status": "UNDELIVERABLE", "detail": msg_real.decode(errors="ignore")[:120]}
        return {"status": "UNKNOWN", "detail": f"SMTP response code: {code_real}"}
    except Exception as error:
        return {"status": "UNKNOWN", "detail": f"SMTP check unavailable: {error}"}


def verify_candidates(candidates, domain, smtp_enabled):
    domain_mail = check_domain_mail(domain)
    verified = []
    for candidate in candidates[:5]:
        email = candidate["email"]
        if not syntax_check(email):
            result = {"email": email, "syntax": False, "mx": False, "status": "INVALID_SYNTAX", "detail": "Email fails syntax check."}
        elif not domain_mail["mx"]:
            result = {"email": email, "syntax": True, "mx": False, "status": "INVALID_DOMAIN", "detail": domain_mail["detail"]}
        elif smtp_enabled:
            smtp_result = smtp_check(email, domain)
            result = {"email": email, "syntax": True, "mx": True, "status": smtp_result["status"], "detail": smtp_result["detail"]}
        else:
            result = {"email": email, "syntax": True, "mx": True, "status": "MX_VALID", "detail": domain_mail["detail"]}
        verified.append(result)
        if smtp_enabled:
            time.sleep(0.5)
    return verified


def find_exact_match(found_emails, first, last):
    possible_locals = {formatter(first, last) for formatter in EMAIL_PATTERNS.values()}
    for email in found_emails:
        if email.split("@")[0].lower() in possible_locals:
            return email
    return None


def choose_best(candidates, verification):
    rank = {"DELIVERABLE": 5, "CATCH_ALL": 4, "MX_VALID": 3, "UNKNOWN": 2, "UNDELIVERABLE": 1}
    verification_by_email = {item["email"]: item for item in verification}
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (rank.get(verification_by_email.get(item["email"], {}).get("status"), 0), item["probability"]), reverse=True)[0]["email"]


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/search")
def api_search():
    payload = request.get_json(silent=True) or {}
    try:
        first, last = sanitize_name(payload.get("fullName", ""))
        domain = normalize_domain(payload.get("domain", ""))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    smtp_enabled = bool(payload.get("smtpCheck"))
    found_emails, sources = search_for_company_emails(domain)
    pattern_probs = analyse_patterns(found_emails, domain)
    exact_match = find_exact_match(found_emails, first, last)
    if exact_match:
        candidates = [{"email": exact_match, "pattern": "found_online", "probability": 99.9, "source": "Exact public match"}]
    else:
        candidates = generate_emails(first, last, domain, pattern_probs)
    verification = verify_candidates(candidates, domain, smtp_enabled)
    best_email = choose_best(candidates, verification)
    return jsonify(
        {
            "person": f"{first.title()} {last.title()}",
            "domain": domain,
            "foundEmails": found_emails[:40],
            "sources": sources,
            "patterns": pattern_probs,
            "candidates": candidates[:9],
            "verification": verification,
            "bestEmail": best_email,
            "usedFallback": not bool(pattern_probs),
            "smtpChecked": smtp_enabled,
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
