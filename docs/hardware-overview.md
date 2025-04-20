# Hardware Overview

This page provides a brief introduction to the specialized hardware systems used in the OpenScope Community Predictive Processing project at the Allen Institute. For detailed specifications and technical information, please follow the links to each system's dedicated documentation page.

## Recording Systems

The project employs three advanced neural recording platforms, each offering unique capabilities for studying predictive processing at different scales:

<!-- Image placeholder - will be added when available -->
<!-- ![Hardware Recording Systems](img/hardware_systems_placeholder.png) -->

### SLAP2 (Swept Line Active Polarization)

The SLAP2 microscope is designed for ultra-fast subcellular imaging, capable of recording from arbitrary sets of pixels across multiple sample planes at speeds up to 220 Hz.

[→ Learn more about SLAP2 Hardware](hardware/allen_institute_slap2_hardware.md)

### Neuropixels Probes

Neuropixels technology enables high-density electrophysiological recordings with hundreds of simultaneous recording sites distributed across multiple brain regions, providing millisecond-precision spike timing.

[→ Learn more about Neuropixels Hardware](hardware/allen_institute_neuropixels_hardware.md)

### Mesoscope

The Allen Institute's Dual-Beam Mesoscope (Multiscope) enables simultaneous multi-plane calcium imaging across multiple cortical regions and depths, significantly increasing data collection throughput.

[→ Learn more about Mesoscope Hardware](hardware/allen_institute_mesoscope_hardware.md)

## Complementary Capabilities

These three recording systems provide complementary information about neural activity:

| System | Spatial Resolution | Temporal Resolution | Coverage | Cell Type Specificity |
|--------|-------------------|---------------------|----------|------------------------|
| SLAP2 | Subcellular | Very high (~5ms) | Single area, targeted cells | High |
| Neuropixels | Single-cell | Highest (<1ms) | Multiple areas, depth spanning | Low |
| Mesoscope | Cellular | Moderate (~90ms) | Multiple areas, multiple depths | High |

## Integration with Experimental Design

All hardware platforms are integrated with standardized stimulus delivery systems to ensure comparability across experiments. For details on stimulus implementation, see the [Bonsai Instructions](stimuli/bonsai_instructions.md).