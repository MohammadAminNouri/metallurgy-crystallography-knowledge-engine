from __future__ import annotations
import pandas as pd
from itertools import product

CORE_COMBINATIONS = [
    ("NiTi shape memory alloys", "EBSD / TKD orientation microscopy", "variant selection and texture"),
    ("NiTi shape memory alloys", "transformation matrices and symmetry", "martensitic transformations"),
    ("martensitic and bainitic steels", "EBSD / TKD orientation microscopy", "martensitic transformations"),
    ("magnesium alloys", "twinning and weak twins", "deformation and mechanical testing"),
    ("aluminum 6xxx and Al-Mg-Si-Cu", "precipitation and ordering", "TEM / STEM / HRTEM"),
    ("Ti and Ti-6Al-4V alloys", "additive manufacturing process", "martensitic transformations"),
    ("316L stainless steel and CuCrZr multi-materials", "additive manufacturing process", "recrystallization and grain evolution"),
    ("gold alloys and ordered Au-Cu/Au-Ti", "precipitation and ordering", "variant selection and texture"),
    ("copper alloys", "precipitation and ordering", "mechanical behavior"),
]

FUTURE_GAPS = [
    {
        "gap": "LPBF NiTi variant-map engine",
        "logic": "He repeatedly connects NiTi, martensite variants, EBSD/TKD and correspondence theory; LPBF-NiTi would extend that crystallographic machinery into process-designed SMA microstructures.",
        "needs": ["NiTi shape memory alloys", "additive manufacturing process", "EBSD / TKD orientation microscopy", "transformation matrices and symmetry"],
        "outputs": "Parent B2 reconstruction, B19′ variant census, texture-memory map, process→variant→superelasticity link."
    },
    {
        "gap": "Weak-twin classifier for Mg/steels/NiTi EBSD data",
        "logic": "Weak twins and unconventional twins are a recurring theoretical theme; coding can turn this into a detector over orientation pairs.",
        "needs": ["twinning and weak twins", "EBSD / TKD orientation microscopy", "magnesium alloys", "martensitic and bainitic steels"],
        "outputs": "Misorientation clusters, twin family labels, weak-twin candidates, boundary confidence score."
    },
    {
        "gap": "Al-Mg-Si precipitate-boundary interaction graph",
        "logic": "Recent Al-Mg-Si work asks how precipitates interact with particles and boundaries; graph analytics can map precipitate sites, boundary type and nucleation conditions.",
        "needs": ["aluminum 6xxx and Al-Mg-Si-Cu", "precipitation and ordering", "EBSD / TKD orientation microscopy", "TEM / STEM / HRTEM"],
        "outputs": "Boundary-particle-precipitate network, β-Mg2Si nucleation sensitivity, heat-treatment design map."
    },
    {
        "gap": "LPBF thermal history → phase stability map for 316L/CuCrZr/Ti-6Al-4V",
        "logic": "His recent AM work links laser beam shaping, phase stabilization, recrystallization and mechanical response; coding can formalize this as a process-microstructure-property engine.",
        "needs": ["additive manufacturing process", "316L stainless steel and CuCrZr multi-materials", "Ti and Ti-6Al-4V alloys", "XRD / synchrotron diffraction"],
        "outputs": "Cooling-rate proxy, BCC/α′/recrystallization map, mechanical-property interpretation."
    },
    {
        "gap": "Automated lath/block/packet reconstruction in steels",
        "logic": "His steel papers repeatedly study lath martensite morphology, packets, blocks and variant selection; EBSD reconstruction code would directly continue that theme.",
        "needs": ["martensitic and bainitic steels", "variant selection and texture", "EBSD / TKD orientation microscopy"],
        "outputs": "Austenite parent reconstruction, packet/block labeling, K–S/N–W relation score, toughness-relevant structure map."
    }
]


def has_label(row, column, label):
    return label.lower() in str(row.get(column, "")).lower()


def combination_counts(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for alloy, method, mechanism in CORE_COMBINATIONS:
        mask = df.apply(lambda r: has_label(r, "alloy_systems", alloy) and has_label(r, "methods", method) and has_label(r, "mechanisms", mechanism), axis=1)
        rows.append({"alloy_system": alloy, "method": method, "mechanism": mechanism, "count": int(mask.sum())})
    return pd.DataFrame(rows).sort_values("count", ascending=False)


def suggest_gaps(df: pd.DataFrame) -> pd.DataFrame:
    enriched = []
    all_text = " ".join(df.get(c, pd.Series(dtype=str)).astype(str).str.cat(sep=" ") for c in ["alloy_systems", "methods", "mechanisms", "title"] if c in df)
    for g in FUTURE_GAPS:
        evidence = []
        for need in g["needs"]:
            count = all_text.lower().count(need.lower())
            if count:
                evidence.append(f"{need} ({count})")
        enriched.append({**g, "evidence_in_seed_dataset": "; ".join(evidence), "coverage_score": len(evidence)})
    return pd.DataFrame(enriched).sort_values(["coverage_score", "gap"], ascending=[False, True])
