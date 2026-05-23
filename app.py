from pathlib import Path
import json
import re

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Metallurgy Crystallography Knowledge Engine",
    page_icon="🔬",
    layout="wide",
)


ROOT = Path(__file__).resolve().parent
DATA_PATHS = [
    ROOT / "data" / "publications_context.csv",
    ROOT / "data" / "publications_seed.csv",
    ROOT / "data" / "cayron_publications_context.csv",
]


TAXONOMY = {
    "alloy_systems": {
        "NiTi shape memory alloys": [
            "NiTi", "nickel titanium", "shape memory", "superelastic",
            "B2", "B19", "B19′", "B19'"
        ],
        "steels and Fe alloys": [
            "steel", "stainless", "316L", "ferritic", "martensitic steel",
            "bainitic", "weld metal", "Fe-", "iron", "austenite"
        ],
        "magnesium alloys": [
            "magnesium", "Mg alloy", "Mg-", "hcp"
        ],
        "aluminum alloys": [
            "aluminum", "aluminium", "Al-Mg-Si", "6014", "Al alloy", "Mg2Si"
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


FALLBACK_RECORDS = [
    {
        "year": 2026,
        "title": "Compatibilities and supercompatibility conditions in shape memory alloys determined from correspondence, metrics and symmetries",
        "venue": "Preprint",
        "abstract": "Martensite crystallography, PTMC, habit planes, transformation twins, correspondence, metrics and symmetries in shape memory alloys.",
        "source": "fallback",
    },
    {
        "year": 2024,
        "title": "Hard-sphere model of the B2 to B19 phase transformation and application to NiTi alloys",
        "venue": "Acta Materialia",
        "abstract": "B2 to B19 prime martensitic transformation, NiTi, crystallography, hard-sphere model and orientation relationship.",
        "source": "fallback",
    },
    {
        "year": 2023,
        "title": "EBSD study of variant reorientation, texture, and twin formation in a martensitic NiTi alloy deformed in compression",
        "venue": "Acta Materialia",
        "abstract": "EBSD analysis of martensitic NiTi, variant reorientation, texture evolution, twin formation and deformation.",
        "source": "fallback",
    },
    {
        "year": 2022,
        "title": "The correspondence theory and its application to NiTi shape memory alloys",
        "venue": "Crystals",
        "abstract": "Correspondence theory, martensite crystallography, variants, symmetries, metrics and NiTi shape memory alloys.",
        "source": "fallback",
    },
    {
        "year": 2022,
        "title": "The concept of axial weak twins",
        "venue": "Acta Materialia",
        "abstract": "Weak twins, axial weak twins, twinning crystallography, invariant plane and twin interfaces.",
        "source": "fallback",
    },
    {
        "year": 2025,
        "title": "Toward architected microstructures using advanced laser beam shaping in laser powder bed fusion of Ti-6Al-4V",
        "venue": "Advanced Functional Materials",
        "abstract": "LPBF, Ti-6Al-4V, beam shaping, thermal gradients, martensitic structure, texture and microstructure control.",
        "source": "fallback",
    },
    {
        "year": 2025,
        "title": "Formation mechanism and microstructural characteristics of a body-centered cubic phase in 3D printed 316L-CuCrZr multi-material structures",
        "venue": "Scripta Materialia",
        "abstract": "Laser powder bed fusion, 316L, CuCrZr, BCC phase, EBSD, TKD, TEM, microstructure and phase formation.",
        "source": "fallback",
    },
    {
        "year": 2026,
        "title": "Quantitative correlative SEM-EBSD analysis of precipitate-particle and precipitate-boundary interactions in Al-Mg-Si alloys",
        "venue": "Materials Characterization",
        "abstract": "SEM, EBSD, Al-Mg-Si alloys, precipitates, particles, grain boundaries and microstructure evolution.",
        "source": "fallback",
    },
]


def normalize_text(text):
    return (
        str(text or "")
        .replace("–", "-")
        .replace("—", "-")
        .replace("‐", "-")
        .replace("→", "->")
        .replace("′", "'")
        .replace("’", "'")
    )


def keyword_hits(text, keywords):
    t = normalize_text(text).lower()
    hits = []
    score = 0

    for kw in keywords:
        k = normalize_text(kw).strip()
        if not k:
            continue
        kl = k.lower()

        if len(kl) <= 3 and kl.replace("-", "").isalnum():
            pattern = r"(?<![A-Za-z0-9])" + re.escape(kl) + r"(?![A-Za-z0-9])"
            found = re.search(pattern, t) is not None
        else:
            found = kl in t

        if found:
            hits.append(k)
            score += 2 if (" " in k or "-" in k or "->" in k) else 1

    return score, sorted(set(hits), key=lambda x: x.lower())


def classify_record(row):
    text = " ".join(
        str(row.get(k, ""))
        for k in ["title", "abstract", "venue", "authors", "keywords"]
    )

    out = {}

    for family, labels in TAXONOMY.items():
        found = []
        for label, keywords in labels.items():
            score, _ = keyword_hits(text, keywords)
            if score > 0:
                found.append(label)
        out[family] = "; ".join(found)

    focus_priority = [
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
    for fam, label in focus_priority:
        if label in out.get(fam, ""):
            focus = label
            break

    out["focus_label"] = focus
    return out


def load_publications():
    for path in DATA_PATHS:
        if path.exists():
            try:
                df = pd.read_csv(path)
                if not df.empty:
                    return df.fillna("")
            except Exception:
                pass

    return pd.DataFrame(FALLBACK_RECORDS)


def enrich_dataframe(df):
    df = df.copy().fillna("")

    for col in ["year", "title", "authors", "venue", "abstract", "source"]:
        if col not in df.columns:
            df[col] = ""

    if "record_id" not in df.columns:
        df.insert(0, "record_id", [f"R{i+1:04d}" for i in range(len(df))])

    rows = []
    for _, row in df.iterrows():
        rec = row.to_dict()
        rec.update(classify_record(rec))
        rows.append(rec)

    out = pd.DataFrame(rows).fillna("")
    out["year_num"] = pd.to_numeric(out["year"], errors="coerce")
    return out


def split_labels(value):
    return [x.strip() for x in str(value).split(";") if x.strip()]


def coverage_counts(df, columns):
    rows = []
    for col in columns:
        if col not in df.columns:
            continue
        for value in df[col]:
            for label in split_labels(value):
                rows.append({"family": col, "label": label})
    if not rows:
        return pd.DataFrame(columns=["family", "label", "count"])
    x = pd.DataFrame(rows)
    return x.value_counts(["family", "label"]).reset_index(name="count")


def filter_by_label(df, label):
    if label == "All":
        return df
    mask = pd.Series(False, index=df.index)
    for col in ["alloy_systems", "methods", "mechanisms", "properties", "focus_label"]:
        if col in df.columns:
            mask = mask | df[col].astype(str).str.contains(re.escape(label), case=False, na=False)
    return df[mask]


def build_gap_cards(counts):
    def get_count(label):
        row = counts[counts["label"] == label]
        return int(row["count"].iloc[0]) if not row.empty else 0

    return [
        {
            "title": "Process-aware NiTi martensite variant-mapping framework",
            "status": "Future research extension, not a direct completed-work claim.",
            "coverage_score": 4,
            "logic": (
                "The corpus strongly covers NiTi shape-memory alloys, B2→B19′ martensitic "
                "transformation, EBSD/TKD orientation microscopy, martensite variants, texture "
                "evolution, and matrix/correspondence-based crystallography. The gap is to combine "
                "that machinery with process-aware NiTi analysis, especially where additive "
                "manufacturing or thermal history controls parent B2 grains and B19′ variants."
            ),
            "evidence": {
                "NiTi shape memory alloys": get_count("NiTi shape memory alloys"),
                "additive manufacturing / LPBF process": get_count("additive manufacturing / LPBF process"),
                "EBSD / TKD orientation microscopy": get_count("EBSD / TKD orientation microscopy"),
                "transformation matrices and symmetry": get_count("transformation matrices and symmetry"),
            },
            "outputs": [
                "B2 parent reconstruction map",
                "B19′ martensite variant census",
                "variant-pair misorientation histogram",
                "texture-memory map",
                "process→variant→superelasticity link",
            ],
        },
        {
            "title": "Weak-twin detection from EBSD/TKD orientation data",
            "status": "Future software extension based on a repeated crystallography theme.",
            "coverage_score": 5,
            "logic": (
                "Weak twins, axial weak twins, twinning theory, simple-shear limits and symmetry "
                "operators recur strongly. A detector could compare observed EBSD/TKD misorientations "
                "against classical and weak-twin operators."
            ),
            "evidence": {
                "twinning and weak twins": get_count("twinning and weak twins"),
                "EBSD / TKD orientation microscopy": get_count("EBSD / TKD orientation microscopy"),
                "transformation matrices and symmetry": get_count("transformation matrices and symmetry"),
            },
            "outputs": [
                "candidate weak-twin pairs",
                "misorientation-axis tables",
                "classical vs weak-twin comparison",
                "orientation-relation confidence score",
            ],
        },
        {
            "title": "Parent-grain reconstruction for complex martensitic microstructures",
            "status": "Future software extension.",
            "coverage_score": 5,
            "logic": (
                "Martensite, variants, orientation relationships, texture, EBSD/TKD and parent/product "
                "phase crystallography are central. A reusable reconstruction engine would connect "
                "product variants back to parent grains in steels, NiTi and titanium alloys."
            ),
            "evidence": {
                "martensitic transformations": get_count("martensitic transformations"),
                "EBSD / TKD orientation microscopy": get_count("EBSD / TKD orientation microscopy"),
                "texture and orientation": get_count("texture and orientation"),
            },
            "outputs": [
                "prior-parent grain map",
                "variant family map",
                "packet/block-style grouping",
                "orientation relationship fitting report",
            ],
        },
        {
            "title": "Transformation-matrix library for metallurgy",
            "status": "Future reusable code library.",
            "coverage_score": 5,
            "logic": (
                "Distortion matrices, orientation relationship matrices, correspondence matrices, "
                "symmetry operators and lattice reduction are repeated theoretical tools. A clean "
                "Python library would make these operations reusable across transformations."
            ),
            "evidence": {
                "transformation matrices and symmetry": get_count("transformation matrices and symmetry"),
                "martensitic transformations": get_count("martensitic transformations"),
                "twinning and weak twins": get_count("twinning and weak twins"),
            },
            "outputs": [
                "matrix registry",
                "variant enumeration",
                "misorientation calculator",
                "symmetry operator tools",
            ],
        },
        {
            "title": "Precipitation-boundary interaction graph for Al-Mg-Si alloys",
            "status": "Future microstructure-graph extension.",
            "coverage_score": 3,
            "logic": (
                "The corpus contains Al-Mg-Si precipitation, precipitate-particle interactions, "
                "grain-boundary interactions and SEM/EBSD correlation. A graph engine could map "
                "precipitates, particles, boundaries and local microstructure evolution."
            ),
            "evidence": {
                "aluminum alloys": get_count("aluminum alloys"),
                "precipitation and ordering": get_count("precipitation and ordering"),
                "SEM microscopy": get_count("SEM microscopy"),
                "EBSD / TKD orientation microscopy": get_count("EBSD / TKD orientation microscopy"),
            },
            "outputs": [
                "precipitate-boundary graph",
                "particle interaction statistics",
                "grain-boundary neighborhood map",
            ],
        },
    ]


def axis_angle_from_matrix(values):
    import math
    import numpy as np

    R = np.array(values, dtype=float).reshape(3, 3)
    trace = float(np.trace(R))
    cos_theta = max(-1.0, min(1.0, (trace - 1.0) / 2.0))
    theta = math.degrees(math.acos(cos_theta))

    if abs(theta) < 1e-8:
        axis = np.array([0.0, 0.0, 1.0])
    else:
        rx = R[2, 1] - R[1, 2]
        ry = R[0, 2] - R[2, 0]
        rz = R[1, 0] - R[0, 1]
        denom = 2.0 * math.sin(math.radians(theta))
        axis = np.array([rx, ry, rz]) / denom

    return theta, axis


df_raw = load_publications()
df = enrich_dataframe(df_raw)
counts = coverage_counts(df, ["alloy_systems", "methods", "mechanisms", "properties"])


st.title("Metallurgy Crystallography Knowledge Engine")
st.caption(
    "Metallurgy-first research map for alloy systems, phase transformations, EBSD/TKD, "
    "martensite, twinning, processing routes, crystallography tools and research gaps."
)


with st.sidebar:
    st.header("Filters")

    all_labels = ["All"] + sorted(counts["label"].unique().tolist()) if not counts.empty else ["All"]
    selected_label = st.selectbox("Theme / alloy / method", all_labels)

    q = st.text_input("Search title or abstract", "")

    year_min = int(df["year_num"].min()) if df["year_num"].notna().any() else 2018
    year_max = int(df["year_num"].max()) if df["year_num"].notna().any() else 2026

    selected_years = st.slider(
        "Year range",
        min_value=year_min,
        max_value=year_max,
        value=(year_min, year_max),
    )


filtered = filter_by_label(df, selected_label)

if q:
    text = (
        filtered["title"].astype(str)
        + " "
        + filtered["abstract"].astype(str)
        + " "
        + filtered["venue"].astype(str)
    )
    filtered = filtered[text.str.contains(q, case=False, na=False)]

filtered = filtered[
    (filtered["year_num"].fillna(year_min) >= selected_years[0])
    & (filtered["year_num"].fillna(year_max) <= selected_years[1])
]


tab_overview, tab_pubs, tab_matrix, tab_gaps, tab_niti, tab_crys, tab_export = st.tabs(
    [
        "Overview",
        "Publication Explorer",
        "Theme Matrix",
        "Research Gap Engine",
        "NiTi Variant Gap",
        "Crystallography Lab",
        "Data Export",
    ]
)


with tab_overview:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records loaded", len(df))
    c2.metric("Filtered records", len(filtered))
    c3.metric("Detected themes", counts["label"].nunique() if not counts.empty else 0)
    c4.metric("Year span", f"{year_min}–{year_max}")

    st.subheader("Theme coverage")
    if not counts.empty:
        top = counts.sort_values("count", ascending=False).head(20)
        st.bar_chart(top.set_index("label")["count"])
        st.dataframe(top, use_container_width=True, hide_index=True)
    else:
        st.warning("No theme counts detected yet.")

    st.subheader("Scientific center of gravity")
    st.markdown(
        """
        The app is focused on metallurgy, especially:

        - martensitic transformations,
        - twinning and weak twins,
        - EBSD/TKD orientation microscopy,
        - transformation matrices and symmetry,
        - NiTi shape-memory alloys,
        - steels, Mg alloys, Al alloys, Cu alloys, Ti alloys and Au alloys,
        - additive manufacturing / LPBF,
        - precipitation, recrystallization, texture and mechanical behavior.
        """
    )


with tab_pubs:
    st.subheader("Publication explorer")

    cols = [
        "year", "title", "venue", "focus_label",
        "alloy_systems", "methods", "mechanisms", "properties"
    ]
    existing = [c for c in cols if c in filtered.columns]
    st.dataframe(filtered[existing], use_container_width=True, hide_index=True)

    st.download_button(
        "Download filtered records as CSV",
        filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_metallurgy_records.csv",
        mime="text/csv",
    )


with tab_matrix:
    st.subheader("Theme matrix")

    families = ["alloy_systems", "methods", "mechanisms", "properties"]
    selected_family = st.selectbox("Theme family", families)

    ex_rows = []
    for _, row in df.iterrows():
        for label in split_labels(row.get(selected_family, "")):
            ex_rows.append(
                {
                    "year": row.get("year", ""),
                    "title": row.get("title", ""),
                    "label": label,
                    "focus": row.get("focus_label", ""),
                }
            )

    if ex_rows:
        ex = pd.DataFrame(ex_rows)
        pivot = pd.crosstab(ex["label"], ex["focus"])
        st.dataframe(pivot, use_container_width=True)
    else:
        st.info("No labels detected for this family.")

    st.subheader("Knowledge graph view")
    st.markdown(
        """
        ```text
        Publication
          → alloy system
          → method
          → mechanism
          → property / research output

        Example:
        NiTi
          → EBSD/TKD
          → B2→B19′ martensitic transformation
          → variant reorientation / texture evolution
          → superelastic or shape-memory interpretation
        ```
        """
    )


with tab_gaps:
    st.subheader("Layered research-gap engine")

    for gap in build_gap_cards(counts):
        with st.expander(f"{gap['title']} · coverage score {gap['coverage_score']}"):
            st.markdown(f"**Status:** {gap['status']}")
            st.markdown(f"**Logic:** {gap['logic']}")

            st.markdown("**Evidence in current dataset:**")
            st.json(gap["evidence"])

            st.markdown("**Possible outputs:**")
            for item in gap["outputs"]:
                st.markdown(f"- {item}")


with tab_niti:
    st.subheader("Process-aware NiTi martensite variant-mapping framework")
    st.info("This is a future research extension, not a direct completed-work claim.")

    st.markdown(
        """
        **Core idea**

        ```text
        process / thermal history
          → B2 parent grain structure
          → B19′ martensite variant selection
          → EBSD/TKD variant map
          → texture-memory relation
          → superelastic / shape-memory response
        ```

        **Main research questions**

        1. Can thermal history bias B2 parent-grain texture in NiTi?
        2. Does B2 parent texture control B19′ martensite variant selection?
        3. Can EBSD/TKD reconstruct parent B2 grains from B19′ product orientations?
        4. Are specific B19′ variant pairs favored near melt-pool boundaries or thermal-gradient directions?
        5. Does variant distribution correlate with recoverable strain, hysteresis, residual strain or transformation stress?
        6. Can correspondence theory predict observed B19′ variant families?
        7. Does heat treatment preserve or erase processing-induced crystallographic memory?

        **Needed data**

        - EBSD/TKD phase and orientation maps,
        - B2/B19′ orientation relationship,
        - variant labels,
        - parent grain reconstruction,
        - texture and pole figures,
        - thermal/process descriptors,
        - transformation temperatures,
        - superelastic or shape-memory mechanical data.
        """
    )


with tab_crys:
    st.subheader("Crystallography Lab")

    st.markdown("Paste a 3×3 rotation/orientation matrix to calculate an axis-angle representation.")

    matrix_text = st.text_area(
        "Matrix",
        value="1 0 0\n0 1 0\n0 0 1",
        height=120,
    )

    try:
        vals = [float(x) for x in re.split(r"[\s,;]+", matrix_text.strip()) if x]
        if len(vals) != 9:
            st.warning("Enter exactly 9 numbers.")
        else:
            theta, axis = axis_angle_from_matrix(vals)
            st.metric("Rotation angle", f"{theta:.4f}°")
            st.write(
                {
                    "axis_x": round(float(axis[0]), 6),
                    "axis_y": round(float(axis[1]), 6),
                    "axis_z": round(float(axis[2]), 6),
                }
            )
    except Exception as exc:
        st.error(f"Could not calculate axis-angle: {exc}")

    st.markdown(
        """
        **Use in metallurgy**

        Axis-angle and misorientation logic is useful for:

        - EBSD/TKD orientation comparison,
        - twin-relation detection,
        - martensite variant comparison,
        - parent/product orientation relationships,
        - texture and variant-family analysis.
        """
    )


with tab_export:
    st.subheader("Data export")

    st.download_button(
        "Download enriched dataset",
        df.to_csv(index=False).encode("utf-8"),
        file_name="enriched_metallurgy_publications.csv",
        mime="text/csv",
    )

    st.download_button(
        "Download theme coverage",
        counts.to_csv(index=False).encode("utf-8"),
        file_name="theme_coverage.csv",
        mime="text/csv",
    )

    st.subheader("Debug information")
    st.write("Root path:", str(ROOT))
    st.write("Existing data files:")
    st.write([str(p) for p in DATA_PATHS if p.exists()])
