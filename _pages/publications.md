---
title: "Publications"
permalink: /publications/
author_profile: true
---
## Refereed Journal Articles:

<div class="journal-chart-container" style="max-width: 520px; margin: 1.5rem auto 2rem; height: 340px;">
  <canvas id="journalChartCanvas" aria-label="Journal publication counts" role="img"></canvas>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
  const journalCounts = [
    { journal: 'Phys. Rev. Lett.', count: 1 },
    { journal: 'Astrophys. J.', count: 1 },
    { journal: 'Phys. Rev. D', count: 1 }
  ];

  const labels = journalCounts.map(item => item.journal);
  const values = journalCounts.map(item => item.count);
  const palette = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc949', '#af7aa1', '#ff9da7'];

  window.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('journalChartCanvas');
    if (!canvas) return;

    new Chart(canvas, {
      type: 'pie',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: palette.slice(0, labels.length),
          borderColor: '#ffffff',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return context.label + ': ' + context.parsed + ' paper(s)';
              }
            }
          }
        }
      }
    });
  });
</script>

### Lead/Co-Lead Authored:
- **L. Lui**, L. V. Drummond, A. Torres-Orjuela. (2026). *Pitching Cosmic Curveballs: Environmental Effects on Extreme-Mass-Ratio Inspirals with Spinning Secondaries.* [Phys. Rev. Lett. 137, 121403]
- **L. Lui**, A. Torres-Orjuela, R. Kar Chowdhury, &  L. Dai. (2025). *Gravitational Wave Signatures of Quasi-Periodic Eruptions: LISA Detection Prospects for RX J1301.9+2747.* [Astrophys.J. 1004 (2025) 1]

### Co-Authored with Significant Contributions:
- Y. Yang, **L. Lui**, A. Torres-Orjuela, X. Chen. (2026). *Relativistic tidal dissipation and the gravitational-wave signal of a white dwarf orbiting an intermediate-mass black hole.* [Phys. Rev. D]

## Preprints:
- P. Amaro-Seoane, **L. Lui**, A. Torres-Orjuela, X. Chen. (2026). *Electromagnetic alignment and jet precession around supermassive black holes: Quasiperiodic oscillations in tidal disruption events.* [arXiv:2026.12345]
- **L. Lui**, A. K-.W. Chung, A. Torres-Orjuela. (2026). *Devoured by a Hairy Gargantua: Probing Massive Scalar Charges with Non-minimal Curvature Coupling with Extreme-Mass-Ratio Inspirals.* [arXiv:2026.23456]
- **L. Lui**, Z. Zhang, A. Torres-Orjuela. (2026). *A Dark Matter Masquerade: Degeneracies in Black Hole and Accretion Inference from X-ray Reflection Measurements and Prospects for Compact Dark Matter.* [arXiv:2026.34567]
