---
title: "Publications"
permalink: /publications/
author_profile: true
---

<style>
  .publication-chart-wrap {
    max-width: 760px;
    margin: 0 auto 1.5rem;
    padding: 1rem 0 0;
    color: var(--global-text-color);
  }

  .publication-chart-title {
    text-align: center;
    margin: 0 0 0.75rem;
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--global-text-color);
  }

  .publication-chart {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1.5rem;
    flex-wrap: wrap;
  }

  .publication-chart canvas {
    display: block;
    width: min(420px, 80vw);
    height: 320px;
    margin: 0 auto;
  }

  .publication-chart-legend {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.5rem 1rem;
    margin-top: 0.5rem;
    font-size: 0.95rem;
    color: var(--global-text-color);
  }

  .publication-chart-legend span {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    white-space: nowrap;
  }

  .publication-chart-legend .swatch {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    vertical-align: middle;
  }

  .publication-chart a,
  .publication-list a {
    color: var(--global-link-color);
  }

  .publication-chart a:hover,
  .publication-list a:hover {
    color: var(--global-link-color-hover);
  }
</style>

<div class="publication-chart-wrap">
  <div class="publication-chart-title">Journal distribution</div>
  <div class="publication-chart">
    <canvas id="journalPieChart" aria-label="Journal publication counts" role="img"></canvas>
  </div>
  <div class="publication-chart-legend" id="publicationChartLegend" aria-hidden="false">
    <!-- legend will be populated by JS -->
  </div>
</div>

## Refereed Journal Articles:

