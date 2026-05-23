from __future__ import annotations
import io
import json
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st

from src.text_parser import parse_copied_profile_text, scholar_csv_to_records
from src.taxonomy import load_taxonomy, enrich_dataframe, explode_labels
from src.visuals import timeline, bar_counts, network_figure
from src.gap_engine import combination_counts, suggest_gaps
from src.crystallography import parse_matrix, matrix_to_markdown, cubic_symmetry_operators, generate_variants, misorientation, axis_angle_from_rotation

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "cayron_seed_publications.csv"
RAW_PATH = ROOT / "data" / "researchgate_uploaded_raw.txt"
SOURCE_REGISTRY_PATH = ROOT / "data" / "source_registry.json"

st.set_page_config(
    page_title="Cayron Metallurgy Knowledge Engine",
    page_icon="🧬",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
    .metric-card {border:1px solid rgba(128,128,128,.25); border-radius:18px; padding:14px 18px;}
    .small-muted {color: #6c6c6c; font-size: 0.92rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data(show_spinner=False)
def load_seed() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH).fillna("")

@st.cache_data(show_spinner=False)
def enrich_cached(df: pd.DataFrame) -> pd.DataFrame:
    return enrich_dataframe(df.fillna(""), load_taxonomy())


def merge_records(base: pd.DataFrame, extra: pd.DataFrame) -> pd.DataFrame:
    if extra.empty:
        return base
    full = pd.concat([base, extra], ignore_index=True, sort=False).fillna("")
    full["_key"] = full["title"].astype(str).str.lower().str.replace(r"\W+", "", regex=True).str.slice(0, 180)
    full = full.drop_duplicates("_key", keep="first").drop(columns=["_key"])
    return full


def safe_download(df: pd.DataFrame, filename: str, label: str):
    st.download_button(label, df.to_csv(index=False).encode("utf-8"), file_name=filename, mime="text/csv")


if "records" not in st.session_state:
    st.session_state.records = load_seed()

with st.sidebar:
    st.title("Cayron Engine")
    st.caption("Metallurgy-first mapping of publications, methods, alloy systems, mechanisms and crystallography tools.")
    st.divider()
    seed_count = len(load_seed())
    st.info(f"Seed dataset: {seed_count} parsed records from the uploaded ResearchGate text. Add EPFL / Scholar / full ResearchGate exports below to extend coverage.")

    with st.expander("Import more records", expanded=False):
        source_name = st.text_input("Source label", value="manual EPFL/Scholar/ResearchGate import")
        text_import = st.text_area("Paste copied publication/profile text", height=160, placeholder="Paste EPFL, ResearchGate page text, Scholar export text, etc.")
        if st.button("Parse pasted text", use_container_width=True):
            recs = parse_copied_profile_text(text_import, source=source_name)
            st.session_state.records = merge_records(st.session_state.records, pd.DataFrame(recs))
            st.success(f"Added {len(recs)} parsed records before deduplication.")

        csv_file = st.file_uploader("Upload CSV export", type=["csv"])
        csv_kind = st.selectbox("CSV type", ["Already normalized", "Google Scholar / Publish or Perish style"])
        if csv_file is not None and st.button("Import CSV", use_container_width=True):
            raw = pd.read_csv(csv_file).fillna("")
            if csv_kind.startswith("Google"):
                recs = scholar_csv_to_records(raw.to_dict(orient="records"), source=source_name)
                extra = pd.DataFrame(recs)
            else:
                extra = raw
            st.session_state.records = merge_records(st.session_state.records, extra)
            st.success(f"Imported {len(extra)} rows before deduplication.")

        if st.button("Reset to uploaded seed", use_container_width=True):
            st.session_state.records = load_seed()
            st.success("Reset complete.")

records = st.session_state.records.fillna("")
df = enrich_cached(records)

st.title("Cyril Cayron Metallurgy Knowledge Engine")
st.markdown(
    "This app maps his publication record into **alloy systems**, **metallurgical mechanisms**, **experimental methods**, "
    "**crystallography concepts**, and **future research gaps**. It is deliberately focused on metallurgy: martensite, twinning, EBSD/TKD, "
    "phase transformations, additive manufacturing, precipitation, texture, and microstructure-property relations."
)

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.metric("Records", len(df))
with m2:
    st.metric("Core metallurgy", int((df["focus_label"] == "Core metallurgy").sum()) if "focus_label" in df else 0)
with m3:
    st.metric("Alloy labels", explode_labels(df, "alloy_systems")["alloy_systems"].nunique() if "alloy_systems" in df else 0)
with m4:
    st.metric("Method labels", explode_labels(df, "methods")["methods"].nunique() if "methods" in df else 0)
with m5:
    year_min = int(pd.to_numeric(df.get("year", pd.Series(dtype=str)), errors="coerce").min()) if not df.empty and pd.to_numeric(df.get("year", pd.Series(dtype=str)), errors="coerce").notna().any() else "—"
    year_max = int(pd.to_numeric(df.get("year", pd.Series(dtype=str)), errors="coerce").max()) if not df.empty and pd.to_numeric(df.get("year", pd.Series(dtype=str)), errors="coerce").notna().any() else "—"
    st.metric("Year span", f"{year_min}–{year_max}")

core_terms = [
    "martensite", "twinning", "EBSD/TKD", "variant selection", "correspondence theory", "transformation matrices", "NiTi", "steels", "Mg", "Al-Mg-Si", "LPBF"
]
st.caption("Core vocabulary: " + " · ".join(core_terms))

tabs = st.tabs([
    "Overview",
    "Publication explorer",
    "Knowledge graph",
    "Methods & alloys",
    "Crystallography calculator",
    "Research gaps",
    "Data export"
])

with tabs[0]:
    c1, c2 = st.columns([1.15, 1])
    with c1:
        st.plotly_chart(timeline(df), use_container_width=True)
    with c2:
        focus_counts = df["focus_label"].value_counts().reset_index() if "focus_label" in df else pd.DataFrame()
        if not focus_counts.empty:
            focus_counts.columns = ["focus", "count"]
            import plotly.express as px
            st.plotly_chart(px.pie(focus_counts, values="count", names="focus", title="Metallurgy relevance split"), use_container_width=True)

    st.subheader("Dominant recurring metallurgy identity")
    st.markdown(
        """
        **Main engine:** crystallography of microstructure formation in metals — especially **martensitic transformations, twinning, variants, orientation relationships, correspondence matrices, EBSD/TKD reconstruction, texture and processing–microstructure–property links**.

        **Practical reading:** his work is less about simple alloy ranking and more about explaining *why a microstructure forms*, *which variants/twins appear*, *how they are measured*, and *how processing drives the final mechanical behavior*.
        """
    )

    st.subheader("Top extracted mechanisms")
    mech = explode_labels(df, "mechanisms")
    if not mech.empty:
        st.plotly_chart(bar_counts(mech, "mechanisms", "Mechanism frequency"), use_container_width=True)

with tabs[1]:
    st.subheader("Search and filter publications")
    q = st.text_input("Search title / abstract / venue / authors", placeholder="NiTi, EBSD, martensite, LPBF, Al-Mg-Si, weak twins...")
    col1, col2, col3 = st.columns(3)
    with col1:
        focus_filter = st.multiselect("Focus", sorted(df["focus_label"].dropna().unique().tolist())) if "focus_label" in df else []
    with col2:
        years = pd.to_numeric(df.get("year", pd.Series(dtype=str)), errors="coerce")
        if years.notna().any():
            yr_min, yr_max = int(years.min()), int(years.max())
            yr_range = st.slider("Year range", yr_min, yr_max, (yr_min, yr_max))
        else:
            yr_range = None
    with col3:
        type_filter = st.multiselect("Publication type", sorted(df["publication_type"].dropna().unique().tolist())) if "publication_type" in df else []

    f = df.copy()
    if q:
        mask = f[[c for c in ["title", "abstract", "venue", "authors", "mechanisms", "methods", "alloy_systems"] if c in f]].astype(str).agg(" ".join, axis=1).str.contains(q, case=False, na=False)
        f = f[mask]
    if focus_filter:
        f = f[f["focus_label"].isin(focus_filter)]
    if type_filter:
        f = f[f["publication_type"].isin(type_filter)]
    if yr_range and "year_num" in f:
        f = f[(f["year_num"].isna()) | ((f["year_num"] >= yr_range[0]) & (f["year_num"] <= yr_range[1]))]

    st.write(f"Showing **{len(f)}** records.")
    show_cols = [c for c in ["year", "title", "publication_type", "venue", "alloy_systems", "mechanisms", "methods", "focus_label", "core_metallurgy_score", "source"] if c in f]
    st.dataframe(f[show_cols].sort_values(["year", "title"], ascending=[False, True]), use_container_width=True, height=520)

with tabs[2]:
    st.subheader("Knowledge graph")
    st.caption("Nodes connect publication titles to extracted alloy systems, mechanisms and methods. Use filters in the publication tab to inspect specific themes, or import more records for full coverage.")
    focus_only = st.toggle("Core metallurgy only", value=True)
    gdf = df[df["focus_label"] == "Core metallurgy"] if focus_only and "focus_label" in df else df
    st.plotly_chart(network_figure(gdf), use_container_width=True)

with tabs[3]:
    st.subheader("Methods, alloy systems and mechanisms")
    a, b, c = st.columns(3)
    with a:
        alloy_df = explode_labels(df, "alloy_systems")
        st.plotly_chart(bar_counts(alloy_df, "alloy_systems", "Alloy systems"), use_container_width=True)
    with b:
        method_df = explode_labels(df, "methods")
        st.plotly_chart(bar_counts(method_df, "methods", "Methods"), use_container_width=True)
    with c:
        mech_df = explode_labels(df, "mechanisms")
        st.plotly_chart(bar_counts(mech_df, "mechanisms", "Mechanisms"), use_container_width=True)

    st.subheader("Cross-combination matrix")
    combos = combination_counts(df)
    st.dataframe(combos, use_container_width=True)

with tabs[4]:
    st.subheader("Crystallography calculator")
    st.markdown(
        "This lightweight calculator covers the matrix logic he repeatedly uses: **orientation relationship**, **correspondence/distortion matrix**, **symmetry operators**, **variants**, and **misorientation**."
    )
    calc_tab1, calc_tab2, calc_tab3 = st.tabs(["Misorientation", "Variant generator", "Axis-angle from matrix"])

    with calc_tab1:
        st.caption("Enter two 3×3 orientation matrices. Rows separated by semicolons. Cubic symmetry is applied by default.")
        mtxt1 = st.text_area("g1", value="1 0 0; 0 1 0; 0 0 1", height=90)
        mtxt2 = st.text_area("g2", value="0 -1 0; 1 0 0; 0 0 1", height=90)
        if st.button("Compute minimum cubic misorientation"):
            try:
                g1 = parse_matrix(mtxt1)
                g2 = parse_matrix(mtxt2)
                res = misorientation(g1, g2, symmetry="cubic")
                st.success(f"Minimum misorientation angle: {res['angle_deg']:.4f}°")
                st.write("Axis:", np.round(res["axis"], 5))
                st.markdown(matrix_to_markdown(res["delta"]), unsafe_allow_html=False)
            except Exception as e:
                st.error(str(e))

    with calc_tab2:
        st.caption("Simplified variant generation: variant = parent symmetry operator × OR × correspondence. Useful for teaching/inspection; not a replacement for full MTEX/ARPGE pipelines.")
        cmat = st.text_area("Correspondence / transformation operator C", value="1 0 0; 0 1 0; 0 0 1", height=90)
        ormat = st.text_area("Orientation relationship operator OR", value="1 0 0; 0 1 0; 0 0 1", height=90)
        if st.button("Generate cubic variants"):
            try:
                C = parse_matrix(cmat)
                OR = parse_matrix(ormat)
                variants = generate_variants(cubic_symmetry_operators(), C, OR)
                st.success(f"Generated {len(variants)} unique variants using cubic parent symmetry.")
                st.dataframe(pd.DataFrame([v.flatten() for v in variants]).round(5), use_container_width=True)
            except Exception as e:
                st.error(str(e))

    with calc_tab3:
        rot = st.text_area("Rotation matrix", value="0 -1 0; 1 0 0; 0 0 1", height=90)
        if st.button("Get axis-angle"):
            try:
                R = parse_matrix(rot)
                angle, axis = axis_angle_from_rotation(R)
                st.success(f"Angle: {angle:.4f}°")
                st.write("Axis:", np.round(axis, 5))
            except Exception as e:
                st.error(str(e))

with tabs[5]:
    st.subheader("Research-gap generator")
    st.caption("The gaps are generated from repeated Cayron themes: martensite, twins, EBSD/TKD, variants, correspondence matrices, LPBF, precipitation and alloy-specific microstructure-property links.")
    gaps = suggest_gaps(df)
    for _, r in gaps.iterrows():
        with st.expander(f"{r['gap']}  ·  coverage score {r['coverage_score']}", expanded=bool(r['coverage_score'] >= 3)):
            st.markdown(f"**Logic:** {r['logic']}")
            st.markdown(f"**Needed knowledge blocks:** {', '.join(r['needs'])}")
            st.markdown(f"**Possible outputs:** {r['outputs']}")
            st.caption("Evidence in current dataset: " + (r["evidence_in_seed_dataset"] or "not detected yet; import more records"))

with tabs[6]:
    st.subheader("Export enriched dataset")
    safe_download(df, "cayron_enriched_metallurgy_map.csv", "Download enriched CSV")
    st.caption("Columns include mechanisms, alloy systems, methods, focus label and core metallurgy score.")
    st.dataframe(df.head(20), use_container_width=True)

    st.subheader("Source coverage note")
    st.markdown(
        """
        The bundled seed data comes from the uploaded ResearchGate text. To cover **all** records from ResearchGate, EPFL and Scholar, paste each profile/export into the importer or upload a CSV/BibTeX-derived table. The taxonomy/classifier will then re-map everything automatically.
        """
    )
    if SOURCE_REGISTRY_PATH.exists():
        st.subheader("Recommended source registry")
        st.dataframe(pd.read_json(SOURCE_REGISTRY_PATH), use_container_width=True)
