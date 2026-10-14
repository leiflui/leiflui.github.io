---
layout: archive
title: "Research"
permalink: /research/
author_profile: true
---

![My Image](images/BH_shadow.png) <br>
*FIG 1. g-factor (energy-shift) contour showing the black-hole (BH) shadow. The observer is at* \\((r_o,\theta_o)=(2000M, 80^{\circ})\\) *and the BH spin is* \\(a=0.9\\). *This figure is generated using [PyHole](https://gitlab.com/EuropeanSpaceAgency/PyHole) via the ray-tracing of null geodesics onto a disk and calculating the change in the 4-momentum due to the rotation of the disk.*

I like solving puzzles, so physics is the natural place to harness my creative energy. I enjoy learning new mathematical techniques and applying them to real-life systems. Currently, my main research area is black-hole (BH) physics, but from time to time, I do enjoy learning about other interesting areas of physics like fluid dynamics, electrodynamics, complex systems, etc. The most exciting part is when I get to integrate ideas that I learn from other disciplines with my research on BHs. Below, I provide an overview of my current projects, and some thoughts that keep me up at night...

<!-- Research card grid: 3 columns x 2 rows with hover overlays. -->

<style>
.research-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin: 1.5rem 0;
}
.research-card {
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.25);
  min-height: 160px;
}
.research-card img {
  width: 100%;
  height: 220px;
  object-fit: cover;
  display: block;
}
.research-overlay {
  position: absolute;
  inset: 0; /* top:0; right:0; bottom:0; left:0 */
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.35);
  color: #fff;
  font-weight: 600;
  font-size: 1.05rem;
  text-align: center;
  padding: 0.75rem;
  opacity: 0;
  transition: opacity 200ms ease-in-out;
}
.research-card:hover .research-overlay,
.research-card:focus-within .research-overlay {
  opacity: 1;
}
.research-link {
  color: inherit;
  text-decoration: none;
  display: block;
}
@media (max-width: 900px) {
  .research-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .research-grid { grid-template-columns: 1fr; }
  .research-card img { height: 180px; }
}
</style>

<div class="research-grid">
  <a class="research-link" href="/research/emris-in-astrophysical-environments/">
    <div class="research-card" tabindex="0">
      <img src="/images/research/emris.jpg" alt="EMRIs in Astrophysical Environments">
      <div class="research-overlay">EMRIs in Astrophysical Environments</div>
    </div>
  </a>

  <a class="research-link" href="/research/bh-spectroscopy-in-astrophysical-environments/">
    <div class="research-card" tabindex="0">
      <img src="/images/research/bh_spectroscopy.jpg" alt="BH Spectroscopy in Astrophysical Environments">
      <div class="research-overlay">BH Spectroscopy in Astrophysical Environments</div>
    </div>
  </a>

  <a class="research-link" href="/research/grhd-grmhd-simulations/">
    <div class="research-card" tabindex="0">
      <img src="/images/research/grhd_grmhd.jpg" alt="GRHD/GRMHD Simulations">
      <div class="research-overlay">GRHD / GRMHD Simulations</div>
    </div>
  </a>

  <a class="research-link" href="/research/modeling-xray-signatures-near-smbhs/">
    <div class="research-card" tabindex="0">
      <img src="/images/research/xray_signatures.jpg" alt="Modeling X-ray Signatures near SMBHs">
      <div class="research-overlay">Modeling X-ray Signatures near SMBHs</div>
    </div>
  </a>

  <a class="research-link" href="/research/modeling-em-signals-from-gw-sources/">
    <div class="research-card" tabindex="0">
      <img src="/images/research/em_signals_gw.jpg" alt="Modeling EM Signals from GW Sources">
      <div class="research-overlay">Modeling EM Signals from GW Sources</div>
    </div>
  </a>

  <a class="research-link" href="/research/problems-in-cosmology/">
    <div class="research-card" tabindex="0">
      <img src="/images/research/cosmology.jpg" alt="Problems in Cosmology">
      <div class="research-overlay">Problems in Cosmology</div>
    </div>
  </a>
</div>
