# Project Plan

This document outlines the project plan for investigating neural mechanisms of predictive processing as part of the OpenScope community project.

## Overview

The OpenScope Community Predictive Processing project involves a series of experiments designed to investigate how the brain processes predictions and prediction errors. The project aims to resolve existing conflicts in the field by systematically testing whether different types of mismatch stimuli engage shared or distinct neural mechanisms across species.

For more extensive details, see our [Detailed Experimental Plan](detailed-experimental-plan.md) document.

## Scientific Rationale

Predictive processing theories propose that the brain continuously predicts sensory inputs and highlights prediction errors. However, current experimental and theoretical findings show both convergences and divergences:

**Convergences:**
- Top-down inputs shape mismatch signals
- Inhibitory interneurons play crucial roles in prediction errors
- Cortical layers show differential involvement in predictive processing

**Divergences:**
- The role of species-specific hierarchies (mouse vs. primate)
- Modality-dependent layer roles in processing prediction errors
- Implementation of predictive coding in neural circuits

To address these knowledge gaps, our experiments are designed to test specific hypotheses about how the brain generates and processes prediction errors.

## Key Research Questions

1. Do different types of mismatch stimuli engage shared or distinct neural mechanisms?
2. How do excitatory and inhibitory neurons contribute to different types of prediction errors?
3. Which computational primitives (stimulus adaptation, dendritic computation, E/I balance, hierarchical processing) are central to predictive processing?
4. How do prediction error mechanisms differ across species?

## Experimental Paradigms

Based on the current literature reviewed in our paper (Neural mechanisms of predictive processing: a collaborative community experiment through the OpenScope program), we will use several complementary paradigms designed to engage different prediction mechanisms:

<figure>
  <img src="../img/paper/arXiv_ Neural mechanisms of predictive processing_figure10.png" alt="Figure 10: Stimulus design">
  <figcaption>Figure 10: Stimulus design. Our experimental design includes four different session contexts (standard mismatch, sensorimotor mismatch, sequence mismatch, and temporal mismatch) with five types of oddballs: drifting grating halt, two alternative drifting orientations, an omission, and temporal jittered oddballs.</figcaption>
</figure>

### Standard Mismatch Paradigm

This paradigm examines how the brain responds to violations of expectations in stimulus sequences under passive viewing conditions.

- **Stimuli**: Visual gratings presented with regular patterns that are occasionally violated
- **Implementation**: 
  - Standard stimuli: Repeated presentation of gratings with the same orientation/spatial frequency
  - Deviant stimuli: Unexpected changes in grating orientation (45° or 90°), halted motion (0 Hz), or blank screens
  - Ratio: 120:1 (standard:deviant)

### Sensorimotor Mismatch Paradigm

This paradigm tests how neural responses change when self-generated motor actions lead to unexpected sensory outcomes.

- **Setup**: Animals run on a wheel with visual stimuli coupled to their movement
- **Conditions**:
    - Standard: Visual flow synchronized with running speed
    - Deviant: Visual flow speeds up, slows down, or decouples from running
    - Control: Passive viewing of matched visual flow patterns

### Sequence Mismatch Paradigm

This paradigm examines how the brain detects violations in learned sequences of stimuli.

- **Setup**: Animals habituated to specific sequences of 4 stimuli
- **Implementation**:
    - Sequences repeat once per second for 37 minutes
    - Deviant stimuli introduced in the third position of the sequence
    - Controls for context-dependent prediction

### Temporal Mismatch Paradigm

This paradigm investigates how the brain responds to unexpected timing changes in stimulus presentation.

- **Setup**: Alternating blocks of fixed vs. jittered timing
- **Implementation**:
    - Standard: 250ms stimulus duration, 500ms ISI
    - Deviant: 150ms or 350ms stimulus duration
    - Focus on timing predictability rather than stimulus identity

## Recording Techniques

We employ three complementary recording approaches to investigate predictive processing at different spatial and temporal scales:

### SLAP2 (Scanned Line Angular Projection)

- Ultra-fast subcellular imaging (220 Hz)
- Cellular-level recording with ability to track specific cell types and dendritic compartments
- Allows investigation of apical dendrite roles in integrating top-down and bottom-up signals

### Neuropixels Probes

- High-density electrophysiological recordings (>380 channels)
- Millisecond-precision spike timing across hundreds of neurons
- Simultaneous recording from multiple brain regions and layers
- Captures both spiking activity and local field potentials

