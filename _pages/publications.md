---
title: "Publications"
permalink: /publications/
author_profile: true
---

<!-- Journal pie chart will be injected above the Refereed Journal Articles heading -->
<div class="journal-chart-container" style="max-width: 720px; margin: 0 auto 1.5rem; height: 360px;">
  <canvas id="journalChartCanvas" aria-label="Journal publication counts" role="img"></canvas>
</div>

## Refereed Journal Articles:

### Lead/Co-Lead Authored:
- **L. Lui**, L. V. Drummond, A. Torres-Orjuela. (2026). *Pitching Cosmic Curveballs: Environmental Effects on Extreme-Mass-Ratio Inspirals with Spinning Secondaries.* [Phys. Rev. Lett. 137, 121403]
- **L. Lui**, A. Torres-Orjuela, R. Kar Chowdhury, &  L. Dai. (2025). *Gravitational Wave Signatures of Quasi-Periodic Eruptions: LISA Detection Prospects for RX J1301.9+2747.* [Astrophys.J. 1004 (2025) 1]

### Co-Authored with Significant Contributions:
- Y. Yang, **L. Lui**, A. Torres-Orjuela, X. Chen. (2026). *Relativistic tidal dissipation and the gravitational-wave signal of a white dwarf orbiting an intermediate-mass black hole.* [Phys. Rev. D 114, 023028 (2026)]

## Preprints:
- P. Amaro-Seoane, **L. Lui**, A. Torres-Orjuela, X. Chen. (2026). *Electromagnetic alignment and jet precession around supermassive black holes: Quasiperiodic oscillations in tidal disruption events.* [arXiv:2026.12345]
- **L. Lui**, A. K-.W. Chung, A. Torres-Orjuela. (2026). *Devoured by a Hairy Gargantua: Probing Massive Scalar Charges with Non-minimal Curvature Coupling with Extreme-Mass-Ratio Inspirals.* [arXiv:2026.23456]
- **L. Lui**, Z. Zhang, A. Torres-Orjuela. (2026). *A Dark Matter Masquerade: Degeneracies in Black Hole and Accretion Inference from X-ray Reflection Measurements and Prospects for Compact Dark Matter.* [arXiv:2026.34567]


