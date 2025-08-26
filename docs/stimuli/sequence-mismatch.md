# Sequence Mismatch Protocol

## Overview

The Sequence Mismatch Protocol investigates how the brain detects violations in learned sequences of stimuli. This paradigm examines whether the brain forms predictions about stimulus patterns and sequences, not just individual stimuli. The protocol presents animals with repeated sequences of stimuli to establish expectations, then occasionally introduces deviants that violate the learned sequence structure.

## Stimulus Structure

![Sequence Mismatch Analysis](../img/stimuli/sequence_mismatch_structure_analysis.png)

The figure above shows a detailed analysis of the sequence mismatch protocol structure:

1. **Block Structure Timeline**: Illustrates the temporal organization of different blocks including:
   - **Sequential Oddball Blocks**: Main experimental blocks where sequences are established and violations introduced
   - **Sequential Control Blocks**: Control periods with shuffled or randomized sequences
   - **RF Mapping Blocks**: Spatial tuning phases

2. **Grating Orientations Over Time**: Shows the sequence of orientations used in the protocol, demonstrating the structured patterns and their violations

3. **Oddball Events Distribution**: Displays when sequence violations occur, including:
   - **Orientation Oddballs**: Unexpected orientations at specific sequence positions
   - **Omission Events**: Missing stimuli in learned sequences

The analysis reveals how the protocol establishes predictable sequences and then systematically violates expectations to probe predictive processing mechanisms.

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