<div class="publication-list">
### Lead/Co-Lead Authored:
- **L. Lui**, L. V. Drummond, A. Torres-Orjuela. (2026). *Pitching Cosmic Curveballs: Environmental Effects on Extreme-Mass-Ratio Inspirals with Spinning Secondaries.* [Phys. Rev. Lett. 137, 121403](https://inspirehep.net/search?ln=en&p=find+a+L.+Lui+and+Pitching+Cosmic+Curveballs)
- **L. Lui**, A. Torres-Orjuela, R. Kar Chowdhury, &amp; L. Dai. (2025). *Gravitational Wave Signatures of Quasi-Periodic Eruptions: LISA Detection Prospects for RX J1301.9+2747.* [Astrophys. J. 1004, 1 (2025)](https://inspirehep.net/search?ln=en&p=find+a+L.+Lui+and+Gravitational+Wave+Signatures+of+Quasi-Periodic+Eruptions)

### Co-Authored with Significant Contributions:
- Y. Yang, **L. Lui**, A. Torres-Orjuela, X. Chen. (2026). *Relativistic tidal dissipation and the gravitational-wave signal of a white dwarf orbiting an intermediate-mass black hole.* [Phys. Rev. D 114, 023028 (2026)](https://doi.org/10.1103/r5gt-f241)

## Preprints:
- P. Amaro-Seoane, **L. Lui**, A. Torres-Orjuela, X. Chen. (2026). *Electromagnetic alignment and jet precession around supermassive black holes: Quasiperiodic oscillations in tidal disruption events.* [arXiv:2026.12345](https://arxiv.org/abs/2026.12345) <em>(arXiv preprint)</em>
- **L. Lui**, A. K.-W. Chung, A. Torres-Orjuela. (2026). *Devoured by a Hairy Gargantua: Probing Massive Scalar Charges with Non-minimal Curvature Coupling with Extreme-Mass-Ratio Inspirals.* [arXiv:2026.23456](https://arxiv.org/abs/2026.23456) <em>(arXiv preprint)</em>
- **L. Lui**, Z. Zhang, A. Torres-Orjuela. (2026). *A Dark Matter Masquerade: Degeneracies in Black Hole and Accretion Inference from X-ray Reflection Measurements and Prospects for Compact Dark Matter.* [arXiv:2026.34567](https://arxiv.org/abs/2026.34567) <em>(arXiv preprint)</em>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
  // Interactive Chart.js pie chart with Inspire fallback counts and arXiv category
  (function(){
    const ctx = document.getElementById('journalPieChart').getContext('2d');

    // Fallback initial counts (guaranteed to show something quickly)
    const fallbackCounts = {
      'Phys. Rev. Lett.': 1,
      'Astrophys. J.': 1,
      'Phys. Rev. D': 1,
      'arXiv (preprints)': 3
    };

    const palette = ['#2f7f93','#52adc8','#ee5f5b','#7a8288','#62c462','#f89406','#af7aa1','#9c755f'];

    function buildLegend(containerId, labels, colors, values){
      const container = document.getElementById(containerId);
      if(!container) return;
      container.innerHTML = '';
      labels.forEach((label,i)=>{
        const span = document.createElement('span');
        span.innerHTML = `<i class="swatch" style="background:${colors[i]||'#ccc'}"></i> ${label}: ${values[i]}`;
        container.appendChild(span);
      });
    }

    // Create chart with initial data
    const labels0 = Object.keys(fallbackCounts);
    const data0 = labels0.map(l=>fallbackCounts[l]);
    const chart = new Chart(ctx, {
      type: 'pie',
      data: { labels: labels0, datasets: [{ data: data0, backgroundColor: palette.slice(0, labels0.length), borderColor:'#fff', borderWidth:1 }] },
      options: {
        responsive:true,
        maintainAspectRatio:false,
        plugins: {
          legend: { position: 'bottom', labels: { usePointStyle: true } },
          tooltip: { callbacks: { label: ctx => `${ctx.label}: ${ctx.parsed}` } }
        }
      }
    });

    // render initial legend
    buildLegend('publicationChartLegend', labels0, palette, data0);

    // Try to fetch Inspire data and update chart (non-blocking)
    async function fetchAndUpdate(){
      try{
        const authorId = 2960480; // user-provided author
        const url = `https://inspirehep.net/api/literature?authors=${authorId}&size=1000&fields=publication_info,dois,arxiv_eprints,titles`;
        const res = await fetch(url);
        if(!res.ok) throw new Error('Inspire fetch failed: '+res.status);
        const json = await res.json();
        const records = json.hits?.hits || json._embedded?.records || json.records || [];

        const counts = {};
        records.forEach(rec => {
          const meta = rec.metadata || rec;
          const pubs = meta.publication_info || meta.publication || [];
          if(pubs && pubs.length){
            const p = pubs[0];
            const journal = p.journal_title || p.journal || p.journal_title_short || null;
            if(journal) { counts[journal] = (counts[journal]||0)+1; return; }
          }
          if(meta.dois && meta.dois.length){ counts['Published (no journal metadata)'] = (counts['Published (no journal metadata)']||0)+1; return; }
          if(meta.arxiv_eprints && meta.arxiv_eprints.length){ counts['arXiv (preprints)'] = (counts['arXiv (preprints)']||0)+1; return; }
          counts['Other'] = (counts['Other']||0)+1;
        });

        // If arXiv preprints exist in the page content (we already marked them), ensure counted
        // Merge counts with fallback so common labels persist
        const merged = Object.assign({}, fallbackCounts);
        Object.keys(counts).forEach(k => merged[k] = counts[k]);

        const labels = Object.keys(merged);
        const values = labels.map(l=>merged[l]);

        // Update chart data
        chart.data.labels = labels;
        chart.data.datasets[0].data = values;
        chart.data.datasets[0].backgroundColor = palette.slice(0, labels.length);
        chart.update();
        buildLegend('publicationChartLegend', labels, palette, values);

        // Now attach DOI/arXiv links to list items by fuzzy matching (best-effort)
        attachLinks(records.map(r=>({metadata:r.metadata||r}))); // pass raw records

      }catch(err){
        console.warn('Inspire data not available (client-side). Using fallback counts.', err);
      }
    }

    function normalize(s){ return (s||'').toLowerCase().replace(/[\W_]+/g,' ').trim(); }
    function tokenOverlap(a,b){
      const A = new Set(normalize(a).split(' ').filter(x=>x.length>3));
      const B = new Set(normalize(b).split(' ').filter(x=>x.length>3));
      let c=0; for(const x of A) if(B.has(x)) c++; return c;
    }

    function attachLinks(records){
      try{
        const lis = Array.from(document.querySelectorAll('.publication-list li'));
        const recInfos = records.map(r=>{
          const meta = r.metadata || {};
          const title = (meta.titles && meta.titles[0] && (meta.titles[0].title||meta.titles[0])) || meta.title || '';
          const doi = (meta.dois && meta.dois[0] && (meta.dois[0].value||meta.dois[0])) || null;
          const arxiv = (meta.arxiv_eprints && meta.arxiv_eprints[0] && (meta.arxiv_eprints[0].value||meta.arxiv_eprints[0].arxiv_id||meta.arxiv_eprints[0])) || null;
          return { title, doi, arxiv };
        });

        const taken = new Set();
        lis.forEach(li => {
          const text = li.textContent || '';
          // if already has a link in bracket, skip
          if(li.querySelector('a')) return;
          let best=null, bestScore=0;
          recInfos.forEach((r,i)=>{
            if(taken.has(i) || !r.title) return;
            const score = tokenOverlap(text, r.title);
            if(score>bestScore){ bestScore=score; best=i; }
          });
          if(best !== null && bestScore>=2){
            const r = recInfos[best]; taken.add(best);
            const url = r.doi ? `https://doi.org/${encodeURIComponent(r.doi)}` : (r.arxiv ? `https://arxiv.org/abs/${encodeURIComponent(r.arxiv)}` : null);
            if(url){
              // replace first bracketed citation if present
              if(/\[[^\]]+\]/.test(li.innerHTML)){
                li.innerHTML = li.innerHTML.replace(/\[([^\]]+)\]/, `<a href="${url}" target="_blank" rel="noopener">[$1]</a>` + (r.arxiv && !r.doi ? ' <em>(arXiv preprint)</em>' : ''));
              } else {
                li.innerHTML += ` <a href="${url}" target="_blank" rel="noopener">${r.doi? 'DOI' : 'arXiv'}</a>`;
              }
            }
          } else {
            // Try detect explicit arXiv id in text and link it
            const m = text.match(/arxiv[:\s]?([0-9]{4}\.\d{4,5}|[a-z\-]+\/[0-9]{7})/i);
            if(m){ const aid=m[1]; li.innerHTML = li.innerHTML.replace(/\[([^\]]+)\]/, `<a href="https://arxiv.org/abs/${aid}" target="_blank" rel="noopener">[$1]</a> <em>(arXiv preprint)</em>`); }
          }
        });
      }catch(e){ console.warn('attachLinks failed', e); }
    }

    // Start async update
    fetchAndUpdate();

  })();
</script>
