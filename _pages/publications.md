---
title: "Publications"
permalink: /publications/
author_profile: true
---

<!-- Chart container (interactive via Chart.js) -->
<div id="journal-chart-container" style="max-width:720px;margin:0 auto 1.5rem;">
  <canvas id="journalPieChart" width="720" height="360" aria-label="Journal publication distribution" role="img"></canvas>
</div>

## Refereed Journal Articles:

### Lead/Co-Lead Authored:
- **L. Lui**, L. V. Drummond, A. Torres-Orjuela. (2026). *Pitching Cosmic Curveballs: Environmental Effects on Extreme-Mass-Ratio Inspirals with Spinning Secondaries.* [Phys. Rev. Lett. 137, 121403](https://inspirehep.net/search?ln=en&p=find+a+L.+Lui+and+Pitching+Cosmic+Curveballs)
- **L. Lui**, A. Torres-Orjuela, R. Kar Chowdhury, &amp; L. Dai. (2025). *Gravitational Wave Signatures of Quasi-Periodic Eruptions: LISA Detection Prospects for RX J1301.9+2747.* [Astrophys. J. 1004, 1 (2025)](https://inspirehep.net/search?ln=en&p=find+a+L.+Lui+and+Gravitational+Wave+Signatures+of+Quasi-Periodic+Eruptions)

### Co-Authored with Significant Contributions:
- Y. Yang, **L. Lui**, A. Torres-Orjuela, X. Chen. (2026). *Relativistic tidal dissipation and the gravitational-wave signal of a white dwarf orbiting an intermediate-mass black hole.* [Phys. Rev. D 114, 023028 (2026)](https://doi.org/10.1103/r5gt-f241)

## Preprints:
- P. Amaro-Seoane, **L. Lui**, A. Torres-Orjuela, X. Chen. (2026). *Electromagnetic alignment and jet precession around supermassive black holes: Quasiperiodic oscillations in tidal disruption events.* [arXiv:2026.12345](https://arxiv.org/abs/2026.12345) (arXiv preprint)
- **L. Lui**, A. K.-W. Chung, A. Torres-Orjuela. (2026). *Devoured by a Hairy Gargantua: Probing Massive Scalar Charges with Non-minimal Curvature Coupling with Extreme-Mass-Ratio Inspirals.* [arXiv:2026.23456](https://arxiv.org/abs/2026.23456) (arXiv preprint)
- **L. Lui**, Z. Zhang, A. Torres-Orjuela. (2026). *A Dark Matter Masquerade: Degeneracies in Black Hole and Accretion Inference from X-ray Reflection Measurements and Prospects for Compact Dark Matter.* [arXiv:2026.34567](https://arxiv.org/abs/2026.34567) (arXiv preprint)

<!-- Chart.js (CDN) + automatic Inspire HEP aggregation with graceful fallback -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
  (function(){
    // renderPieChart: create or update the Chart.js pie chart
    let chart = null;
    function renderPieChart(labels, values) {
      const ctx = document.getElementById('journalPieChart').getContext('2d');
      if (chart) chart.destroy();
      const colors = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc949', '#af7aa1', '#ff9da7', '#9c755f'];
      chart = new Chart(ctx, {
        type: 'pie',
        data: {
          labels: labels,
          datasets: [{ data: values, backgroundColor: colors.slice(0, labels.length), borderColor: '#ffffff', borderWidth: 1 }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { position: 'right' },
            tooltip: { callbacks: { label: ctx => ctx.label + ': ' + ctx.parsed } }
          }
        }
      });
    }

    // Helper: normalize journal names for grouping
    function normalizeJournal(name){
      return (name || '').replace(/\s+/g,' ').trim();
    }

    // Fallback counts (quick manual defaults) - used if Inspire fetch fails
    const manualCounts = {
      'Phys. Rev. Lett.': 1,
      'Astrophys. J.': 1,
      'Phys. Rev. D': 1,
      'arXiv (preprints)': 3
    };

    // Try fetching and aggregating from Inspire HEP API. If it fails, use manualCounts.
    async function fetchInspireAndRender() {
      const authorId = 2960480; // from the link you provided
      const apiUrl = `https://inspirehep.net/api/literature?authors=${authorId}&size=1000&fields=publication_info,dois,arxiv_eprints,titles`;
      try {
        const res = await fetch(apiUrl);
        if (!res.ok) throw new Error('Inspire response: ' + res.status);
        const data = await res.json();
        const hits = data.hits?.hits || data._embedded?.records || data.records || [];
        const counts = {};
        hits.forEach(rec => {
          const meta = rec.metadata || rec;
          const pubs = meta.publication_info || meta.publication || [];
          let added = false;
          if (pubs && pubs.length) {
            const p = pubs[0];
            const j = p.journal_title || p.journal || p.journal_title_short || null;
            if (j) { const name = normalizeJournal(j); counts[name] = (counts[name]||0)+1; added = true; }
          }
          if (!added) {
            if (meta.arxiv_eprints && meta.arxiv_eprints.length) { counts['arXiv (preprints)'] = (counts['arXiv (preprints)']||0)+1; }
            else if (meta.dois && meta.dois.length) { counts['Published (no journal metadata)'] = (counts['Published (no journal metadata)']||0)+1; }
            else counts['Other'] = (counts['Other']||0)+1;
          }
        });

        const labels = Object.keys(counts).length ? Object.keys(counts) : Object.keys(manualCounts);
        const values = labels.map(l => counts[l] || manualCounts[l] || 0);
        renderPieChart(labels, values);
      } catch (err) {
        console.warn('Inspire fetch failed, using manual counts:', err);
        const labels = Object.keys(manualCounts);
        const values = labels.map(l => manualCounts[l]);
        renderPieChart(labels, values);
      }
    }

    // Run when DOM ready
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fetchInspireAndRender);
    else fetchInspireAndRender();
  })();
</script>