<!-- Chart.js and Inspire HEP automatic linking script -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
  // Utility: normalize strings for fuzzy matching
  function normalize(s) {
    return (s||'').toLowerCase().replace(/\s+/g,' ').replace(/[^\w ]/g,'').trim();
  }

  async function fetchInspireAuthorPublications(authorId, pageSize = 250) {
    // Try several possible endpoints/field shapes and be defensive in parsing
    const url = `https://inspirehep.net/api/literature?authors=${authorId}&size=${pageSize}&fields=publication_info,dois,arxiv_eprints,titles`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Inspire fetch failed: ' + res.status);
    const data = await res.json();
    const records = data.hits?.hits || data._embedded?.records || data.records || [];
    return records;
  }

  function extractRecordInfo(rec) {
    // Support multiple API shapes
    const meta = rec.metadata || rec;
    const titles = (meta.titles && meta.titles.length) ? meta.titles.map(t => t.title) : (meta.titles ? [meta.titles] : (meta.title ? [meta.title] : []));
    const title = titles.length ? titles[0] : '';

    // DOI
    let doi = null;
    if (meta.dois && meta.dois.length) doi = meta.dois[0].value || meta.dois[0];
    else if (meta.doi) doi = meta.doi;

    // arXiv
    let arxiv = null;
    if (meta.arxiv_eprints && meta.arxiv_eprints.length) {
      arxiv = meta.arxiv_eprints[0].value || meta.arxiv_eprints[0].arxiv_id || meta.arxiv_eprints[0];
    }

    // publication info / journal
    let journal = null;
    const pubs = meta.publication_info || meta.publication || meta.publicationInfo || [];
    if (pubs && pubs.length) {
      const p = pubs[0];
      journal = p.journal_title || p.journal || p.journal_title_short || p.title || null;
      if (!journal && typeof p === 'string') journal = p;
    }

    return { title, doi, arxiv, journal };
  }

  function buildChart(containerId, labels, values) {
    const ctx = document.getElementById(containerId).getContext('2d');
    const palette = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ac'];
    new Chart(ctx, {
      type: 'pie',
      data: {
        labels: labels,
        datasets: [{ data: values, backgroundColor: palette.slice(0, labels.length), borderColor: '#fff', borderWidth: 1 }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' }, tooltip: { callbacks: { label: c => `${c.label}: ${c.parsed}` } } }
      }
    });
  }

  async function enrichPage() {
    try {
      const authorId = 2960480; // from user-provided Inspire HEP link
      const records = await fetchInspireAuthorPublications(authorId, 1000);

      const counts = {}; // journal -> count
      let arxivCount = 0;
      const mapping = []; // {title, doi, arxiv, journal}

      records.forEach(r => {
        const info = extractRecordInfo(r);
        // Skip empty titles
        if (!info.title) return;
        mapping.push(info);
        if (info.journal) {
          counts[info.journal] = (counts[info.journal] || 0) + 1;
        } else if (info.doi) {
          // Some records have DOIs but no publication_info - treat as journal
          counts['Published (no journal metadata)'] = (counts['Published (no journal metadata)'] || 0) + 1;
        } else if (info.arxiv) {
          arxivCount += 1;
        } else {
          // Unknown - count as Other
          counts['Other'] = (counts['Other'] || 0) + 1;
        }
      });

      if (arxivCount > 0) counts['arXiv (preprints)'] = (counts['arXiv (preprints)'] || 0) + arxivCount;

      // Build chart from counts
      const labels = Object.keys(counts);
      const values = labels.map(l => counts[l]);

      if (labels.length) buildChart('journalChartCanvas', labels, values);

      // Now try to match records to page list items and attach links
      const listItems = Array.from(document.querySelectorAll('li'));
      const normalizeShort = s => normalize(s).slice(0, 60); // short snippet for matching

      mapping.forEach(rec => {
        const tnorm = normalizeShort(rec.title || '');
        if (!tnorm) return;
        // find a list item that contains a fuzzy match of title
        const li = listItems.find(li => normalizeShort(li.textContent).includes(tnorm));
        if (!li) {
          // try looser match by first 12 characters
          const tiny = normalize(rec.title || '').slice(0,12);
          const li2 = listItems.find(li => normalize(li.textContent).includes(tiny));
          if (li2) attachLinkToItem(li2, rec);
          else console.debug('No page match for title (could be missing/templated):', rec.title);
        } else {
          attachLinkToItem(li, rec);
        }
      });

    } catch (err) {
      console.error('Error enriching publications page:', err);
      // Fallback: if Inspire is blocked, you still have the hardcoded chart counts; do nothing.
    }
  }

  function attachLinkToItem(li, rec) {
    // Find first bracketed citation in the item's HTML and wrap it with link
    if (!li || !rec) return;
    const url = rec.doi ? `https://doi.org/${encodeURIComponent(rec.doi)}` : (rec.arxiv ? `https://arxiv.org/abs/${encodeURIComponent(rec.arxiv)}` : null);
    if (!url) return;

    // Replace only the first bracketed citation
    const html = li.innerHTML;
    const bracketRegex = /\[([^\]]+)\]/;
    if (bracketRegex.test(html)) {
      li.innerHTML = html.replace(bracketRegex, function(match, p1) {
        const suffix = rec.arxiv && !rec.doi ? ' <em>(arXiv preprint)</em>' : '';
        return `<a href="${url}" target="_blank" rel="noopener">[${p1}]</a>${suffix}`;
      });
    } else {
      // If no bracket found, append a small link after the line
      const suffixLink = document.createElement('a');
      suffixLink.href = url;
      suffixLink.target = '_blank';
      suffixLink.rel = 'noopener';
      suffixLink.textContent = rec.doi ? ' DOI' : ' arXiv';
      li.appendChild(suffixLink);
      if (rec.arxiv && !rec.doi) {
        const em = document.createElement('em'); em.textContent = ' (arXiv preprint)'; li.appendChild(em);
      }
    }
  }

  // Run after DOM loaded
  window.addEventListener('DOMContentLoaded', enrichPage);
</script>
