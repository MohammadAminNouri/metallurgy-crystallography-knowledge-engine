# Cayron Metallurgy Knowledge Engine

A Streamlit research dashboard for mapping Cyril Cayron's publication record with a metallurgy-first lens.

## What it does

The app extracts and classifies publications into:

- Alloy systems: NiTi, martensitic/bainitic steels, 316L/CuCrZr, Mg alloys, Al-Mg-Si-Cu, Ti-6Al-4V, Au-Cu/Au-Ti, Cu alloys, HEAs, superalloys, MMCs.
- Metallurgical mechanisms: martensitic transformations, twinning/weak twins, variant selection, correspondence theory, precipitation, recrystallization, LPBF metallurgy, mechanical behavior, diffraction artefacts.
- Methods: EBSD/TKD, TEM/STEM/HRTEM, SEM/BSE/FESEM, XRD/synchrotron, thermal processing, deformation/mechanical testing, LPBF, crystallographic modeling.
- Research gaps: generated from recurring combinations in the publication map.
- Crystallography calculator: orientation matrices, cubic misorientation, simplified variant generation, axis-angle extraction.

## Data coverage

The bundled seed dataset is parsed from the uploaded ResearchGate text in this conversation. It contains the visible copied records, not necessarily every publication ever listed on ResearchGate/EPFL/Scholar.

To cover all publications:

1. Copy all ResearchGate publication pages or use an export if available.
2. Copy EPFL/Infoscience publication text or export CSV/BibTeX and convert to CSV.
3. Export Google Scholar using a compliant tool such as Publish or Perish or manual CSV/BibTeX export.
4. Use the sidebar importer in the app to paste text or upload CSV.
5. Download the enriched CSV from the Data export tab.

The app avoids automated Google Scholar/ResearchGate scraping because those pages are fragile and may have access restrictions. It is designed to ingest user-provided exports safely.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud

1. Push this folder to GitHub.
2. On Streamlit Cloud, choose `app.py` as the entry point.
3. Keep `requirements.txt` in the repository root.

## Important scientific scope

This is not a generic bibliometric dashboard. It is built around the scientific patterns that repeatedly appear in Cayron's metallurgy work:

- martensite crystallography
- twinning and weak twins
- variant selection and orientation relationships
- EBSD/TKD parent grain reconstruction
- transformation matrices and correspondence theory
- LPBF/thermal processing and microstructure control
- precipitation and ordering in Al, Cu and Au-based alloys
- microstructure-property relations in NiTi, steels, Mg, Ti and 316L systems

## Files

```text
app.py                                  Main Streamlit app
data/cayron_seed_publications.csv       Parsed seed dataset
data/metallurgy_taxonomy.json           Metallurgy dictionary and classifier terms
src/text_parser.py                      Text/CSV import tools
src/taxonomy.py                         Classification engine
src/crystallography.py                  Matrix, variant and misorientation tools
src/gap_engine.py                       Research-gap generator
src/visuals.py                          Plotly/networkx visualizations
```
