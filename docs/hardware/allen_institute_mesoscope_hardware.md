# Allen Institute Mesoscope Hardware

## Overview

The Mesoscope is an advanced two-photon calcium imaging system developed by the Allen Institute for Neural Dynamics. This cutting-edge microscopy technology enables simultaneous multi-plane imaging of neural activity across multiple brain regions and depths, significantly increasing data collection throughput compared to conventional single-plane two-photon microscopes.

## Dual-Beam Technology

The Allen Institute uses a modified Mesoscope system, also referred to as a "Multiscope," which features innovative dual-beam technology. This design allows researchers to:

- Image multiple cortical depths simultaneously
- Record from two different brain areas in a single experiment
- Acquire data at higher throughput than conventional microscopes

## Technical Specifications

The Dual-Beam Mesoscope consists of three key components:

1. **Delay Line**: Splits the original laser beam into two separate beams and delays one beam by half a period of the excitation laser
2. **Secondary Z-Scanner**: Sends the two beams to different focal planes along the Z-axis
3. **Custom Demultiplexing Unit**: Separates fluorescence from the two planes based on the arrival time at the photodetector

### Key Features:

- **Laser Source**: Ti:Sapphire ultrafast laser (Chameleon Ultra II, Coherent)
- **Control Software**: Customized ScanImage software (VidrioTech) with an in-house developed Workflow Sequencing Engine
- **Imaging Rate**: 11 Hz per plane
- **Field of View**: Full 5mm field of view for targeting, 400-512 μm for recording

## Data Analysis

Data from the Mesoscope is processed through standardized pipelines that include:

- Motion correction
- ROI extraction
- Fluorescence trace extraction
- Deconvolution for estimating neural activity
- Registration to common coordinate frameworks

## Related Hardware

- [Behavior Platform](behavior_training.md)
- [SLAP2 Hardware](allen_institute_slap2_hardware.md)
- [Neuropixels Hardware](allen_institute_neuropixels_hardware.md)

## References

For more detailed information about the Allen Institute's Mesoscope technology:

- [Allen Neural Dynamics website](https://www.allenneuraldynamics.org/)

## Additional Resources

- [Visual Behavior 2P Technical Whitepaper (Allen Brain Observatory)](https://portal.brain-map.org/explore/circuits/visual-behavior-2p)

## Related Documents

- **[Hardware Overview](../hardware-overview.md)**: Summary of all recording platforms used in the project
- **[Experimental Plan](../experimental-plan.md)**: How the Mesoscope is used in different experimental paradigms
- **[Detailed Experimental Plan](../detailed-experimental-plan.md)**: Specific information about Mesoscope recording protocols

<!-- DISCUSSION_LINK_START -->
<div class="discussion-link">
    <hr>
    <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions/new?category=q-a&title=Discussion%3A%20hardware/allen_institute_mesoscope_hardware" target="_blank">
            💬 Start a discussion for this page on GitHub
        </a>
        <span class="note">(A GitHub account is required to create or participate in discussions)</span>
    </p>
</div>
<!-- DISCUSSION_LINK_END -->
