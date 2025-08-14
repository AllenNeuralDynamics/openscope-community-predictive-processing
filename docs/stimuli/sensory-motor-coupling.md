# Sensory-Motor Coupling

## Overview

The sensory-motor coupling mechanism creates a real-time connection between the mouse's running behavior and the visual stimulus presented on the screen. This coupling allows the investigation of how neural responses are modulated by self-generated visual feedback and provides a foundation for studying predictive processing in the context of sensorimotor integration.

## Coupling Mechanism

The coupling system transforms the mouse's wheel movement into corresponding changes in the visual gratings' spatial phase, creating the illusion that the mouse is navigating through a visual environment. This creates a direct sensorimotor loop where the animal's movement controls the visual feedback.

### Hardware Setup

The sensory-motor coupling relies on a specific geometric arrangement:

- **Screen Distance**: 15 cm from the mouse's eye
- **Mouse Position**: 5.5 cm from the center of the running wheel
- **Encoder**: AMT10 encoder with 8192 counts per revolution tracking wheel rotation
- **Stimulus**: Vertical drifting gratings displayed on the screen

### Mathematical Foundation

The conversion from wheel rotation to grating phase offset is accomplished through the following geometric transformation:

```
Phase Offset = 2 * Math.PI * WheelRadiusOverScreenRatio * WheelAngle / (Math.tan((1/SpatialFrequency) * Math.PI / 180))
```

Where:

- **WheelAngle** (Item1): The encoder reading in degrees representing the wheel's rotational position
- **WheelRadiusOverScreenRatio** (Item2): The ratio of 5.5/15 = 0.36, accounting for the geometric relationship between wheel radius and screen distance
- **SpatialFrequency** (Item3): The spatial frequency of the gratings in cycles per degree (typically 0.04 cpd)

## Geometric Analysis

### The Coupling Formula Explained

The formula implements a geometric transformation that accounts for the relationship between wheel movement and visual field displacement:

1. **Linear Distance Calculation**: `2 * Math.PI * WheelRadiusOverScreenRatio * WheelAngle` calculates the linear distance the mouse has "moved" based on wheel rotation:
   - `WheelAngle` is converted from degrees to a proportion of full rotation
   - Multiplied by `2 * Math.PI` to get radians of wheel rotation
   - Scaled by `WheelRadiusOverScreenRatio` to account for the geometric relationship between wheel and screen

2. **Spatial Frequency Conversion**: `Math.tan((1/SpatialFrequency) * Math.PI / 180)` converts the spatial frequency to the appropriate scaling factor:
   - `1/SpatialFrequency` gives the spatial period (degrees per cycle)
   - Converted to radians and tangent calculated to account for visual field geometry

3. **Phase Calculation**: The division gives the final phase offset that corresponds to the appropriate visual displacement for the given spatial frequency.

### Physical Interpretation

The goal is to create a realistic spatial coupling where:

- Forward wheel movement → Forward visual motion
- Backward wheel movement → Backward visual motion
- The amount of visual motion matches the mouse's perceived movement through space

The formula ensures that when the mouse runs forward by rotating the wheel, the visual pattern shifts by a distance that accurately represents the mouse's movement through a stationary visual environment. The spatial frequency scaling ensures that the visual displacement is appropriate for the specific grating pattern being displayed.

## Implementation in Bonsai

### Data Flow

1. **Encoder Input**: The AMT10 encoder continuously reports wheel position in degrees
2. **Parameter Combination**: The wheel angle is combined with the coupling ratio (0.36) and spatial frequency (0.04 cpd)
3. **Phase Calculation**: The coupling formula calculates the appropriate phase offset
4. **Modulo Operation**: The result is wrapped to 360° to maintain continuous phase cycling
5. **Visual Rendering**: The calculated phase offset is applied to the vertical gratings

## Configuration Parameters

The coupling system uses several configurable parameters:

- **WheelRadiusOverScreenRatio**: 0.36 (ratio of 5.5cm/15cm)
- **MotorCouplingCPD**: 0.04 cycles per degree (spatial frequency of the gratings)
- **CountsPerRevolution**: 8192 (encoder resolution)

These parameters can be adjusted to modify the coupling strength or adapt to different experimental setups.

## Script Location

The sensory-motor coupling implementation is found in:

- [`/code/stimulus-control/src/Mindscope/generic_oddball.bonsai`](https://github.com/allenneuraldynamics/openscope-community-predictive-processing/blob/main/code/stimulus-control/src/Mindscope/generic_oddball.bonsai)


## Technical Considerations

- **Latency**: The system operates at the display refresh rate (typically 60 Hz) ensuring minimal latency between movement and visual feedback
- **Resolution**: The 8192 counts per revolution encoder provides high-resolution tracking of wheel movement
- **Continuous Operation**: The phase calculation updates continuously, providing smooth visual motion that tracks wheel movement in real-time

## Related Documents

- **[Sensory-Motor Closed-Loop](sensory-motor-closed-loop.md)**: Implementation of oddball violations in motor-coupled environments
- **[Generic Oddball Protocol](generic-oddball.md)**: Flexible framework using this coupling mechanism
- **[Bonsai Instructions](bonsai_instructions.md)**: Setup and deployment instructions

<!-- DISCUSSION_LINK_START -->
<div class="discussion-link">
    <hr>
    <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions/new?category=q-a&title=Discussion%3A%20stimuli/sensory-motor-coupling" target="_blank">
            💬 Start a discussion for this page on GitHub
        </a>
        <span class="note">(A GitHub account is required to create or participate in discussions)</span>
    </p>
</div>
<!-- DISCUSSION_LINK_END -->
