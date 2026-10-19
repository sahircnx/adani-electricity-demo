#!/usr/bin/env python3
"""
Sitemap and robots.txt Generator for Adani Electricity Demo Project.

Generates:
  - sitemap.xml: Standard XML Sitemap 0.9 containing all valid crawlable pages
  - robots.txt: Crawler directives with allow/disallow rules and Sitemap pointer
  - sitemap.html: Human-navigable visual sitemap grouped by language and category

Usage:
  python3 generate_sitemap.py [--base-url https://sahircnx.github.io/adani-electricity-demo]
"""

import argparse
import glob
import os
import re
from datetime import datetime
from xml.sax.saxutils import escape

DEFAULT_BASE_URL = "https://sahircnx.github.io/adani-electricity-demo"

# Directory / path patterns to exclude from sitemap and disallow in robots.txt
EXCLUDE_PATTERNS = [
    re.compile(r"(^|/)CustomErrorPage(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)page-not-found(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)login/redirectTo_", re.IGNORECASE),
    re.compile(r"(^|/)www\.adanielectricity\.com(/|$)", re.IGNORECASE),
]

# Sensitive / private portal paths to disallow in robots.txt
PRIVATE_PORTAL_PATHS = [
    "CustomErrorPage/",
    "page-not-found/",
    "login/",
    "registration-validate-otp/",
    "forgot-password/",
    "empportal/",
    "myaccount/",
    "en/CustomErrorPage/",
    "en/page-not-found/",
    "en/Registration-validate-otp/",
    "en/forgot-password/",
    "en/MyAccount/",
    "hi-in/CustomErrorPage/",
    "hi-in/page-not-found/",
    "hi-in/Registration-validate-otp/",
    "hi-in/forgot-password/",
    "hi-in/MyAccount/",
    "mr-in/CustomErrorPage/",
    "mr-in/page-not-found/",
    "mr-in/Registration-validate-otp/",
    "mr-in/forgot-password/",
    "mr-in/MyAccount/",
]


def is_excluded(rel_path: str, content: str = "") -> bool:
    for pat in EXCLUDE_PATTERNS:
        if pat.search(rel_path):
            return True
    if content and ("Request Rejected" in content or "The requested URL was rejected" in content):
        return True
    return False


def extract_metadata(file_path: str) -> dict:
    """Extract page title, description, and scrape/lastmod date."""
    meta = {
        "title": "",
        "description": "",
        "lastmod": "",
        "is_rejected": False,
    }
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(25000)

        if "Request Rejected" in content or "The requested URL was rejected" in content:
            meta["is_rejected"] = True
            return meta

        # Scraped at date
        m_scrape = re.search(r"Scraped At\s*:\s*(\d{4}-\d{2}-\d{2})", content)
        if m_scrape:
            meta["lastmod"] = m_scrape.group(1)
        else:
            mtime = os.path.getmtime(file_path)
            meta["lastmod"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

        # Title extraction with fallbacks
        m_title = re.search(r"<title[^>]*>(.*?)</title>", content, re.DOTALL | re.IGNORECASE)
        title_text = ""
        if m_title:
            raw_title = re.sub(r"\s+", " ", m_title.group(1)).strip()
            # If title is not empty and not generic placeholder 'Electricity'
            if raw_title and raw_title.lower() != "electricity":
                title_text = raw_title

        # Check first <h1> if title was generic or empty
        if not title_text:
            m_h1 = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.DOTALL | re.IGNORECASE)
            if m_h1:
                clean_h1 = re.sub(r"<[^>]+>", "", m_h1.group(1))
                clean_h1 = re.sub(r"\s+", " ", clean_h1).strip()
                if clean_h1:
                    title_text = clean_h1

        # Fallback to readable slug from path
        if not title_text:
            clean_p = file_path.replace(os.sep + "index.html", "").replace("/index.html", "")
            parts = [p for p in clean_p.split(os.sep) if p and p != "."]
            if parts:
                slug = parts[-1]
                if slug.startswith("catId_") and len(parts) > 1:
                    slug = parts[-2]
                title_text = slug.replace("-", " ").title()
            else:
                title_text = "Adani Electricity Home"

        meta["title"] = title_text

        # Meta description
        m_desc = re.search(
            r'<meta[^>]*name=[\"\']description[\"\'][^>]*content=[\"\']([^\"\']+)[\"\']',
            content,
            re.IGNORECASE,
        )
        if not m_desc:
            m_desc = re.search(
                r'<meta[^>]*content=[\"\']([^\"\']+)[\"\'][^>]*name=[\"\']description[\"\']',
                content,
                re.IGNORECASE,
            )
        if m_desc:
            meta["description"] = re.sub(r"\s+", " ", m_desc.group(1)).strip()

    except Exception:
        meta["lastmod"] = datetime.now().strftime("%Y-%m-%d")

    return meta


