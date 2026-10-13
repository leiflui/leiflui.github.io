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


<!-- Chart.js and improved Inspire HEP automatic linking script -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
  // Improved client-side enrichment:
  // - Robust fallback: if Inspire API is blocked/fails, build chart from page contents
  // - Fuzzy matching between page items and Inspire records using token overlap so truncated titles still match
  // - Directly link arXiv: IDs found in the page

  function normalize(s) {
    return (s||'').toLowerCase().replace(/\s+/g,' ').replace(/[\u2018\u2019\u201c\u201d]/g, "'").replace(/[^\w \-:\.\/]/g,'').trim();
  }

  function words(s){
    return normalize(s).split(/\s+/).filter(w => w.length>3);
  }

  function tokenOverlap(a,b){
    const A = new Set(words(a));
    const B = new Set(words(b));
    let common=0; for (const x of A) if (B.has(x)) common++;
    return common;
  }

  function parseBracketCitation(text){
    // Find first bracketed content
    const m = text.match(/\[([^\]]+)\]/);
    return m ? m[1].trim() : null;
  }

  function buildChartFromCounts(counts){
    const labels = Object.keys(counts);
    const values = labels.map(l => counts[l]);
    const canvas = document.getElementById('journalChartCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const palette = ['#4e79a7','#f28e2b','#e15759','#76b7b2','#59a14f','#edc949','#af7aa1','#ff9da7','#9c755f'];
    // Clear previous chart area
    canvas.width = canvas.clientWidth * devicePixelRatio;
    canvas.height = canvas.clientHeight * devicePixelRatio;
    if (window._journalChart) { window._journalChart.destroy(); window._journalChart=null; }
    window._journalChart = new Chart(ctx, {
      type: 'pie', data: { labels, datasets:[{ data: values, backgroundColor: palette.slice(0,labels.length), borderColor:'#fff', borderWidth:1 }] },
      options: { responsive: true, maintainAspectRatio:false, plugins:{ legend:{position:'bottom'}, tooltip:{callbacks:{label: c=>`${c.label}: ${c.parsed}`}} } }
    });
  }

  async function fetchInspireAuthorPublications(authorId, pageSize=250){
    // Try the literature endpoint by author id using the author resource if available
    // Multiple possible shapes are handled by extractRecordInfo
    const url = `https://inspirehep.net/api/literature?authors=${authorId}&size=${pageSize}&fields=publication_info,dois,arxiv_eprints,titles`;
    const r = await fetch(url);
    if (!r.ok) throw new Error('Inspire fetch failed: ' + r.status);
    return await r.json();
  }

  function extractRecordInfo(rec){
    const meta = rec.metadata || rec;
    const titles = (meta.titles && meta.titles.length) ? meta.titles.map(t=>t.title||t) : (meta.title ? [meta.title] : []);
    const title = titles.length?titles[0]:'';
    let doi=null; if (meta.dois && meta.dois.length) doi = meta.dois[0].value || meta.dois[0];
    let arxiv=null; if (meta.arxiv_eprints && meta.arxiv_eprints.length) arxiv = meta.arxiv_eprints[0].value || meta.arxiv_eprints[0].arxiv_id || meta.arxiv_eprints[0];
    // publication info
    let journal=null; let year=null;
    const pubs = meta.publication_info || meta.publication || [];
    if (pubs && pubs.length){
      const p = pubs[0];
      journal = p.journal_title || p.journal || p.journal_title_short || p.title || null;
      year = p.year || p.pubyear || null;
      // sometimes volume/page are present
      const volume = p.volume || p.journal_volume || null;
      const page = p.page || p.page_start || null;
      if (volume && page) journal = `${journal} ${volume}, ${page}`;
    }
    return { title, doi, arxiv, journal, year };
  }

  async function enrichPublications(){
    const lis = Array.from(document.querySelectorAll('li'));
    // initial counts from page: count bracketed citations
    const counts = {};
    lis.forEach(li=>{
      const bc = parseBracketCitation(li.textContent);
      if (!bc) return;
      // detect arXiv id
      const arxivMatch = bc.match(/arxiv[:\s]?([0-9]{4}\.\d{4,5}|[a-z\-]+\/[0-9]{7})/i);
      if (arxivMatch) { counts['arXiv (preprints)'] = (counts['arXiv (preprints)']||0)+1; return; }
      // take journal up to first digit (volume/year)
      const jMatch = bc.match(/^([^\d]+)\s*(\d.*)?$/);
      const jName = jMatch ? jMatch[1].trim() : bc;
      counts[jName] = (counts[jName]||0)+1;
    });

    // Render chart from page counts as a fallback immediately so visitors see something
    buildChartFromCounts(counts);

    // Try to fetch Inspire and refine counts + attach links
    try {
      const authorId = 2960480; // user-provided
      const raw = await fetchInspireAuthorPublications(authorId, 1000);
      const records = raw.hits?.hits || raw._embedded?.records || raw.records || [];
      const recs = records.map(extractRecordInfo).filter(r=>r.title);

      // Recompute counts from Inspire if we got useful journal names
      const inspireCounts = {};
      recs.forEach(r=>{
        if (r.journal) inspireCounts[r.journal] = (inspireCounts[r.journal]||0)+1;
        else if (r.arxiv) inspireCounts['arXiv (preprints)'] = (inspireCounts['arXiv (preprints)']||0)+1;
        else inspireCounts['Other'] = (inspireCounts['Other']||0)+1;
      });
      // if inspireCounts has entries, use them to update chart
      if (Object.keys(inspireCounts).length > 0) buildChartFromCounts(inspireCounts);

      // Now fuzzy-match records to list items and attach links
      const taken = new Set();
      // Precompute tokens for recs and lis
      const recTokens = recs.map(r=>({r, tokens: new Set(words(r.title))}));
      lis.forEach(li=>{
        const liText = li.textContent || '';
        const bc = parseBracketCitation(liText);
        // If bracket already looks like arXiv with id, link it directly
        const arxivMatch = (bc||'').match(/arxiv[:\s]?([0-9]{4}\.\d{4,5}|[a-z\-]+\/[0-9]{7})/i);
        if (arxivMatch){
          const aid = arxivMatch[1];
          const url = `https://arxiv.org/abs/${encodeURIComponent(aid)}`;
          li.innerHTML = li.innerHTML.replace(/\[([^\]]+)\]/, `<a href="${url}" target="_blank" rel="noopener">[$1]</a>` + ' <em>(arXiv preprint)</em>');
          return;
        }
        // find best matching record by token overlap
        let best=null, bestScore=0;
        const liTokens = words(liText);
        for (let i=0;i<recTokens.length;i++){
          if (taken.has(i)) continue;
          // compute overlap between li and rec title
          const overlap = tokenOverlap(liText, recTokens[i].r.title);
          if (overlap>bestScore){ bestScore=overlap; best=i; }
        }
        if (best !== null && bestScore >= 2){ // at least two token overlap
          const rec = recTokens[best].r;
          taken.add(best);
          const url = rec.doi ? `https://doi.org/${encodeURIComponent(rec.doi)}` : (rec.arxiv ? `https://arxiv.org/abs/${encodeURIComponent(rec.arxiv)}` : null);
          if (url){
            // Replace first bracket with link
            li.innerHTML = li.innerHTML.replace(/\[([^\]]+)\]/, `<a href="${url}" target="_blank" rel="noopener">[$1]</a>` + (rec.arxiv && !rec.doi ? ' <em>(arXiv preprint)</em>' : ''));
          }
        }
      });

    } catch (err){
      console.warn('Inspire fetch/processing failed, using page-derived counts. Error:', err);
      // we already rendered counts from the page, nothing else to do
    }
  }

  window.addEventListener('DOMContentLoaded', enrichPublications);
</script>
