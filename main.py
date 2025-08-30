# -*- coding: utf-8 -*-
"""
Google CSE → US-Origin Deportees extractor (CSV)
Env:
  GOOGLE_API_KEY=<your key>
  GOOGLE_SEARCH_ENGINE_ID=<your cx>

Run:
  python us_deportees_cse.py
"""

import os
import re
import httpx
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")
if not API_KEY or not SEARCH_ENGINE_ID:
    raise ValueError("Missing GOOGLE_API_KEY or GOOGLE_SEARCH_ENGINE_ID in env.")

# --- Query presets (U.S.-origin only) ---
# Tip: focus by destination. Duplicate lines for your target countries/news portals.
QUERIES = [
    # Official / U.S. gov
    'site:ice.gov (removal OR deport* OR repatriat*) "United States" OR "U.S."',
    'site:dhs.gov (removal OR deport* OR repatriat*)',
    'site:cbp.gov removal OR deport*',
    # Embassies / Consulates / IOM
    'site:usembassy.gov deport* OR removal',
    'site:iom.int charter flight deport* "United States" OR "U.S."',
    # Ghana example (swap in your destination country portals)
    'site:gov.gh deport* OR "returnees" "United States" OR "U.S."',
    'site:graphic.com.gh OR site:myjoyonline.com OR site:citinewsroom.com deport* "United States" OR "U.S."',
    # Generic catch-alls
    '"deportees from the U.S." OR "deported from the United States" charter flight',
    '"arrived from the United States" deport* OR returnees',
]

MAX_RESULTS = 80     # total per query (CSE caps ~100)
BATCH_SIZE = 10
OUTPUT_CSV = "us_origin_deportees.csv"

# --- Hints & dictionaries tuned for U.S. origin ---
DESTINATION_COUNTRIES = [
    "Ghana","Nigeria","Mexico","Guatemala","Honduras","El Salvador","Jamaica",
    "Dominican Republic","Haiti","Cuba","Pakistan","India","China","Ecuador",
    "Colombia","Brazil","Venezuela","Philippines","Bangladesh","Cameroon",
    "Sierra Leone","Liberia","Kenya","Somalia","Ethiopia","South Sudan",
    "Nicaragua","Peru","Bolivia","Paraguay","Uruguay","Argentina","Chile",
    "Morocco","Algeria","Tunisia","Egypt","Iraq","Iran","Afghanistan","Nepal",
    "Sri Lanka","Vietnam","Laos","Thailand","Indonesia","Malaysia","Turkey",
    "Albania","Kosovo","Bosnia","Serbia","Romania","Bulgaria","Ukraine",
    "Russia","Georgia","Armenia","Azerbaijan"
]

AGENCY_HINTS = [
    "ICE","U.S. Immigration and Customs Enforcement","Enforcement and Removal Operations",
    "ERO","DHS","Department of Homeland Security","CBP",
    "ICE Air","ICE Air Operations","IAO"
]

TRANSPORT_HINTS = {
    "charter_flight": [
        "charter flight","chartered flight","deportation flight","ICE Air","World Atlantic",
        "iAero","Swift Air","Omni Air"
    ],
    "commercial_flight": ["commercial flight"],
    "bus": ["bus"],
    "ship": ["ship","vessel","boat"]
}

# --- HTTP ---
def google_search(api_key, search_engine_id, query, **params):
    base = "https://www.googleapis.com/customsearch/v1"
    qparams = {"key": api_key, "cx": search_engine_id, "q": query, **params}
    try:
        r = httpx.get(base, params=qparams, timeout=15.0)
        r.raise_for_status()
        return r.json()
    except httpx.RequestError as e:
        print(f"[http] request error: {e}")
        return {}
    except httpx.HTTPStatusError as e:
        print(f"[http] status error: {e.response.text}")
        return {}

# --- Heuristics (U.S.-origin aware) ---
NEAR_KEYS = re.compile(r'(deport|deportee|removed|removal|repatriat|returnee)', re.I)
INT_RE = re.compile(r'\b(\d{1,4})\b')
RANGE_RE = re.compile(r'\b(\d{1,4})\s*(?:-|–|—|to|and|between)\s*(\d{1,4})\b', re.I)

US_TOKENS = [
    "united states","u.s.","us ","u.s.a","usa","america","american authorities","us authorities"
]

def pick_first_count(text, window=50):
    if not text:
        return None, None, False
    for m in NEAR_KEYS.finditer(text):
        s = max(0, m.start() - window)
        e = min(len(text), m.end() + window)
        ctx = text[s:e]
        rm = RANGE_RE.search(ctx)
        if rm:
            low, high = int(rm.group(1)), int(rm.group(2))
            return int(round((low + high) / 2)), (low, high), True
        im = INT_RE.search(ctx)
        if im:
            return int(im.group(1)), None, False
    return None, None, False

