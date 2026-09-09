"""
Threat / intimidation corpus builder  (services/scoring/corpus/threat_corpus_builder.py)

The longest-lead item of the perception track: a labelled corpus that separates
"I'm being threatened / coerced" from "I'm scared / sad / stressed about the case".

Pipeline
  1. COLLECT   scrape    Indian Kanoon API -> candidate sentences next to coercion cues, one CSV row each
                         (needs IK_API_TOKEN; --dry-run parses a bundled example offline and writes nothing)
  2. LABEL     (manual)  open training/data/kanoon_candidates.csv, fill `label` (1 threat/coercion, 0 not)
                         and optionally `category` from the taxonomy below -> training/data/kanoon_labelled.csv
  3. VALIDATE  validate  check a labelled CSV before it is merged (labels 0/1, known categories, no empties)
  4. MERGE     merge     synthetic threat V7 (520 rows, generators in this folder) + distress-V3 negatives
                         + labelled Kanoon rows -> training/data/threat_corpus_v8.csv, categories normalised
  5. AUDIT     stats     category coverage of any corpus CSV against the required taxonomy (gaps are printed)

Nothing here fabricates data: `scrape` writes only what the API returned, `--dry-run` writes nothing,
and `merge` only combines files that exist on disk (ILDC is NOT wired in yet; see stats output).

Usage
  export IK_API_TOKEN=...                                    # never commit it
  PYTHONPATH=. python corpus/threat_corpus_builder.py scrape --pages 5
  PYTHONPATH=. python corpus/threat_corpus_builder.py scrape --dry-run
  PYTHONPATH=. python corpus/threat_corpus_builder.py validate --labelled training/data/kanoon_labelled.csv
  PYTHONPATH=. python corpus/threat_corpus_builder.py merge  [--labelled training/data/kanoon_labelled.csv]
  PYTHONPATH=. python corpus/threat_corpus_builder.py stats  [--csv training/data/threat_dataset_v7.csv]
"""
import argparse
import csv
import html
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # services/scoring
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

# ---------------------------------------------------------------- canonical taxonomy
# canonical category -> (label, what it means)
TAXONOMY = {
    # threat / coercion  (label 1)
    "direct_threat":               (1, "explicit harm stated to the speaker"),
    "indirect_threat":             (1, "veiled / implied consequence, no explicit act"),
    "witness_intimidation":        (1, "pressure not to testify / to change a statement"),
    "forced_silence":              (1, "told to keep quiet, forget, not tell anyone"),
    "financial_coercion":          (1, "livelihood, wages, land, ration used as leverage"),
    "third_party_threat":          (1, "harm threatened against family / others close to the speaker"),
    "case_withdrawal_coercion":    (1, "pressure to withdraw / compromise / settle the complaint"),
    # hard negatives  (label 0)
    "fear_without_threat":         (0, "fear or anxiety with nobody threatening"),
    "sadness_without_threat":      (0, "sadness, hopelessness, generic distress"),
    "anger_without_threat":        (0, "anger / frustration, no coercion"),
    "legal_stress_without_threat": (0, "stress about hearings, paperwork, delays"),
    "negation":                    (0, "explicit denial of being threatened"),
    "third_party_statement":       (0, "report about someone else that is not a threat to the speaker"),
    "benign_advice":               (0, "advice / suggestion that is not coercive"),
    "ambiguous":                   (0, "context-dependent wording; non-threat by labelling policy"),
    "neutral_legal":               (0, "procedural or narrative legal text"),
    "hard_negative":               (0, "threat-like vocabulary with a non-threat meaning"),
}
REQUIRED = list(TAXONOMY)

