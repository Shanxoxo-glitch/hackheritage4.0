"""
Threat / intimidation corpus builder (the longest-lead item in the project).

Sources
  1. Indian Kanoon (API, token required: https://api.indiankanoon.org)  -> candidate sentences from
     judgments tagged SC/ST Atrocities / POCSO / witness intimidation, extracted next to
     coercion cues ("threatened", "pressurised to withdraw", "compromise", "hostile witness"...).
     Output CSV for MANUAL labelling: text, label (empty), category_hint, source_url, doc_title, query.
  2. Synthetic corpora already in training/data (threat V7: 520 rows, distress V3 negatives).
  3. Labelled Kanoon rows merged back in (--merge) -> training/data/threat_corpus_v8.csv
     Labels: 1 = threat/coercion, 0 = neutral-legal or generic-distress. Target >= 2500 rows by Week 2.

Usage
  export IK_API_TOKEN=...            # never commit it
  PYTHONPATH=. python training/corpus/threat_corpus_builder.py scrape --pages 5
  PYTHONPATH=. python training/corpus/threat_corpus_builder.py scrape --dry-run       # offline parser check
  PYTHONPATH=. python training/corpus/threat_corpus_builder.py merge --labelled training/data/kanoon_labelled.csv
"""
import argparse
import csv
import html
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "training" / "data"

API = "https://api.indiankanoon.org"
QUERIES = [
    "SC ST Prevention of Atrocities Act witness threatened withdraw complaint",
    "witness intimidation threatened not to depose atrocities",
    "complainant pressurised to compromise SC ST Act",
    "hostile witness threat accused caste atrocity",
    "victim threatened dire consequences complaint police caste",
    "POCSO victim threatened family withdraw case",
]
CUES = {
    "physical_threat": r"\b(kill|beat|assault|burn|hurt|eliminate|dire consequences|finish (him|her|you))\b",
    "case_withdrawal": r"\b(withdraw|compromise|settle|take back) (the |her |his |their )?(complaint|case|fir|statement)\b",
    "forced_silence": r"\b(not to (depose|speak|disclose|tell)|keep (quiet|silent|mum)|remain silent)\b",
    "witness_intimidation": r"\b(hostile|intimidat|pressuri[sz]ed|coerc|threaten)\w*\b",
    "financial_coercion": r"\b(livelihood|wages|employment|land|ration|boycott|money)\b.*\b(threat|stop|deny|deprive)\w*",
    "family_threat": r"\b(family|wife|husband|children|daughter|son|parents)\b.*\b(threat|harm|kill|abduct)\w*",
}
NEUTRAL_LEGAL_HINT = r"\b(section|hon'ble|learned counsel|appellant|petitioner|bail|sentenced|acquitted)\b"


def strip_html(text):
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", text) if 25 <= len(s.strip()) <= 400]


def extract_candidates(text, min_cues=1):
    """Return [(sentence, category_hint)] for sentences carrying at least `min_cues` coercion cue(s)."""
    out = []
    for s in sentences(strip_html(text)):
        hits = [cat for cat, rx in CUES.items() if re.search(rx, s, flags=re.I)]
        if len(hits) >= min_cues:
            out.append((s, "|".join(hits)))
    return out


def _get(url, token, **params):
    import httpx
    r = httpx.post(url, headers={"Authorization": f"Token {token}", "Accept": "application/json"},
                   data=params, timeout=30)
    r.raise_for_status()
    return r.json()


def scrape(args):
    out_path = DATA / "kanoon_candidates.csv"
    if args.dry_run:
        sample = ("<p>The complainant stated that the accused threatened to kill her if she deposed before the "
                  "court. The learned counsel for the appellant argued that Section 3(1)(r) is not attracted. "
                  "PW-4 turned hostile after being pressurised to compromise the case.</p>")
        for s, cat in extract_candidates(sample):
            print(f"[{cat}] {s}")
        return
    token = os.environ.get("IK_API_TOKEN")
    if not token:
        sys.exit("set IK_API_TOKEN (https://api.indiankanoon.org) or use --dry-run")
    seen, rows = set(), []
    if out_path.exists():
        with open(out_path, newline="") as f:
            for r in csv.DictReader(f):
                seen.add(r["text"].lower()); rows.append(r)
    for q in QUERIES:
        for page in range(args.pages):
            try:
                res = _get(f"{API}/search/", token, formInput=q, pagenum=page)
            except Exception as e:
                print("search failed:", q, page, e); break
            for doc in res.get("docs", []):
                tid = doc.get("tid")
                try:
                    d = _get(f"{API}/doc/{tid}/", token)
                except Exception as e:
                    print("doc failed:", tid, e); continue
                url = f"https://indiankanoon.org/doc/{tid}/"
                for s, cat in extract_candidates(d.get("doc", "")):
                    if s.lower() in seen:
                        continue
                    seen.add(s.lower())
                    rows.append({"text": s, "label": "", "category_hint": cat, "source_url": url,
                                 "doc_title": d.get("title", ""), "query": q})
                time.sleep(args.sleep)
    DATA.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["text", "label", "category_hint", "source_url", "doc_title", "query"])
        w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} candidate sentences -> {out_path}  (label them: 1 threat/coercion, 0 neutral-legal/distress)")


def merge(args):
    import pandas as pd
    parts = []
    syn = pd.read_csv(DATA / "threat_dataset_v7.csv")
    syn["source"] = syn.get("source", "synthetic_v7")
    parts.append(syn[["text", "label", "category", "language", "source"]])
    dis = pd.read_csv(DATA / "distress_dataset_v3.csv")
    dis = dis[dis["label"] > 0].assign(label=0, category="generic_distress", source="distress_v3_negatives")
    parts.append(dis[["text", "label", "category", "language", "source"]])
    if args.labelled and os.path.exists(args.labelled):
        lab = pd.read_csv(args.labelled)
        lab = lab[lab["label"].isin([0, 1, "0", "1"])].copy()
        lab["label"] = lab["label"].astype(int)
        lab["category"] = lab.get("category_hint", "kanoon")
        lab["language"] = "english"
        lab["source"] = "indian_kanoon"
        parts.append(lab[["text", "label", "category", "language", "source"]])
    df = pd.concat(parts, ignore_index=True).drop_duplicates("text").sample(frac=1, random_state=42)
    out = DATA / "threat_corpus_v8.csv"
    df.to_csv(out, index=False)
    print(f"{len(df)} rows -> {out}\n", df["source"].value_counts().to_string(), "\n", df["label"].value_counts().to_string())
    print("target >= 2500 rows:", "OK" if len(df) >= 2500 else f"short by {2500 - len(df)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scrape"); s.add_argument("--pages", type=int, default=3); s.add_argument("--sleep", type=float, default=1.0)
    s.add_argument("--dry-run", action="store_true")
    m = sub.add_parser("merge"); m.add_argument("--labelled", default=str(DATA / "kanoon_labelled.csv"))
    a = ap.parse_args()
    (scrape if a.cmd == "scrape" else merge)(a)
