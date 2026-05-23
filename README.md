# Metallurgy Crystallography Knowledge Engine

A Streamlit research dashboard for mapping publication records with a metallurgy-first lens: alloy systems, phase transformations, EBSD/TKD methods, martensite crystallography, twinning mechanisms, processing–microstructure–property links, and research-gap discovery.

[![Python Check](https://github.com/MohammadAminNouri/metallurgy-crystallography-knowledge-engine/actions/workflows/python-check.yml/badge.svg)](https://github.com/MohammadAminNouri/metallurgy-crystallography-knowledge-engine/actions/workflows/python-check.yml)

---

## Purpose

This repository provides an interactive research-intelligence platform for metallurgy and materials-science publication analysis.

The goal is to transform a publication record into a structured scientific map showing:

- alloy systems studied,
- phase transformations investigated,
- microscopy and diffraction methods used,
- microstructure mechanisms,
- processing–microstructure–property links,
- crystallographic concepts,
- and possible future research gaps.

The focus is metallurgy, not generic bibliometrics.

---

## What it does

The dashboard can:

1. Parse publication records from copied profile text or CSV files.
2. Detect metallurgy-related keywords and mechanisms.
3. Classify publications by alloy system, method, mechanism, and processing route.
4. Build a knowledge graph linking papers, methods, alloys, and scientific themes.
5. Map martensite, twinning, EBSD/TKD, crystallography, texture, precipitation, recrystallization, LPBF, and thermomechanical processing.
6. Provide simple crystallography tools for orientation matrices, misorientation, axis-angle calculations, and variant-style analysis.
7. Generate research-gap suggestions based on repeated and underexplored combinations.

---

## Metallurgy focus

The platform is designed around recurring metallurgy concepts such as:

- martensitic transformations,
- deformation twinning,
- transformation twinning,
- weak twins and unconventional twins,
- orientation relationships,
- correspondence matrices,
- distortion matrices,
- variant selection,
- habit planes,
- EBSD and TKD analysis,
- TEM, SEM, and XRD characterization,
- parent grain reconstruction,
- texture evolution,
- precipitation,
- recrystallization,
- additive manufacturing,
- laser powder bed fusion,
- steels,
- NiTi shape memory alloys,
- magnesium alloys,
- aluminum alloys,
- copper alloys,
- titanium alloys,
- gold alloys,
- high-entropy alloys,
- and processing–microstructure–property relations.

---

## Core modules

```text
Publication Explorer
    Search, filter, and classify publication records.

Metallurgy Knowledge Graph
    Connect papers, alloy systems, methods, mechanisms, and processing routes.

Methods Dashboard
    Track EBSD, TKD, TEM, SEM, XRD, synchrotron diffraction, and related tools.

Alloy-System Mapper
    Group work by NiTi, steels, Mg alloys, Al alloys, Cu alloys, Ti alloys, Au alloys, and AM materials.

Crystallography Calculator
    Perform simplified matrix, misorientation, axis-angle, and variant calculations.

Research-Gap Generator
    Identify strong, weak, and missing combinations in the publication landscape.
