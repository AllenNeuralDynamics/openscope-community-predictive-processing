# Detailed experimental plan

This document provides a comprehensive experimental plan for investigating neural mechanisms of predictive processing as part of the OpenScope community project. The plan is designed to resolve existing conflicts between experimental and theoretical domains and deepen our understanding of the neural circuits underlying predictive processing.

## Background and scientific context

### Current state of predictive processing research

Predictive processing theories propose that the brain continuously builds and updates internal models of the world, using these models to predict incoming sensory signals. When predictions differ from actual inputs, the resulting prediction errors drive learning and perceptual updating. However, significant questions remain about how these processes are implemented in neural circuits.

Recent research has revealed that the brain may employ various mechanisms for predictive processing, which can differ depending on:

- The sensory modality (visual, auditory, somatosensory)
- The type of prediction being made (spatial, temporal, sensorimotor)
- The complexity and timescale of the prediction
- The species and brain region involved

Our review of the literature has identified several key computational primitives that may support predictive processing:

1. **Stimulus adaptation**: Neurons adjust their responses to recurring stimuli, potentially enhancing sensitivity to change
2. **Dendritic computation**: Integration of top-down and bottom-up inputs within a neuron's dendrites may support prediction error calculation
3. **Excitatory/inhibitory (E/I) balance**: Different inhibitory interneuron subtypes provide a framework for complex predictions and error signaling
4. **Hierarchical processing**: Multi-level processing across brain areas enables sophisticated, multi-modal predictions

## Key research hypotheses and questions

### Alternative hypotheses

We are testing two alternative hypotheses:

- **H0 (Multiple Mechanisms)**: Different types of prediction errors involve fundamentally distinct neural mechanisms, with specialized circuits for each type of mismatch processing.
- **H1 (Unified Mechanism)**: A common computational principle underlies all mismatch responses, with apparent differences reflecting implementation variations rather than distinct mechanisms.
  
### Primary research questions

At a finer level, we seek answer to the following questions: 

1. Do sequential, sensory-motor, and omission mismatch stimuli engage shared or distinct neural mechanisms?
2. How do these mechanisms differ across cortical layers, cell types, and brain regions?
3. Are prediction errors computed locally within a brain area or distributed across multiple areas?
4. How do predictive processing mechanisms differ between mice and primates?

## Experimental design

To systematically investigate different aspects of predictive processing, we've designed a stimulus set that includes several validated mismatch stimuli capable of engaging different neural mechanisms:

<figure>
  <img src="../img/paper/arXiv_ Neural mechanisms of predictive processing_figure10.png" alt="Figure 10: Stimulus design">
  <figcaption>Figure 10: Stimulus design. Our experimental design includes four different session contexts (standard mismatch, sensorimotor mismatch, sequence mismatch, and temporal mismatch) with five types of oddballs: drifting grating halt, two alternative drifting orientations, an omission, and temporal jittered oddballs. This design allows for fitting models of synaptic adaptation, positive and negative errors, short-term memory that could emerge through local recurrence, and E/I balance.</figcaption>
</figure>

#### Oddball types

Our experiments will feature sequences of drifting gratings with five types of oddball events:

1. **Orientation Oddballs**: Unexpected changes in grating orientation
    - Standard: 0° orientation drifting gratings
    - Deviant: 90° or 45° orientation drifting gratings

2. **Motion Oddballs**: Unexpected changes in drift speed
    - Standard: Consistent motion parameters
    - Deviant: halted motion

3. **Omission Oddballs**: Complete absence of expected stimulus

4. **Temporal Oddballs**: Unexpected timing of stimulus presentation
    - Standard: 250ms stimulus duration, 500ms ISI
    - Deviant: 150ms or 350ms stimulus duration

5. **Sensorimotor oddballs**: Unexpected sensory feedback during motor activity
    - Standard: Visual flow coupled to running speed
    - Deviant: Flow different than expected based on running speed
    - Implemented during active running periods

### Session contexts

These oddball stimuli will be presented in four different paradigms as described in our review paper "Neural mechanisms of predictive processing: a collaborative community experiment through the OpenScope program":

#### Session 1 – Standard oddball sequence

- Animals presented with series of drifting gratings (same orientation)
- Occasional oddball stimuli (orientation changes, omissions)
- Passive viewing condition

#### Session 2 – Sensorimotor mismatch (sensorimotor coupling)

- Animals run on wheel with visual flow coupled to movement
- Closed-loop visuo-motor coupling (running controls visual flow)
- Occasional mismatches between running and visual flow
- Same oddball types as Session 1
- Tests predictions based on self-generated sensory consequences