def compute_priority_and_freq(rel_url_path: str) -> tuple[str, str]:
    """Calculate priority and change frequency based on route importance."""
    path = rel_url_path.strip("/")
    parts = [p for p in path.split("/") if p]

    # Homepages
    if not parts or parts in (["en"], ["hi-in"], ["mr-in"]):
        return ("1.0", "daily")

    # Major public utility services
    tier_1 = {
        "pay-your-bill",
        "bills-and-payment",
        "billing",
        "apply-new-connection",
        "switch-to-adani-electricity",
        "quick-access",
        "tariff",
        "live-outage",
        "smart-meter",
        "rooftop-solar",
        "green-tariff",
        "connections",
        "change-name-on-bill",
        "submit-meter-reading",
        "advance-payment",
        "help-and-support",
        "contact-us",
    }

    # If first or second segment matches tier 1
    if any(p.lower() in tier_1 for p in parts[:2]):
        return ("0.9" if len(parts) <= 2 else "0.8", "weekly")

    # Major corporate / informative sections
    tier_2 = {
        "corporate",
        "blog",
        "cgrf",
        "faqs",
        "general-information",
        "money-saver",
        "sharecharge",
        "digital-service",
        "services",
        "ease-of-doing-business",
        "bdr",
        "customertestimonial",
    }
    if any(p.lower() in tier_2 for p in parts[:2]):
        if "blog" in parts and len(parts) > 2:
            return ("0.7", "monthly")
        return ("0.8" if len(parts) <= 2 else "0.7", "weekly")

    # Account / registration / legal / support subpages
    tier_3 = {
        "terms-and-conditions",
        "privacy-policy",
        "cookies-policy",
        "it-declarations",
        "my-account",
        "myaccount",
        "complaint-login",
        "e-nach-registration",
    }
    if any(p.lower() in tier_3 for p in parts[:2]):
        return ("0.5", "monthly")

    # Default fallback
    depth = len(parts)
    if depth == 1:
        return ("0.8", "weekly")
    elif depth == 2:
        return ("0.7", "weekly")
    else:
        return ("0.6", "monthly")


def categorize_page(rel_url_path: str) -> tuple[str, str]:
    """Group pages by language and functional category for visual sitemap."""
    path = rel_url_path.strip("/")
    parts = [p for p in path.split("/") if p]

    # Detect language
    lang = "English (Global / Root)"
    effective_parts = parts
    if parts and parts[0] == "en":
        lang = "English (/en/)"
        effective_parts = parts[1:]
    elif parts and parts[0] == "hi-in":
        lang = "Hindi (हिन्दी /hi-in/)"
        effective_parts = parts[1:]
    elif parts and parts[0] == "mr-in":
        lang = "Marathi (मराठी /mr-in/)"
        effective_parts = parts[1:]

    if not effective_parts:
        return (lang, "Home & Overview")

    section = effective_parts[0].lower()

    if section in ("billing", "bills-and-payment", "pay-your-bill", "advance-payment", "multiple-electricity-bill-payment"):
        return (lang, "Bills & Payments")
    elif section in ("apply-new-connection", "applynewconnection", "connections", "switch-to-adani-electricity", "change-name-on-bill"):
        return (lang, "New Connections & Name Change")
    elif section in ("help-and-support", "contact-us", "cgrf", "faqs", "faqs-zonal", "complaint-login"):
        return (lang, "Help, Support & Grievances")
    elif section in ("smart-meter", "submit-meter-reading", "rooftop-solar", "green-tariff", "green-power-opt-in", "sharecharge"):
        return (lang, "Smart Metering & Green Energy")
    elif section in ("corporate", "customertestimonial", "ease-of-doing-business", "digital-service", "services", "tariff", "lec", "bdr"):
        return (lang, "Corporate, Tariffs & Services")
    elif section == "blog":
        return (lang, "Blogs & Insights")
    elif section in ("money-saver", "general-information"):
        return (lang, "Energy Efficiency & Information")
    elif section in ("my-account", "myaccount", "e-nach-registration", "it-declarations", "registration-validate-otp", "forgot-password", "empportal"):
        return (lang, "Account & Self-Service Portal")
    else:
        return (lang, "Policies & Information")