def detect_transport(text):
    if not text: return "unknown"
    tl = text.lower()
    for label, keys in TRANSPORT_HINTS.items():
        for k in keys:
            if k.lower() in tl:
                return label
    return "unknown"

def detect_agency(text):
    if not text: return None
    tl = text.lower()
    for a in AGENCY_HINTS:
        if a.lower() in tl:
            return a
    return None

def implies_us_origin(text):
    if not text: return False
    tl = text.lower()
    if any(tok in tl for tok in US_TOKENS):
        # strengthen with prepositions/verbs if available
        if ("from the united states" in tl or "from the u.s." in tl or
            "deported from the united states" in tl or "removed from the united states" in tl or
            "deported from the u.s." in tl or "removed from the u.s." in tl):
            return True
        # also accept if agency is ICE/ERO
        if "ice" in tl or "enforcement and removal operations" in tl or "ice air" in tl:
            return True
    return False

def detect_destination(text):
    if not text: return None
    tl = text.lower()
    dest = None
    for c in DESTINATION_COUNTRIES:
        cl = c.lower()
        if f" to {cl}" in tl or f" arrived in {cl}" in tl or f" returned to {cl}" in tl:
            dest = c
            break
    # fallback: if only country name occurs with verbs "arrived"/"landed"
    if not dest:
        for c in DESTINATION_COUNTRIES:
            cl = c.lower()
            if cl in tl and ("arrived" in tl or "landed" in tl or "received" in tl or "welcomed" in tl):
                dest = c
                break
    return dest

def get_meta(ditem, keys):
    pagemap = ditem.get("pagemap", {})
    metas = pagemap.get("metatags", [])
    for m in metas:
        for k in keys:
            v = m.get(k)
            if v: return v
    return None

def parse_date(dt):
    if not dt: return None
    try:
        return pd.to_datetime(dt, errors="coerce").isoformat()
    except Exception:
        return None

# --- Processing ---
def process_items(items, query):
    rows = []
    now_iso = datetime.utcnow().isoformat() + "Z"
    for it in items:
        title = it.get("title", "")
        link = it.get("link", "")
        snippet = it.get("snippet", "")
        domain = it.get("displayLink", "")
        publisher = get_meta(it, ["og:site_name", "application-name"]) or domain
        published = parse_date(get_meta(it, ["article:published_time","datePublished","og:updated_time"]))
        descr = get_meta(it, ["og:description","description"])
        author = get_meta(it, ["author","article:author","og:author"])

        bag = " | ".join(filter(None, [title, snippet, descr, publisher]))

        # Only keep if U.S. origin is implied (or source is ICE/DHS/CBP domains)
        domain_l = domain.lower()
        us_source_domain = any(d in domain_l for d in ["ice.gov","dhs.gov","cbp.gov","usembassy.gov"])
        if not (implies_us_origin(bag) or us_source_domain):
            continue

        count, rng, est = pick_first_count(bag)
        agency = detect_agency(bag)
        transport = detect_transport(bag)
        destination = detect_destination(bag)

        rows.append({
            "source_url": link,
            "publisher_domain": domain,
            "headline": title,
            "snippet": snippet,
            "date_discovered": now_iso,
            "publisher_name": publisher,
            "date_published": published,
            "author_name": author,

            # Hard-set origin to United States for this pipeline
            "origin_country": "United States",
            "destination_country": destination,

            "deportee_count": count,
            "deportee_count_is_estimate": est,
            "deportee_count_low": (rng[0] if rng else None),
            "deportee_count_high": (rng[1] if rng else None),

            "conducting_agency": agency or ("ICE" if us_source_domain else None),
            "transport_mode": transport,
            "cse_query": query,
        })
    return rows

def run_queries(queries):
    out = []
    for q in queries:
        print(f"\n=== Query: {q}")
        fetched = 0
        for start in tqdm(range(1, MAX_RESULTS + 1, BATCH_SIZE), desc="Fetching", unit="page"):
            resp = google_search(API_KEY, SEARCH_ENGINE_ID, q, start=start, num=BATCH_SIZE)
            items = resp.get("items", [])
            if not items: break
            out.extend(process_items(items, q))
            fetched += len(items)
            if "nextPage" not in resp.get("queries", {}): break
        print(f"Fetched {fetched} items (pre-filter). Kept {sum(1 for _ in out)} total so far.")
    return out

if __name__ == "__main__":
    rows = run_queries(QUERIES)
    if not rows:
        print("No US-origin deportation results found.")
    else:
        df = pd.DataFrame(rows).drop_duplicates(subset=["source_url"])
        print(df.head(10))
        outpath = "us_origin_deportees.csv"
        df.to_csv(outpath, index=False)
        print(f"Saved {len(df)} rows → {outpath}")
