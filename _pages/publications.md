---
title: "Publications"
permalink: /publications/
author_profile: true
layout: publications-list
---

This page displays my publications with optional preview figures. Publications with a preview image will show a representative figure alongside the publication details.

## Citation Format

Each publication entry supports the following fields for rich presentation:

- **preview**: Path to a representative figure (e.g., `qpe-lisa.png`)
- **selected**: Boolean to highlight featured publications
- **abstract**: Publication abstract
- **url**: Publication DOI or arXiv link
- **year**, **journal**, **volume**, **pages**: Standard bibliographic info

## Adding Preview Images

To add a preview image to your publication:

1. Save your image to `images/publications/` directory (e.g., `qpe-lisa.png`)
2. Add a `preview: qpe-lisa.png` field to the publication's BibTeX entry in `_data/publications.bib`
3. Optionally set `selected: true` to highlight the publication on the main publications page

## Publication Data

All publications are managed through `_data/publications.bib` in BibTeX format, making it easy to import from your reference manager (Zotero, Mendeley, etc.).
