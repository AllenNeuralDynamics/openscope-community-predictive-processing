# Sequence Mismatch Protocol

## Overview

The Sequence Mismatch Protocol investigates how the brain detects violations in learned sequences of stimuli. This paradigm examines whether the brain forms predictions about stimulus patterns and sequences, not just individual stimuli. The protocol presents animals with repeated sequences of stimuli to establish expectations, then occasionally introduces deviants that violate the learned sequence structure.

## Stimulus Structure

1. **Habituation Phase**: Animals are exposed to repeating sequences of 4 stimuli to establish learning.

2. **Testing Phase**: 
   - Standard sequences continue the learned pattern
   - Deviant sequences introduce unexpected stimuli at the third position
   - Omission trials occasionally remove an expected stimulus from the sequence

3. **Control Conditions**: Control sequences with matched stimulus properties but without established sequence expectations.

## Hardware Requirements

- SLAP2 imaging system or Neuropixels setup
- Behavior device with encoder/wheel for tracking animal movement
- Digital outputs for synchronization with recording equipment

## Stimulus Parameters

### Basic Parameters
- **Display Type**: Visual gratings with varying orientations
- **Spatial Frequency**: 0.04 cycles per degree
- **Temporal Frequency**: 2 Hz 
- **Contrast**: 1.0 (full contrast)
- **Size**: 90° (covering a large portion of the visual field)
- **Stimulus Duration**: 250 ms per element in the sequence
- **Inter-sequence Interval**: 500 ms between complete sequences

### Configurable Parameters
The protocol includes several parameters that can be adjusted:
- Sequence Length: Number of elements in each sequence (typically 4)
- Habituation Time: Minutes of habituation before introducing deviants (typically 20 minutes)
- Deviant Probability: Probability of deviant sequences (typically 0.05)
- Omission Probability: Probability of omission trials (typically 0.05)
- Number of Unique Sequences: Number of different sequences to use (typically 2-4)

## Experimental Design

### 1. Sequence Structure
The experiment establishes predictable sequences of stimuli:

- **Sequence Elements**: Four distinct grating orientations (0°, 45°, 90°, 135°) 
- **Sequence Types**: 2-4 unique sequences are used per session
- **Element Duration**: Each element appears for 250ms
- **Inter-element Interval**: No gap between elements within a sequence
- **Sequence Repetition**: Each sequence repeats once per second (with 500ms gap between sequences)

### 2. Habituation Phase
- Animals are exposed to the sequences for 20 minutes at the start of the session
- This establishes learning of the sequence structure
- No deviant sequences are presented during this phase

### 3. Testing Phase
The core of the experiment consists of:

- **Standard Sequences**: Continuation of the learned sequences (~90% of trials)
- **Deviant Sequences**: 
  - Unexpected stimulus at the third position in the sequence
  - Preserves the temporal structure but violates stimulus identity prediction
  - Occurs with ~10% probability

### 4. Control Conditions
- Random sequences matching stimulus statistics but without established expectations
- These control for sensory-specific adaptation effects
- Help distinguish true prediction errors from stimulus-specific adaptation

## Data Collection

The protocol will log stimulus parameters and timing information to CSV files:
- Details of sequence events and deviant trials
- Parameters of each sequence presentation

Behavioral data (animal running) will be collected via an encoder on the behavior device.

## Synchronization
- TTL pulses will be generated at the start of each sequence for synchronization with recording equipment
- Additional markers will indicate the timing of deviant and omission events

## Running the Experiment
1. Start the Bonsai workflow
2. Begin the habituation phase
3. The experiment will automatically transition to the testing phase after the habituation period
4. The experiment can be terminated upon completion

## Related Documents

- **[Standard Oddball](standard-oddball.md)**: Information about the standard oddball paradigm
- **[Bonsai Instructions](bonsai_instructions.md)**: Setup and deployment of Bonsai code
- **[Experimental Plan](../experimental-plan.md)**: Overview of all experimental paradigms
- **[SLAP2 Hardware](../hardware/allen_institute_slap2_hardware.md)**: Details about the SLAP2 imaging system used

<!-- DISCUSSION_LINK_START -->
<div class="discussion-link">
    <hr>
    <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions/new?category=q-a&title=Discussion%3A%20stimuli/sequence-mismatch" target="_blank">
            💬 Start a discussion for this page on GitHub
        </a>
        <span class="note">(A GitHub account is required to create or participate in discussions)</span>
    </p>
</div>
<!-- DISCUSSION_LINK_END -->
