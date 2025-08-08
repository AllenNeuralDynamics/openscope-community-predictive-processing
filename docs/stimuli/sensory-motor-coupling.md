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
Phase Offset = Math.Atan(2 * Math.PI / 360 * WheelRadiusOverScreenRatio * WheelAngle) * 180 / (SpatialFrequency * Math.PI)
```

Where:

- **WheelAngle** (Item1): The encoder reading in degrees representing the wheel's rotational position
- **WheelRadiusOverScreenRatio** (Item2): The ratio of 5.5/15 = 0.367, accounting for the geometric relationship between wheel radius and screen distance
- **SpatialFrequency** (Item3): The spatial frequency of the gratings in cycles per degree (typically 0.04 cpd)

## Geometric Analysis

### The Coupling Formula Explained

The formula implements a perspective projection that accounts for the geometric relationship between the wheel movement and the visual field:

1. **Angular Conversion**: `2 * Math.PI / 360 * WheelAngle` converts the wheel angle from degrees to radians

2. **Geometric Scaling**: The ratio `5.5/15` (0.367) represents the relationship between:

   - The distance from the mouse to the wheel center (5.5 cm)
   - The distance from the mouse to the screen (15 cm)
   
   This ratio ensures that when the mouse moves forward by a certain distance, the visual pattern moves by a proportional amount in the visual field.

3. **Perspective Projection**: `Math.Atan()` function calculates the angular displacement in the mouse's visual field that corresponds to the wheel movement. This arctangent transformation accounts for the fact that equal distances at different depths create different angular changes in the visual field.

4. **Spatial Frequency Compensation**: Division by spatial frequency (`SpatialFrequency * Math.PI`) ensures that the phase offset is appropriate for the specific grating being displayed. Higher spatial frequencies require smaller phase changes to achieve the same visual displacement.

5. **Degree Conversion**: `* 180 / Math.PI` converts the result back to degrees for use in the rendering system.

### Physical Interpretation

The goal is to create a realistic spatial coupling where:

- Forward wheel movement → Forward visual motion
- Backward wheel movement → Backward visual motion
- The amount of visual motion matches the mouse's perceived movement through space

The formula ensures that when the mouse runs forward by a distance `d`, the visual pattern shifts by an angle that corresponds to what the mouse would see if actually moving through a stationary visual environment.

## Implementation in Bonsai

### Data Flow

1. **Encoder Input**: The AMT10 encoder continuously reports wheel position in degrees
2. **Parameter Combination**: The wheel angle is combined with the coupling ratio (0.367) and spatial frequency (0.04 cpd)
3. **Phase Calculation**: The coupling formula calculates the appropriate phase offset
4. **Modulo Operation**: The result is wrapped to 360° to maintain continuous phase cycling
5. **Visual Rendering**: The calculated phase offset is applied to the vertical gratings

## Configuration Parameters

The coupling system uses several configurable parameters:

- **WheelRadiusOverScreenRatio**: 0.367 (ratio of 5.5cm/15cm)
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
