# Data Provenance

This project uses manually provided and user-imported publication records.

The repository may include a seed dataset created from copied publication-profile text. Additional records can be added manually through CSV files or pasted text.

---

## Supported data sources

The app supports input from:

- copied research-profile text,
- copied institutional publication pages,
- manually prepared CSV files,
- Google Scholar / Publish or Perish CSV exports,
- ResearchGate-style copied publication lists,
- university profile publication lists,
- ORCID-style publication exports,
- DOI metadata copied manually.

---

## What is stored

The project may store publication metadata such as:

- title,
- year,
- authors,
- journal or source,
- abstract or description,
- keywords,
- detected alloy systems,
- detected methods,
- detected mechanisms,
- detected processing routes.

---

## What is not stored

This repository should not store:

- private emails,
- private reviewer comments,
- paywalled full-text papers without permission,
- restricted institutional documents,
- scraped data from pages that prohibit automated collection.

---

## Scraping policy

The project does not automatically scrape restricted academic-profile pages.

For sources such as Google Scholar, ResearchGate, institutional pages, or other academic platforms, users should provide:

- exported CSV files,
- copied text,
- public metadata,
- or manually prepared publication lists.

---

## Data quality

Classification quality depends on the input text.

Short records with only titles may produce weaker classification than records containing titles, abstracts, methods, alloy names, and keywords.

The keyword-mapping system should be reviewed by a metallurgy expert before using the output in formal academic work.

---

## Reproducibility

For reproducible analysis, keep a stable CSV version of the publication dataset in the `data/` folder and document the date when the dataset was exported or copied.

Recommended file naming:

```text
data/publications_YYYY_MM_DD.csv