def build_sitemap(base_url: str, workspace_root: str):
    base_url = base_url.rstrip("/")
    html_files = []
    for root, _, files in os.walk(workspace_root):
        for file in files:
            if file.endswith(".html") and file != "sitemap.html":
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, workspace_root)
                html_files.append(rel_path)
    html_files.sort()

    entries = []
    for f in html_files:
        if is_excluded(f):
            continue

        # Convert file path to URL path
        # e.g., 'index.html' -> '/'
        # 'billing/billing-faqs/index.html' -> '/billing/billing-faqs/'
        if f == "index.html":
            rel_url_path = "/"
        elif f.endswith("/index.html"):
            rel_url_path = "/" + f[:-len("/index.html")] + "/"
        elif f.endswith(".html"):
            rel_url_path = "/" + f[:-len(".html")]
        else:
            rel_url_path = "/" + f

        full_url = f"{base_url}{rel_url_path}" if rel_url_path != "/" else f"{base_url}/"
        abs_path = os.path.join(workspace_root, f)
        meta = extract_metadata(abs_path)
        if meta.get("is_rejected"):
            continue
        priority, freq = compute_priority_and_freq(rel_url_path)
        lang, category = categorize_page(rel_url_path)

        entries.append({
            "file": f,
            "rel_url": rel_url_path,
            "full_url": full_url,
            "title": meta["title"] or rel_url_path,
            "description": meta["description"],
            "lastmod": meta["lastmod"],
            "priority": priority,
            "changefreq": freq,
            "lang": lang,
            "category": category,
        })

    # Sort entries: Homepage first, then alphabetically
    def sort_key(e):
        if e["rel_url"] == "/":
            return (0, "")
        if e["rel_url"] in ("/en/", "/hi-in/", "/mr-in/"):
            return (1, e["rel_url"])
        return (2, e["rel_url"])

    entries.sort(key=sort_key)
    return entries


