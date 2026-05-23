from pathlib import Path
import json
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TAXONOMY_PATH = ROOT / "data" / "metallurgy_taxonomy.json"


FALLBACK_TAXONOMY = {
    "alloy_systems": {
        "NiTi shape memory alloys": [
            "NiTi", "nickel titanium", "shape memory", "superelastic",
            "B2", "B19", "B19′", "B19'"
        ],
        "steels and Fe alloys": [
            "steel", "stainless", "316L", "ferritic", "martensitic steel",
            "bainitic", "weld metal", "Fe-", "iron"
        ],
        "magnesium alloys": [
            "magnesium", "Mg alloy", "Mg-", "hcp"
        ],
        "aluminum alloys": [
            "aluminum", "aluminium", "Al-Mg-Si", "6014", "Al alloy"
        ],
        "copper alloys": [
            "Cu-Ti", "copper", "CuCrZr", "Cu alloy"
        ],
        "titanium alloys": [
            "Ti-6Al-4V", "Ti alloy", "titanium", "beta titanium"
        ],
        "gold alloys": [
            "gold", "red gold", "Au-Cu", "Au-Ti", "18 carat"
        ],
        "high entropy alloys": [
            "high entropy alloy", "HEA"
        ],
    },
    "methods": {
        "EBSD / TKD orientation microscopy": [
            "EBSD", "electron backscatter diffraction", "TKD",
            "transmission kikuchi diffraction", "orientation map",
            "IPF", "pole figure", "misorientation"
        ],
        "TEM / STEM microscopy": [
            "TEM", "transmission electron microscopy", "STEM", "HRTEM",
            "SAED", "lamella"
        ],
        "SEM microscopy": [
            "SEM", "FESEM", "BSE", "back-scattered", "secondary electron"
        ],
        "XRD / synchrotron diffraction": [
            "XRD", "x-ray diffraction", "synchrotron", "diffraction"
        ],
        "additive manufacturing / LPBF process": [
            "LPBF", "laser powder bed fusion", "additive manufacturing",
            "3D printed", "beam shaping", "melt pool"
        ],
        "thermomechanical processing": [
            "rolling", "bending", "compression", "extrusion",
            "heat treatment", "age hardening", "annealing",
            "shock peening", "welding", "creep", "HIP"
        ],
    },
    "mechanisms": {
        "martensitic transformations": [
            "martensite", "martensitic", "B2-B19", "B2 → B19",
            "B2→B19", "austenite", "habit plane", "PTMC",
            "displacive transformation", "variant selection"
        ],
        "twinning and weak twins": [
            "twin", "twins", "twinning", "weak twin", "axial weak twin",
            "heterotwin", "type I twin", "type II twin",
            "simple shear", "invariant plane"
        ],
        "transformation matrices and symmetry": [
            "correspondence", "correspondence matrix", "distortion matrix",
            "orientation relationship", "symmetry", "matrix",
            "group theory", "lattice reduction", "Bézout", "Bézout"
        ],
        "precipitation and ordering": [
            "precipitation", "precipitate", "Mg2Si", "β-Mg2Si",
            "ordering", "L10", "A1", "age-hardening", "nucleation"
        ],
        "recrystallization and grain evolution": [
            "recrystallization", "grain", "grain boundary",
            "parent grain", "grain fragmentation", "texture evolution"
        ],
        "mechanical behavior": [
            "mechanical properties", "strength", "toughness", "ductility",
            "hardness", "superelastic", "creep", "formability",
            "deformation", "fatigue"
        ],
    },
    "properties": {
        "texture and orientation": [
            "texture", "orientation", "variant", "pole figure",
            "misorientation", "parent reconstruction"
        ],
        "strength and hardness": [
            "strength", "hardness", "yield", "mechanical properties"
        ],
        "functional response": [
            "shape memory", "superelastic", "transformation temperature",
            "recoverable strain"
        ],
        "toughness and fracture": [
            "toughness", "fracture", "crack", "impact"
        ],
    },
}


def load_taxonomy(path=DEFAULT_TAXONOMY_PATH):
    """
    Load metallurgy taxonomy from data/metallurgy_taxonomy.json.
    If the JSON file is missing or broken, use a safe built-in fallback.
    """
    path = Path(path)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return FALLBACK_TAXONOMY
    return FALLBACK_TAXONOMY


