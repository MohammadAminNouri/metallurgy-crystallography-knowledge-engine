from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Tuple
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = ROOT / "data" / "metallurgy_taxonomy.json"


def load_taxonomy(path: str | Path = TAXONOMY_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _hit_score(text: str, keywords: List[str]) -> Tuple[int, List[str]]:
    """Keyword score with metallurgical token boundaries.

    Avoids false hits such as SiC inside "classical" while still matching
    hyphenated alloy names and phrases.
    """
    hits = []
    score = 0
    for kw in keywords:
        k = str(kw).strip()
        if not k:
            continue
        if " " in k:
            found = k.lower() in text.lower()
        else:
            pattern = r"(?<![A-Za-z0-9])" + re.escape(k) + r"(?![A-Za-z0-9])"
            found = re.search(pattern, text, flags=re.IGNORECASE) is not None
        if found:
            hits.append(kw)
            score += 2 if len(k.split()) > 1 else 1
    return score, sorted(set(hits), key=lambda x: x.lower())


def classify_record(row: pd.Series, taxonomy: dict | None = None) -> dict:
    taxonomy = taxonomy or load_taxonomy()
    text = " ".join(str(row.get(c, "")) for c in ["title", "abstract", "venue", "authors"])
    result = {}
    total_score = 0
    metallurgical_hits = []
    for section in ["mechanisms", "alloy_systems", "methods"]:
        matches = []
        hit_terms = []
        for label, kws in taxonomy[section].items():
            score, hits = _hit_score(text, kws)
            if score:
                matches.append(label)
                hit_terms += hits
                total_score += score
        result[section] = "; ".join(sorted(set(matches)))
        result[f"{section}_hits"] = "; ".join(sorted(set(hit_terms), key=lambda x: x.lower()))
        metallurgical_hits += hit_terms

    # focus score: Cayron core = martensite/twinning/variant/EBSD + metallurgy alloy/process methods
    core_keywords = taxonomy["source_focus"]["core metallurgy"]
    adjacent_keywords = taxonomy["source_focus"]["adjacent microstructure/materials"]
    core_score, core_hits = _hit_score(text, core_keywords)
    adjacent_score, adjacent_hits = _hit_score(text, adjacent_keywords)
    result["core_metallurgy_score"] = int(core_score * 2 + total_score - adjacent_score)
    result["adjacent_materials_score"] = int(adjacent_score)
    result["focus_label"] = "Core metallurgy" if result["core_metallurgy_score"] >= 5 else ("Adjacent microstructure/materials" if adjacent_score else "Peripheral/unclear")
    result["core_hits"] = "; ".join(core_hits)
    result["adjacent_hits"] = "; ".join(adjacent_hits)
    return result


def enrich_dataframe(df: pd.DataFrame, taxonomy: dict | None = None) -> pd.DataFrame:
    taxonomy = taxonomy or load_taxonomy()
    if df.empty:
        return df
    enriched = []
    for _, row in df.iterrows():
        d = row.to_dict()
        d.update(classify_record(row, taxonomy))
        enriched.append(d)
    out = pd.DataFrame(enriched)
    if "year" in out.columns:
        out["year_num"] = pd.to_numeric(out["year"], errors="coerce")
    return out


def explode_labels(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if column not in df.columns or df.empty:
        return pd.DataFrame(columns=[column, "count"])
    rows = []
    for _, r in df.iterrows():
        for label in str(r.get(column, "")).split(";"):
            label = label.strip()
            if label:
                rows.append({column: label, "title": r.get("title", ""), "year": r.get("year", "")})
    return pd.DataFrame(rows)