# legacy category names used by the V5/V6/V7 generators and the challenge sets -> canonical
LEGACY = {
    "physical_threat": "direct_threat", "targeted_threat": "direct_threat", "hinglish_threat": "direct_threat",
    "clear_direct_threats": "direct_threat",
    "indirect_threat": "indirect_threat", "hinglish_indirect": "indirect_threat", "indirect_implied_threats": "indirect_threat",
    "witness_intimidation": "witness_intimidation",
    "forced_silence": "forced_silence",
    "financial_coercion": "financial_coercion", "financial_employment_coercion": "financial_coercion",
    "family_threat": "third_party_threat", "family_social_pressure": "third_party_threat",
    "case_withdrawal": "case_withdrawal_coercion",
    "fear": "fear_without_threat", "fear_without_threat": "fear_without_threat",
    "hinglish_fear": "fear_without_threat", "fear_without_an_actual_threat": "fear_without_threat",
    "sadness": "sadness_without_threat", "hopelessness": "sadness_without_threat",
    "general_distress": "sadness_without_threat", "generic_distress": "sadness_without_threat",
    "anger_distress_without_threat": "sadness_without_threat",
    "anger": "anger_without_threat",
    "legal_stress": "legal_stress_without_threat",
    "negation": "negation", "hinglish_negation": "negation", "case_negation": "negation",
    "explicit_denial_of_being_threatened": "negation",
    "non_threat_advice": "benign_advice",
    "ambiguous_non_threat": "ambiguous", "ambiguous_context_dependent": "ambiguous",
    "hard_negative": "hard_negative", "hinglish": "hard_negative",
    "kanoon": "neutral_legal",
}


# legacy names whose meaning depends on the row's label: threat *to* the speaker vs. report *about* others
LABEL_DEPENDENT = {
    "other_person_threat": {1: "third_party_threat", 0: "third_party_statement"},
    "mention_of_threats_to_other_people": {1: "third_party_threat", 0: "third_party_statement"},
    "third_party_threat": {1: "third_party_threat", 0: "third_party_statement"},
}


def canonical(category, label=None):
    """Map any legacy/generator category name onto the canonical taxonomy.

    `label` disambiguates names that mean different things per label (see LABEL_DEPENDENT):
    "they threatened my brother if I testify" (1) vs "I heard another family was threatened" (0).
    """
    c = str(category or "").strip().lower()
    if not c:
        return "uncategorised"
    if c in LABEL_DEPENDENT and label is not None:
        try:
            return LABEL_DEPENDENT[c][int(label)]
        except (ValueError, TypeError, KeyError):
            pass
    return LEGACY.get(c, c)


def canonical_series(df):
    """Vectorised canonical() over a dataframe with `category` and `label` columns."""
    return [canonical(c, l) for c, l in zip(df["category"], df["label"])]


# ---------------------------------------------------------------- 1. collect
CUES = {
    "direct_threat": r"\b(kill|beat|assault|burn|hurt|eliminate|dire consequences|finish (him|her|you))\b",
    "case_withdrawal_coercion": r"\b(withdraw|compromise|settle|take back) (the |her |his |their )?(complaint|case|fir|statement)\b",
    "forced_silence": r"\b(not to (depose|speak|disclose|tell)|keep (quiet|silent|mum)|remain silent)\b",
    "witness_intimidation": r"\b(hostile|intimidat|pressuri[sz]ed|coerc|threaten)\w*\b",
    "financial_coercion": r"\b(livelihood|wages|employment|land|ration|boycott|money)\b.*\b(threat|stop|deny|deprive)\w*",
    "third_party_threat": r"\b(family|wife|husband|children|daughter|son|parents)\b.*\b(threat|harm|kill|abduct)\w*",
}


def strip_html(text):
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", text) if 25 <= len(s.strip()) <= 400]


def extract_candidates(text, min_cues=1):
    """[(sentence, category_hint)] for sentences carrying at least `min_cues` coercion cue(s)."""
    out = []
    for s in sentences(strip_html(text)):
        hits = [cat for cat, rx in CUES.items() if re.search(rx, s, flags=re.I)]
        if len(hits) >= min_cues:
            out.append((s, "|".join(hits)))
    return out


def _api(url, token, **params):
    import httpx
    r = httpx.post(url, headers={"Authorization": f"Token {token}", "Accept": "application/json"},
                   data=params, timeout=30)
    r.raise_for_status()
    return r.json()


DRY_RUN_SAMPLE = ("<p>The complainant stated that the accused threatened to kill her if she deposed before the "
                  "court. The learned counsel for the appellant argued that Section 3(1)(r) is not attracted. "
                  "PW-4 turned hostile after being pressurised to compromise the case. The family of the victim "
                  "was told that their children would be harmed if the FIR was not withdrawn.</p>")