def normalize_text(text):
    """
    Normalize unicode hyphens/arrows/apostrophes for more stable keyword matching.
    """
    return (
        str(text or "")
        .replace("–", "-")
        .replace("—", "-")
        .replace("‐", "-")
        .replace("-", "-")
        .replace("→", "->")
        .replace("′", "'")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )


def keyword_hits(text, keywords):
    """
    Return keyword score and matched keywords for one text block.
    """
    t = normalize_text(text).lower()
    hits = []
    score = 0

    for kw in keywords:
        k = normalize_text(kw).strip()
        if not k:
            continue

        kl = k.lower()

        # Short acronyms like Mg, Al, Ti need word boundaries.
        if len(kl) <= 3 and kl.replace("-", "").isalnum():
            pattern = r"(?<![A-Za-z0-9])" + re.escape(kl) + r"(?![A-Za-z0-9])"
            found = re.search(pattern, t) is not None
        else:
            found = kl in t

        if found:
            hits.append(k)
            if " " in k or "-" in k or "->" in k:
                score += 2
            else:
                score += 1

    hits = sorted(set(hits), key=lambda x: (len(x), x.lower()))
    return score, hits


def classify_record(record, taxonomy=None):
    """
    Classify one publication record into alloy systems, methods, mechanisms,
    and properties using the metallurgy taxonomy.
    """
    taxonomy = taxonomy or load_taxonomy()

    text = " ".join(
        str(record.get(k, ""))
        for k in ["title", "abstract", "venue", "authors", "keywords"]
    )

    out = {}
    details = {}

    for family, labels in taxonomy.items():
        found_labels = []
        family_details = {}

        for label, keywords in labels.items():
            score, hits = keyword_hits(text, keywords)
            if score > 0:
                found_labels.append(label)
                family_details[label] = hits

        out[family] = found_labels
        details[family] = family_details

    priority = [
        ("mechanisms", "martensitic transformations"),
        ("mechanisms", "twinning and weak twins"),
        ("mechanisms", "transformation matrices and symmetry"),
        ("methods", "additive manufacturing / LPBF process"),
        ("mechanisms", "precipitation and ordering"),
        ("mechanisms", "recrystallization and grain evolution"),
        ("methods", "EBSD / TKD orientation microscopy"),
        ("mechanisms", "mechanical behavior"),
    ]

    focus = "general metallurgy / microstructure"
    for family, label in priority:
        if label in out.get(family, []):
            focus = label
            break

    out["focus_label"] = focus
    out["hit_details"] = details
    return out


def enrich_dataframe(df, taxonomy=None):
    """
    Add classification columns to a publication dataframe.
    Expected columns: title, abstract, year, authors, venue.
    Missing columns are handled safely.
    """
    taxonomy = taxonomy or load_taxonomy()

    if df is None or df.empty:
        return pd.DataFrame()

    working = df.copy().fillna("")

    if "record_id" not in working.columns:
        working.insert(0, "record_id", [f"R{i+1:04d}" for i in range(len(working))])

    for col in ["title", "abstract", "year", "authors", "venue", "source"]:
        if col not in working.columns:
            working[col] = ""

    rows = []

    for _, row in working.iterrows():
        rec = row.to_dict()
        cls = classify_record(rec, taxonomy)
        new = rec.copy()

        for key, value in cls.items():
            if key == "hit_details":
                new[key] = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, list):
                new[key] = "; ".join(value)
            else:
                new[key] = value

        rows.append(new)

    out = pd.DataFrame(rows).fillna("")

    if "year" in out.columns:
        out["year_num"] = pd.to_numeric(out["year"], errors="coerce")

    return out


def explode_labels(df, column):
    """
    Explode a semicolon-separated label column.
    """
    if df is None or df.empty or column not in df.columns:
        return pd.DataFrame(columns=[column, "record_id", "title"])

    x = df[["record_id", "title", column]].copy()
    x[column] = x[column].fillna("").astype(str).str.split(";")
    x = x.explode(column)
    x[column] = x[column].astype(str).str.strip()
    return x[x[column] != ""]


def coverage_counts(df, columns):
    """
    Count detected taxonomy labels across selected classification columns.
    """
    rows = []

    for col in columns:
        ex = explode_labels(df, col)

        if ex.empty:
            continue

        counts = ex[col].value_counts().reset_index()
        counts.columns = ["label", "count"]
        counts.insert(0, "family", col)
        rows.append(counts)

    if rows:
        return pd.concat(rows, ignore_index=True)

    return pd.DataFrame(columns=["family", "label", "count"])
