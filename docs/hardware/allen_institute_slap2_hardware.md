# SLAP2 Microscope Hardware

## Overview

The SLAP2 (Scanned Line Angular Projection) microscope is an advanced imaging system developed by the Allen Institute for Neural Dynamics as part of their Single-Cell Computation project. This cutting-edge technology is specifically designed to record neural activity at the synaptic level with unprecedented speed and precision in the living brain.

## SLAP2 in Action

<div style="padding:56.25% 0 0 0;position:relative;"><iframe src="https://player.vimeo.com/video/1015679273?h=d9a03585be&badge=0&autoplay=1&loop=1&player_id=0&app_id=58479" style="position:absolute;top:0;left:0;width:100%;height:100%;" frameborder="0" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe></div>
<script src="https://player.vimeo.com/api/player.js"></script>
<p><em>Video: SLAP2 microscope recording iGluSnFR3 activity (synaptic activity in red, structure in cyan) from the cell body and dendrites of a Layer 2/3 neuron in mouse motor cortex. These dendrites were imaged at 220 Hz.</em></p>

## Technical Capabilities

Unlike conventional microscopes, SLAP2 offers several key advantages:

- **Targeted Pixel Selection**: SLAP2 can image any desired set of pixels in its field of view, with time requirements proportional to the number of pixels selected, without additional access time costs for each pixel.
- **Superior Speed**: 20-200 times faster for imaging synaptic activity compared to conventional microscopes.
- **High-volume Recording**: Ability to record from hundreds to thousands of synapses at the pace of neuronal computation.
- **Real-time Motion Correction**: Incorporates high-performance online motion correction to follow imaged synapses in 3D even as the brain moves during behavior.
- **Multi-plane Imaging**: Records from arbitrary sets of pixels across multiple sample planes.

SLAP2 is primarily used to investigate neural computations by measuring:
- Patterns of input arriving at thousands of input synapses onto individual neurons
- The simultaneous firing output of those neurons

## Technical Design

The SLAP2 microscope uses:
- Two-photon imaging technology based on scanning of pulsed infrared lasers
- A novel laser scanning system optimized for imaging large numbers of synapses in the living, moving brain
- Specialized genetically encoded indicators (like iGluSnFR3) to measure synaptic activity

## Synchronization with Other Hardware

The SLAP2 system is fully synchronized with:

- Running wheel and behavioral measurements
- Visual stimulus presentation through the Bonsai framework
- Data acquisition systems for behavioral tracking

## Behavior Platform Integration

The SLAP2 system incorporates a standardized behavior platform for head-fixed mice:

<figure>
  <img src="../img/slap2/slap2_behavior.png" alt="SLAP2 Behavior Platform" width="100%" style="max-width: 800px; height: auto;">
  <figcaption>The behavior platform mounted on the SLAP2 microscope. This setup allows simultaneous recording of neural activity at synaptic resolution while the mouse engages with visual stimuli and runs on the wheel.</figcaption>
</figure>


## Related Hardware

- [Behavior Platform](behavior_training.md)
- [Mesoscope Hardware](allen_institute_mesoscope_hardware.md)
- [Neuropixels Hardware](allen_institute_neuropixels_hardware.md)

## Availability

SLAP2 microscope kits and software are now being distributed by MBF Biosciences for wider research use.

## References

For more detailed information about SLAP2 and the Single-Cell Computation project, visit the [Allen Neural Dynamics website](https://www.allenneuraldynamics.org/projects/single-cell-computation).

## Related Documents

- **[Hardware Overview](../hardware-overview.md)**: Summary of all recording platforms used in the project
- **[Experimental Plan](../experimental-plan.md)**: How SLAP2 is used in different experimental paradigms
- **[Experiment Summary](../experiment-summary.md)**: Overview of experiments conducted with SLAP2

<!-- DISCUSSION_LINK_START -->
<div class="discussion-link">
    <hr>
    <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions/new?category=q-a&title=Discussion%3A%20hardware/allen_institute_slap2_hardware" target="_blank">
            💬 Start a discussion for this page on GitHub
        </a>
        <span class="note">(A GitHub account is required to create or participate in discussions)</span>
    </p>
</div>
<!-- DISCUSSION_LINK_END -->