def scrape(args):
    if args.dry_run:
        print("dry run: parsing a bundled illustrative paragraph (NOT scraped data, nothing is written)\n")
        for s, cat in extract_candidates(DRY_RUN_SAMPLE):
            print(f"  [{cat}] {s}")
        return
    token = os.environ.get("IK_API_TOKEN")
    if not token:
        sys.exit("set IK_API_TOKEN (https://api.indiankanoon.org) or use --dry-run")
    out_path = Path(args.out)
    seen, rows = set(), []
    if out_path.exists():                                  # resume: keep what was already collected
        with open(out_path, newline="") as f:
            for r in csv.DictReader(f):
                seen.add(r["text"].lower()); rows.append(r)
    for q in QUERIES:
        for page in range(args.pages):
            try:
                res = _api(f"{API}/search/", token, formInput=q, pagenum=page)
            except Exception as e:
                print("search failed:", q, page, e); break
            for doc in res.get("docs", []):
                tid = doc.get("tid")
                try:
                    d = _api(f"{API}/doc/{tid}/", token)
                except Exception as e:
                    print("doc failed:", tid, e); continue
                url = f"https://indiankanoon.org/doc/{tid}/"
                for s, cat in extract_candidates(d.get("doc", "")):
                    if s.lower() in seen:
                        continue
                    seen.add(s.lower())
                    rows.append({"text": s, "label": "", "category": "", "category_hint": cat, "source_url": url,
                                 "doc_title": d.get("title", ""), "query": q})
                time.sleep(args.sleep)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["text", "label", "category", "category_hint", "source_url", "doc_title", "query"])
        w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} candidate sentences -> {out_path}")
    print("next: fill `label` (1 threat/coercion, 0 not) and optionally `category`, save as kanoon_labelled.csv, then `validate`")


# ---------------------------------------------------------------- 3. validate
def validate(args):
    import pandas as pd
    path = Path(args.labelled)
    if not path.exists():
        sys.exit(f"{path} not found")
    df = pd.read_csv(path)
    problems = []
    for col in ("text", "label"):
        if col not in df.columns:
            problems.append(f"missing column: {col}")
    if problems:
        sys.exit("\n".join(problems))
    empty = df["label"].isna() | (df["label"].astype(str).str.strip() == "")
    bad = ~df["label"].astype(str).str.strip().isin(["0", "1"]) & ~empty
    dupes = df["text"].str.lower().duplicated().sum()
    print(f"{path}: {len(df)} rows | labelled {int((~empty).sum())} | unlabelled {int(empty.sum())} | "
          f"bad labels {int(bad.sum())} | duplicate texts {int(dupes)}")
    if "category" in df.columns:
        unknown = sorted({canonical(r.get("category"), r.get("label")) for _, r in df.iterrows()
                          if str(r.get("category") or "").strip()} - set(TAXONOMY))
        if unknown:
            problems.append(f"unknown categories (use the taxonomy): {unknown}")
        mism = 0
        for _, r in df[~empty & ~bad].iterrows():
            cat = canonical(r.get("category"), r["label"])
            if cat in TAXONOMY and TAXONOMY[cat][0] != int(r["label"]):
                mism += 1
        if mism:
            problems.append(f"{mism} rows whose category implies a different label than the one given")
    if int(bad.sum()):
        problems.append("labels must be 0 or 1")
    if problems:
        print("PROBLEMS:\n  " + "\n  ".join(problems)); sys.exit(1)
    print("OK: ready to merge")


# ---------------------------------------------------------------- 4. merge
def _load_synthetic():
    import pandas as pd
    parts = []
    syn = pd.read_csv(DATA / "threat_dataset_v7.csv")
    if "source" not in syn.columns:
        syn["source"] = "synthetic_v7"
    parts.append(syn[["text", "label", "category", "language", "source"]])
    dis_path = DATA / "distress_dataset_v3.csv"
    if dis_path.exists():
        dis = pd.read_csv(dis_path)
        dis = dis[dis["label"] > 0].assign(label=0, category="sadness_without_threat", source="distress_v3_negatives")
        parts.append(dis[["text", "label", "category", "language", "source"]])
    return parts


