# Metallurgy Crystallography Knowledge Engine

A Streamlit-based research intelligence app for mapping metallurgy publication corpora into alloy systems, phase transformations, EBSD/TKD methods, crystallography tools, processing routes, microstructure mechanisms, properties, and research gaps.

[![Python Check](https://github.com/MohammadAminNouri/metallurgy-crystallography-knowledge-engine/actions/workflows/python-check.yml/badge.svg)](https://github.com/MohammadAminNouri/metallurgy-crystallography-knowledge-engine/actions/workflows/python-check.yml)

## Purpose

This project turns a publication corpus into a metallurgy-first knowledge map. It focuses on repeated scientific themes rather than only paper counts.

## Main modules

- Overview
- Publication Explorer
- Knowledge Graph
- Theme Matrix
- Research Gap Engine
- Deep NiTi Variant Gap
- Crystallography Lab
- Data Export

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud

Repository: `MohammadAminNouri/metallurgy-crystallography-knowledge-engine`  
Branch: `main`  
Main file path: `app.py`  
Python version: `3.11`

## Data coverage

The bundled seed corpus is parsed from the publication/profile text supplied in the working context. It covers all publication-like records visible in that text. If the original profile contains additional pages or records not included in the copied text, import them through the app using pasted text or CSV.

The app intentionally avoids automatic scraping of academic profile pages.

## Scientific caution

Classification is rule-based and should be reviewed by a metallurgy expert before formal academic use. Crystallography calculations are simplified helper tools.

## License

MIT License.