#### Session 3 - Complex sequence learning

- Animals habituated to specific sequences of 4 stimuli
- Oddball stimuli introduced in third position of sequence
- Controls for context-dependent prediction

#### Session 4 - Temporal prediction

- Focus on timing predictability rather than stimulus identity
- Shorter/longer duration stimuli serve as temporal oddballs

### Recording Approaches

To evaluate the relative contributions of different mechanisms, we will use three complementary recording approaches:

- Neuropixels Recordings

    - High-density electrophysiological recordings (384 channels)
    - Millisecond-precision spike timing
    - Simultaneous recording across cortical layers and areas
    - Implementation of optogenetic tagging for cell-type identification
    - Coverage of multiple regions in a single recording
    - Specific objectives:
        - Compare response latencies across areas to determine signal flow direction
        - Evaluate layer-specific responses across different prediction paradigms
        - Investigate oscillatory synchronization during prediction and error states
        - Examine inter-area coordination during prediction and error signaling

- Mesoscope Two-photon Imaging

    - Dual-beam technology for multi-plane imaging
    - Simultaneous recording from 4 depths across 2 areas
    - 11 Hz per plane imaging rate
    - Tracking same neural populations across sessions
    - Coverage of multiple visual areas (V1 and higher areas)
    - Specific objectives:
        - Evaluate excitatory and inhibitory response diversity across different prediction paradigms
        - Determine whether common neural ensembles participate in different prediction paradigms
        - Track changes in prediction signals over multiple sessions

- SLAP2 (Scanned Line Angular Projection) Two-Photon Imaging

    - Ultra-fast subcellular imaging (220 Hz)
    - Targeted recording of dendrites and somata simultaneously
    - Allows direct investigation of apical dendrite contributions
    - Specific objectives:
        - Determine whether prediction errors are computed at the level of single neurons
        - Test whether top-down predictions and bottom-up inputs are integrated in specific dendritic compartments
        - Examine how inhibitory interneurons shape prediction error signals

### Recorded brain regions in mice

- Primary visual cortex (V1)
- Secondary visual areas (LM, AL)
- Motor cortex (M1, M2)
- Prefrontal regions

### Recorded brain regions in primate

- V1, V2, V4
- MT/MST
- Prefrontal regions

### Experimental timeline in mice

Each mouse will undergo:

- Cranial window implantation and recovery
- Intrinsic signal imaging for area identification
- Habituation and task training (2-3 weeks)
- Multiple recording sessions (one session type per day)
- Mesoscope: 8-10 sessions per mouse
- Neuropixels: 4 sessions per mouse

## Analysis plan

This document focuses on the experimental design. For our detailed analysis approach, please see the [Analysis Plan](analysis-plan.md) document, which covers:

1. What kind of information is encoded by mismatch responses
2. Distinguishing between categories of predictions made by neurons
3. Comparing mismatch responses across different types of predictions
4. Computational modeling approaches

For a more concise overview of our approach, see the [Experimental Plan](experimental-plan.md).

## Expected outcomes and significance

This experimental plan will produce:

1. The first comprehensive dataset enabling direct comparison across different mismatch error signals
2. Resolution between alternative hypotheses regarding unified vs. distinct mechanisms
3. A detailed map of how prediction errors are encoded across cell types, layers, and regions
4. A pivotal resource for validating computational models of predictive processing

The resulting datasets, collected through the OpenScope program, will be shared openly with the neuroscience community via NWB files on the DANDI archive. This approach will enable model validation and community analysis, fostering iterative refinement of our understanding of the neural mechanisms underlying predictive processing.

## References

1. [Neural mechanisms of predictive processing: a collaborative community experiment through the OpenScope program](https://arxiv.org/abs/2504.09614)

## Related Documents

- **[Experimental Plan](experimental-plan.md)**: Concise overview of experimental paradigms and approaches
- **[Analysis Plan](analysis-plan.md)**: Detailed methods for analyzing the collected data
- **[Experiment Summary](experiment-summary.md)**: Overview of all conducted and planned experiments
- **[Hardware Overview](hardware-overview.md)**: Information about the recording platforms used

<!-- DISCUSSION_LINK_START -->
<div class="discussion-link">
    <hr>
    <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions/new?category=q-a&title=Discussion%3A%20detailed-experimental-plan" target="_blank">
            💬 Start a discussion for this page on GitHub
        </a>
        <span class="note">(A GitHub account is required to create or participate in discussions)</span>
    </p>
</div>
<!-- DISCUSSION_LINK_END -->
