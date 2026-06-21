---
layout: archive
title: "Research"
permalink: /research/
author_profile: true
---

![My Image](images/BH_shadow.png) <br>
*FIG 1. g-factor (energy-shift) contour showing the black-hole (BH) shadow. The observer is at* \\((r_o,\theta_o)=(2000M, 80^{\circ})\\) *and the BH spin is* \\(a=0.9\\). *This figure is generated using [PyHole](https://gitlab.com/EuropeanSpaceAgency/PyHole) via the ray-tracing of null geodesics onto a disk and calculating the change in the 4-momentum due to the rotation of the disk.*

I like solving puzzles, so physics is the natural place to harness my creative energy. I enjoy learning new mathematical techniques and applying them to real-life systems. Currently, my main research area is black-hole (BH) physics, but from time to time, I do enjoy learning about other interesting areas of physics like fluid dynamics, electrodynamics, complex systems, etc. The most exciting part is when I get to integrate ideas that I learn from other disciplines with my research on BHs. Below, I provide an overview of my current projects, and some thoughts that keep me up at night...

## Extreme-Mass-Ratio Inspirals (EMRIs)
------
![LoopingDemo](images/kerr_geodesics_rotating_trails_9_16_long.gif)

*FIG. 2: EMRI with mass ratio* \\(q=5\times 10^{-6}\\) *, where red and blue trails are the trajectories for spinning and non-spinning secondary in Kerr spacetime, respectively. The orbital parameters are* \\((a, p, e, x)=(0.95M,8M, 0.65, \cos(\pi/4))\\). *The trajectory of the spinning secondary is governed by the Matthison-Papapetrou-Dixon (MPD) equations, and has dimensionless spin* \\(\chi=0.95\\). *The geodesics for blue trail is computed using [kerrgeopy](https://github.com/BlackHolePerturbationToolkit/KerrGeoPy) and are evolved using [pybhpt](https://github.com/znasipak/pybhpt). The red trail is computed using my own adapted version of [kerrgeopy](https://github.com/BlackHolePerturbationToolkit/KerrGeoPy) using the analytical MPD solution from [Skoupý & Witzany](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.134.171401) and is evolved using [pybhpt](https://github.com/znasipak/pybhpt) and [KerrSpinningFluxes](https://github.com/vskoupy/KerrSpinningFluxes).*

Extreme-mass-ratio inspirals (EMRIs) are binary systems with mass ratio \\(q\lesssim 10^{-5}\\), consisting of a stellar/intermediate-mass secondary (i.e. black holes (BHs), neutron stars (NSs), white dwarfs (WDs), etc.), gravitationally bound to a massive black hole (MBH) of mass \\(M\gtrsim 10^{5}M_{\odot}\\). For orbital motion on short timescales, we typically opt for the test particle approximation. That is, we assume that the secondary's self-gravity is small and negligible when considering orbits over a few cycles. However, EMRIs can have orbital timescales of the order of ~1000 years, so the small corrections due to the secondary's self-gravity can accumulate over long timescale to produce large deviations in the orbital morphology. These small changes in the orbit are modelled using BH perturbation and self-force (SF) theory. This is where we take the exact, analytical Kerr solution for spinning BHs, and perturb this solution by deforming the spacetime due to the secondary's self-gravity. This is done by solving the Teukolsky equation and adding a self-force term to the geodesic equation. In FIG. 2, we compare the orbital evolution for an EMRI with a spinning (red trail) versus a non-spinning secondary (blue trail), where the former evolves due to gravitational radiation and spin-curvature coupling, and solely evolves due to gravitational radiation. We can clearly see how small secular evolutions can change the orbit over long timescales!

## Gravitational Wave (GWs) from EMRIs
------
EMRIs are one of the primary targets for space-based millihertz gravitational-wave (GW) detectors such as LISA, TianQin, and Taiji. As seen in FIG. 2, EMRIs have complex orbits, but what makes them so remarkable is their gravitational-wave (GW) signals, as this would allow us to test physics near a MBH. EMRI orbits have 2 phases: The first of which is the adiabatic inspiral phase, where the secondary is on a stable orbit and slowly inspirals towards a MBH due to GW radiation. 
![LoopingDemo](images/emri_orbit_and_waveform.gif)
*FIG. 3: EMRI on stable orbit and its GW signal. The orbital parameters are* \\((a, p, e, x)=(0.95M,8M, 0.65, \cos(\pi/4))\\). *The trajectory and waveform are evolved using [kerrgeopy](https://github.com/BlackHolePerturbationToolkit/KerrGeoPy) and [pybhpt](https://github.com/znasipak/pybhpt).*

The second phase is when the orbit loses a sufficient amount of energy and angular momentum such that the orbit is no longer stable and plunges towards the MBH. 

![LoopingDemo](images/plunge_waveform.gif)
*FIG. 4: EMRI trajectory plunge with mass ratio* \\(q=4\times 10^{-7}\\) *and its GW signal. The plunge time to be at \\(t=0\\), and the initial constants of motion are* \\((a, \mathscr{E}, \mathscr{L}, \mathscr{Q})= (0.8,0.95,2.6, 0.5)\\). *The trajectory and waveform are evolved using [kerrgeopy](https://github.com/BlackHolePerturbationToolkit/KerrGeoPy) and my own time-domain Teukolsky solver [TeukolPy](https://github.com/leiflui/TeukolPy).*

## Environmental Effects (EEs) on EMRI GWs
As mentioned previously, the long orbital timescales allow for small perturbations to manifest as considerable changes in the orbital evolution. These changes modify the GW signals, which can be picked up by our space-based detectors and to be subsequently analyzed. Apart from GW radiation and gravitational SFs, there can be perturbative changes due to astrophysical environmental effects (EEs) such as aerodynamical forces and resonant effects from gases in accretion disks, changes in the spacetime due to dense dark matter halos, tidal effects from other orbiting bodies in globular clusters, etc. Part of my research is to understand how these EEs are imprinted on the GW signals. 

## Probing Strong Gravity with EMRIs

## Other Thoughts and Ideas