def merge(args):
    import pandas as pd
    parts = _load_synthetic()
    if args.labelled and os.path.exists(args.labelled):
        lab = pd.read_csv(args.labelled)
        lab = lab[lab["label"].astype(str).str.strip().isin(["0", "1"])].copy()
        lab["label"] = lab["label"].astype(int)
        cat = lab["category"] if "category" in lab.columns else pd.Series([None] * len(lab))
        hint = lab["category_hint"] if "category_hint" in lab.columns else pd.Series([None] * len(lab))
        lab["category"] = [c if isinstance(c, str) and c else (str(h).split("|")[0] if isinstance(h, str) and h else "neutral_legal")
                           for c, h in zip(cat, hint)]
        lab["category"] = canonical_series(lab)
        lab["language"] = lab.get("language", "english")
        lab["source"] = "indian_kanoon"
        parts.append(lab[["text", "label", "category", "language", "source"]])
        print(f"included {len(lab)} labelled Indian Kanoon rows from {args.labelled}")
    else:
        print("no labelled Kanoon file found -> corpus = synthetic + distress negatives only")
    df = pd.concat(parts, ignore_index=True)
    df["category"] = canonical_series(df)
    df = df.drop_duplicates("text").sample(frac=1, random_state=42).reset_index(drop=True)
    implied = df["category"].map(lambda c: TAXONOMY.get(c, (None,))[0])
    mism = df[implied.notna() & (implied != df["label"])]
    if len(mism):
        print(f"WARNING: {len(mism)} rows whose category implies another label (kept, review them):")
        print(mism[["text", "label", "category", "source"]].head(10).to_string(index=False))
    out = Path(args.out)
    df.to_csv(out, index=False)
    print(f"\n{len(df)} rows -> {out}")
    print(df["source"].value_counts().to_string()); print(df["label"].value_counts().to_string())
    print("target >= 2500 rows:", "OK" if len(df) >= 2500 else f"short by {2500 - len(df)}")
    _coverage(df)


# ---------------------------------------------------------------- 5. stats
def _coverage(df):
    import pandas as pd
    counts = pd.Series(canonical_series(df)).value_counts()
    print("\ncategory coverage (canonical taxonomy):")
    print(f"  {'category':30s} {'label':5s} {'rows':>5s}")
    gaps = []
    for cat in REQUIRED:
        n = int(counts.get(cat, 0))
        print(f"  {cat:30s} {TAXONOMY[cat][0]:<5d} {n:5d}" + ("   <- GAP" if n == 0 else ""))
        if n == 0:
            gaps.append(cat)
    unknown = sorted(set(counts.index) - set(REQUIRED))
    if unknown:
        print("  unmapped categories:", {u: int(counts[u]) for u in unknown})
    if gaps:
        print(f"\nGAPS (no rows yet): {gaps}  -> write/collect examples before claiming coverage")


def stats(args):
    import pandas as pd
    df = pd.read_csv(args.csv)
    print(f"{args.csv}: {len(df)} rows; labels {df['label'].value_counts().to_dict()}"
          + (f"; languages {df['language'].value_counts().to_dict()}" if "language" in df.columns else ""))
    _coverage(df)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scrape", help="Indian Kanoon -> candidate sentences for labelling (IK_API_TOKEN)")
    s.add_argument("--pages", type=int, default=3); s.add_argument("--sleep", type=float, default=1.0)
    s.add_argument("--dry-run", action="store_true"); s.add_argument("--out", default=str(DATA / "kanoon_candidates.csv"))
    v = sub.add_parser("validate", help="check a labelled CSV before merging")
    v.add_argument("--labelled", default=str(DATA / "kanoon_labelled.csv"))
    m = sub.add_parser("merge", help="synthetic + distress negatives + labelled Kanoon -> threat_corpus_v8.csv")
    m.add_argument("--labelled", default=str(DATA / "kanoon_labelled.csv"))
    m.add_argument("--out", default=str(DATA / "threat_corpus_v8.csv"))
    st = sub.add_parser("stats", help="taxonomy coverage of a corpus CSV")
    st.add_argument("--csv", default=str(DATA / "threat_dataset_v7.csv"))
    a = ap.parse_args()
    {"scrape": scrape, "validate": validate, "merge": merge, "stats": stats}[a.cmd](a)