### Mesoscope

- Wide-field calcium imaging across multiple cortical regions
- Simultaneous multi-plane imaging (4 depths across 2 areas)
- Tracking of the same neural populations across different experimental sessions

## Species and Brain Regions

### Mice
- Primary visual cortex (V1)
- Higher visual areas (LM, AL)
- Motor areas (M1, M2)
- Targeted recordings from specific cell types using transgenic lines:
    - Excitatory neurons: Slc17a7-IRES2-Cre lines
    - Inhibitory neurons: Sst-IRES-Cre, Vip-IRES-Cre lines

### Primates (Collaborative Studies)
- Homologous visual cortical areas (V1, V2, V4)
- Prefrontal cortex
- Comparative analysis with mouse data to address species differences

## Data Analysis Framework

Our analysis plan is structured to address three main scientific questions aligned with our review paper (Neural mechanisms of predictive processing: a collaborative community experiment through the OpenScope program). For complete analysis details, see our separate [Analysis Plan](analysis-plan.md) document.

### I. What kind of information is encoded by mismatch responses?

We will determine whether mismatch responses represent:

- **Multiplicative novelty**: Stimulus-specific enhancement for novel stimuli (response scales with tuning)
- **Additive novelty**: A generalized "alert" signal (uniform response regardless of stimulus preference)
- **Subtractive novelty**: Difference between expected vs. actual stimulus (activity reflects prediction error)

This analysis will help us understand the computational principles underlying prediction error signals and determine whether the same information coding scheme is used across different paradigms.

### II. Distinguish between two categories of prediction made by neurons

We will distinguish between:
- A. Detailed predictions about the identity of the upcoming stimulus
- B. Deviation of stimulus probability from the expected stimulus ensemble, often described in the literature as "adaptation". This empirical outcome could be interpreted as a form of refutation of the hypothesis that predictive computation was involved in the experimental conditions tested.

Our analyses will include:
- Comparing responses to the same mismatch stimulus across different conditions (closed loop, open loop, control)
- Calculating decoding performance and mutual information for individual mismatch stimuli versus novelty per se
- Examining the emergence of prediction signals in both single neurons and neural populations
- Testing multiple hypotheses including predictive coding vs. static tuning, predictive activity, pattern completion, and changes in population representation structure

### III. Mismatch responses across different types of predictions

We will compare neural responses across our five experimental paradigms to determine:

- Whether common neural ensembles encode different types of prediction errors
- If specialized circuits exist for different mismatch types (orientation, motion, temporal, omission)
- How response dynamics differ between passive oddball, sensorimotor, and sequence-based predictions
- Whether prediction errors rely on common or distinct computational mechanisms

This comparison will help resolve the question of whether there's a unified prediction error mechanism or multiple specialized mechanisms in the brain.

## Data Sharing and Community Engagement

All data will be:
- Formatted according to Neurodata Without Borders (NWB) standards
- Shared openly through the DANDI archive
- Accompanied by comprehensive metadata and analysis code
- Available for community analysis to foster iterative refinement

## Current Status and Timeline

For current experimental progress, please refer to:
- [Experiment summaries](experiment-summary.md) for details on completed sessions
- [Project tracking page](project-tracking.md) for overall progress

## References

1. [Neural mechanisms of predictive processing: a collaborative community experiment through the OpenScope program](https://arxiv.org/abs/2504.09614)

## Related Documents

- **[Detailed Experimental Plan](detailed-experimental-plan.md)**: Comprehensive methodology and experimental design details
- **[Analysis Plan](analysis-plan.md)**: Methods for analyzing the collected data
- **[Experiment Summary](experiment-summary.md)**: Overview of all conducted and planned experiments
- **[Hardware Overview](hardware-overview.md)**: Information about the recording platforms used
- **[Project Tracking](project-tracking.md)**: Current progress and status of project components

<!-- DISCUSSION_LINK_START -->
<div class="discussion-link">
    <hr>
    <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions/new?category=q-a&title=Discussion%3A%20experimental-plan" target="_blank">
            💬 Start a discussion for this page on GitHub
        </a>
        <span class="note">(A GitHub account is required to create or participate in discussions)</span>
    </p>
</div>
<!-- DISCUSSION_LINK_END -->