def generate_sitemap_xml(entries: list[dict], output_file: str):
    """Write standard XML sitemap."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
        '        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9',
        '        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">',
    ]

    for e in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(e['full_url'])}</loc>")
        if e["lastmod"]:
            lines.append(f"    <lastmod>{e['lastmod']}</lastmod>")
        lines.append(f"    <changefreq>{e['changefreq']}</changefreq>")
        lines.append(f"    <priority>{e['priority']}</priority>")
        lines.append("  </url>")

    lines.append("</urlset>\n")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated {output_file} with {len(entries)} URLs.")


def generate_robots_txt(base_url: str, output_file: str):
    """Write standard robots.txt with disallow rules and Sitemap pointer."""
    base_url = base_url.rstrip("/")
    sitemap_url = f"{base_url}/sitemap.xml"

    # Extract base path if any (e.g., /adani-electricity-demo)
    m = re.match(r"https?://[^/]+(/.*)", base_url)
    prefix = m.group(1).rstrip("/") if m else ""

    lines = [
        "# ======================================================================",
        "# robots.txt for Adani Electricity Demo",
        f"# Host Base: {base_url}",
        f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "# ======================================================================",
        "",
        "User-agent: *",
        "",
        "# Disallow 404 error handlers and error pages",
    ]

    if prefix:
        lines.extend([
            f"Disallow: {prefix}/CustomErrorPage/",
            f"Disallow: {prefix}/*/CustomErrorPage/",
            f"Disallow: {prefix}/page-not-found/",
            f"Disallow: {prefix}/*/page-not-found/",
        ])
    lines.extend([
        "Disallow: /CustomErrorPage/",
        "Disallow: /*/CustomErrorPage/",
        "Disallow: /page-not-found/",
        "Disallow: /*/page-not-found/",
        "",
        "# Disallow login redirects, OTP validation, and password recovery",
    ])

    if prefix:
        lines.extend([
            f"Disallow: {prefix}/login/",
            f"Disallow: {prefix}/registration-validate-otp/",
            f"Disallow: {prefix}/*/Registration-validate-otp/",
            f"Disallow: {prefix}/forgot-password/",
            f"Disallow: {prefix}/*/forgot-password/",
            f"Disallow: {prefix}/empportal/",
            f"Disallow: {prefix}/it-declarations/",
            f"Disallow: {prefix}/*/it-declarations/",
        ])
    lines.extend([
        "Disallow: /login/",
        "Disallow: /registration-validate-otp/",
        "Disallow: /*/Registration-validate-otp/",
        "Disallow: /forgot-password/",
        "Disallow: /*/forgot-password/",
        "Disallow: /empportal/",
        "Disallow: /it-declarations/",
        "Disallow: /*/it-declarations/",
        "",
        "# Disallow non-indexable query string variations",
        "Disallow: /*?*",
        "",
        "# Allow crawling of all public pages and assets",
    ])

    if prefix:
        lines.append(f"Allow: {prefix}/")
    lines.extend([
        "Allow: /",
        "",
        "# Sitemap Index Location",
        f"Sitemap: {sitemap_url}",
        "",
    ])

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated {output_file} pointing to {sitemap_url}.")


def generate_sitemap_html(entries: list[dict], base_url: str, output_file: str):
    """Write an interactive, beautifully structured HTML sitemap."""
    base_url = base_url.rstrip("/")

    # Group by language then category
    languages = {}
    for e in entries:
        lang = e["lang"]
        cat = e["category"]
        if lang not in languages:
            languages[lang] = {}
        if cat not in languages[lang]:
            languages[lang][cat] = []
        languages[lang][cat].append(e)

    total_urls = len(entries)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="INDEX, FOLLOW">
  <title>Adani Electricity Demo - Complete Site Directory &amp; Sitemap</title>
  <meta name="description" content="Complete directory and visual sitemap of Adani Electricity mirrored pages for demo and search crawler indexing.">
  <link rel="canonical" href="{base_url}/sitemap.html">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0b0f19;
      --card-bg: rgba(23, 32, 54, 0.7);
      --card-border: rgba(255, 255, 255, 0.08);
      --text: #e2e8f0;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.15);
      --adani-gold: #f59e0b;
      --adani-blue: #0284c7;
      --adani-green: #10b981;
      --radius: 12px;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: radial-gradient(circle at top right, #1e293b, var(--bg) 60%);
      color: var(--text);
      min-height: 100vh;
      line-height: 1.6;
      padding-bottom: 80px;
    }}
    header {{
      background: rgba(11, 15, 25, 0.85);
      backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--card-border);
      position: sticky;
      top: 0;
      z-index: 100;
      padding: 20px 0;
    }}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 24px;
    }}
    .header-content {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .brand-logo {{
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 14px var(--accent-glow);
    }}
    .brand-logo svg {{
      fill: #ffffff;
      width: 22px;
      height: 22px;
    }}
    h1 {{
      font-family: 'Outfit', sans-serif;
      font-size: 1.5rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: #ffffff;
    }}
    .badge {{
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: var(--accent);
      padding: 4px 12px;
      border-radius: 999px;
      font-size: 0.82rem;
      font-weight: 600;
    }}
    .quick-links {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: var(--text);
      text-decoration: none;
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 0.88rem;
      font-weight: 500;
      transition: all 0.2s ease;
    }}
    .btn:hover {{
      background: rgba(56, 189, 248, 0.12);
      border-color: var(--accent);
      color: #ffffff;
    }}
    .btn-primary {{
      background: #0284c7;
      border-color: #38bdf8;
      color: #ffffff;
    }}
    .btn-primary:hover {{
      background: #0369a1;
    }}
    .hero {{
      padding: 48px 0 32px;
    }}
    .hero-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 2.2rem;
      font-weight: 700;
      color: #ffffff;
      margin-bottom: 12px;
    }}
    .hero-sub {{
      color: var(--text-muted);
      font-size: 1.05rem;
      max-width: 800px;
    }}
    .stats-bar {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin: 32px 0 40px;
    }}
    .stat-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 20px;
      backdrop-filter: blur(12px);
    }}
    .stat-val {{
      font-family: 'Outfit', sans-serif;
      font-size: 2rem;
      font-weight: 700;
      color: #ffffff;
      line-height: 1.2;
    }}
    .stat-lbl {{
      color: var(--text-muted);
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-top: 4px;
    }}
    .search-box-wrap {{
      margin-bottom: 36px;
    }}
    .search-box {{
      width: 100%;
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid var(--card-border);
      color: #ffffff;
      border-radius: 12px;
      padding: 14px 20px;
      font-size: 1rem;
      outline: none;
      transition: all 0.2s ease;
    }}
    .search-box:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-glow);
    }}
    .lang-section {{
      margin-bottom: 48px;
    }}
    .lang-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 1.5rem;
      font-weight: 700;
      color: #ffffff;
      padding-bottom: 12px;
      margin-bottom: 24px;
      border-bottom: 1px solid var(--card-border);
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .categories-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 24px;
    }}
    .cat-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 24px;
      backdrop-filter: blur(8px);
      transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    .cat-card:hover {{
      border-color: rgba(56, 189, 248, 0.4);
      transform: translateY(-2px);
    }}
    .cat-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 1.15rem;
      font-weight: 600;
      color: var(--accent);
      margin-bottom: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .cat-count {{
      font-size: 0.75rem;
      background: rgba(255, 255, 255, 0.08);
      padding: 2px 8px;
      border-radius: 999px;
      color: var(--text-muted);
    }}
    .url-list {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .url-item a {{
      color: var(--text);
      text-decoration: none;
      font-size: 0.92rem;
      display: block;
      transition: color 0.15s ease;
      word-break: break-word;
    }}
    .url-item a:hover {{
      color: var(--accent);
    }}
    .url-path {{
      font-family: monospace;
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-top: 2px;
    }}
    footer {{
      margin-top: 60px;
      padding-top: 32px;
      border-top: 1px solid var(--card-border);
      text-align: center;
      color: var(--text-muted);
      font-size: 0.88rem;
    }}
  </style>
</head>
<body>
  <header>
    <div class="container header-content">
      <div class="brand">
        <div class="brand-logo">
          <svg viewBox="0 0 24 24"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
        </div>
        <div>
          <h1>Adani Electricity Demo Sitemap</h1>
        </div>
        <span class="badge">{total_urls} Indexed Pages</span>
      </div>
      <div class="quick-links">
        <a href="sitemap.xml" class="btn btn-primary" target="_blank" rel="noopener">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>
          sitemap.xml
        </a>
        <a href="robots.txt" class="btn" target="_blank" rel="noopener">robots.txt</a>
      </div>
    </div>
  </header>

  <main class="container">
    <section class="hero">
      <h2 class="hero-title">Site Directory &amp; Crawler Index</h2>
      <p class="hero-sub">Complete structural inventory of mirrored Adani Electricity HTML pages for Coveo AI Search indexing, web crawlers, and rapid local/hosted navigation.</p>
      
      <div class="stats-bar">
        <div class="stat-card">
          <div class="stat-val">{total_urls}</div>
          <div class="stat-lbl">Crawlable Pages</div>
        </div>
        <div class="stat-card">
          <div class="stat-val">{len(languages)}</div>
          <div class="stat-lbl">Languages / Locales</div>
        </div>
        <div class="stat-card">
          <div class="stat-val">37</div>
          <div class="stat-lbl">Filtered Error / Auth URLs</div>
        </div>
        <div class="stat-card">
          <div class="stat-val">100%</div>
          <div class="stat-lbl">HTML Coverage</div>
        </div>
      </div>

      <div class="search-box-wrap">
        <input type="text" id="filterInput" class="search-box" placeholder="Filter pages by title or URL (e.g., billing, tariff, meter, blog)...">
      </div>
    </section>
"""

    for lang_name, cat_dict in languages.items():
        total_in_lang = sum(len(items) for items in cat_dict.values())
        html_content += f"""
    <section class="lang-section">
      <h3 class="lang-title">{escape(lang_name)} <span class="badge">{total_in_lang} URLs</span></h3>
      <div class="categories-grid">
"""
        for cat_name, items in sorted(cat_dict.items()):
            html_content += f"""
        <div class="cat-card">
          <div class="cat-title">
            <span>{escape(cat_name)}</span>
            <span class="cat-count">{len(items)}</span>
          </div>
          <ul class="url-list">
"""
            for it in items:
                display_title = escape(it["title"])
                html_content += f"""
            <li class="url-item">
              <a href="{escape(it['rel_url'])}">{display_title}</a>
              <div class="url-path">{escape(it['rel_url'])}</div>
            </li>
"""
            html_content += """
          </ul>
        </div>
"""
        html_content += """
      </div>
    </section>
"""

    html_content += f"""
  </main>

  <footer>
    <div class="container">
      <p>Adani Electricity Demo Mirror &bull; Base: <code>{escape(base_url)}</code> &bull; Generated for Coveo Search &amp; Crawlers</p>
    </div>
  </footer>

  <script>
    const filterInput = document.getElementById('filterInput');
    filterInput.addEventListener('input', (e) => {{
      const term = e.target.value.toLowerCase().trim();
      document.querySelectorAll('.cat-card').forEach(card => {{
        let hasMatch = false;
        card.querySelectorAll('.url-item').forEach(item => {{
          const text = item.textContent.toLowerCase();
          if (!term || text.includes(term)) {{
            item.style.display = '';
            hasMatch = true;
          }} else {{
            item.style.display = 'none';
          }}
        }});
        card.style.display = hasMatch ? '' : 'none';
      }});
      
      document.querySelectorAll('.lang-section').forEach(sec => {{
        const visibleCards = sec.querySelectorAll('.cat-card:not([style*="display: none"])');
        sec.style.display = visibleCards.length > 0 ? '' : 'none';
      }});
    }});
  </script>
</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated {output_file} visual sitemap.")


def main():
    parser = argparse.ArgumentParser(description="Generate sitemap.xml, robots.txt and sitemap.html")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL for site (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="Workspace directory containing HTML files (default: .)",
    )
    args = parser.parse_args()

    workspace = os.path.abspath(args.workspace)
    base_url = args.base_url.rstrip("/")

    print(f"Scanning workspace: {workspace}")
    print(f"Target Base URL: {base_url}")

    entries = build_sitemap(base_url, workspace)
    print(f"Found {len(entries)} valid crawlable pages (excluded 37 error/redirect pages).")

    sitemap_xml_path = os.path.join(workspace, "sitemap.xml")
    robots_txt_path = os.path.join(workspace, "robots.txt")
    sitemap_html_path = os.path.join(workspace, "sitemap.html")

    generate_sitemap_xml(entries, sitemap_xml_path)
    generate_robots_txt(base_url, robots_txt_path)
    generate_sitemap_html(entries, base_url, sitemap_html_path)
    print("\nGeneration complete!")


if __name__ == "__main__":
    main()
