# C# Wheel Encoder Plugin

## Overview

This document describes the C# wheel encoder plugin, specifically the [**aind-behavior-amt10-encoder**](https://github.com/AllenNeuralDynamics/aind-behavior-amt10-encoder) library, used for acquiring rotary encoder data from the running wheel on **Neuropixel and Mesoscope experimental rigs** at the Allen Institute. This plugin provides Bonsai nodes for reading and interacting with AMT10 quadrature encoders.

**Note:** This plugin is *not* used for SLAP2 rigs, which utilize HARP for wheel encoder communication.

**Important Disclaimer:** This documentation is provided for transparency and to fully describe the experimental setup. The `aind-behavior-amt10-encoder` and the associated hardware configuration are highly specific to the Allen Institute's experimental rigs and are **not intended for general use outside of this specific context.**

## Purpose

The primary purpose of this plugin within the Allen Institute's setup is to:

- Provide real-time access to wheel position and speed from AMT10 encoders.
- Offer a standardized interface within Bonsai workflows for these specific digital wheel encoders.
- Facilitate synchronization of behavioral data (running) with neural recordings and visual stimuli, which is critical for experiments such as sensory-motor oddballs.

## Hardware and Communication Architecture

The system relies on a specific hardware and software chain:

1.  **AMT10 Encoder:** A digital rotary encoder measures the wheel's rotation.
2.  **LS7366R Quadrature Counter Chip:** This chip interfaces directly with the encoder.
3.  **Arduino:** An Arduino board, running custom firmware (`LS7366R_quadrature_counter.ino`), reads data from the LS7366R chip.
4.  **Serial Communication:** The Arduino sends the encoder data over a serial (USB) connection.
5.  **C# (Bonsai Nodes):** The `aind-behavior-amt10-encoder` library provides Bonsai nodes (e.g., `AMT10EncoderSource`) that communicate with the Arduino via this serial connection, parsing the data to make it available within Bonsai workflows.

This architecture allows C# applications, primarily Bonsai workflows, to access and utilize the wheel encoder data.

## Source Code

- **Repository Link:** [https://github.com/AllenNeuralDynamics/aind-behavior-amt10-encoder](https://github.com/AllenNeuralDynamics/aind-behavior-amt10-encoder)
- **Key Files/Modules:**
  
    - `src/Aind.Behavior.Amt10Encoder/`: Contains the C# source code for the Bonsai nodes.
    - `reference/LS7366R_quadrature_counter.ino`: The Arduino firmware.
    - `reference/AMT10_quadrature_encoder.py`: Python reference implementation of the communication protocol.

## Related Hardware

- [Neuropixels Hardware](allen_institute_neuropixels_hardware.md)
- [Mesoscope Hardware](allen_institute_mesoscope_hardware.md)

<!-- DISCUSSION_LINK_START -->
<div class="discussion-link">
    <hr>
    <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions/new?category=q-a&title=Discussion%3A%20hardware/wheel_encoder_plugin" target="_blank">
            💬 Start a discussion for this page on GitHub
        </a>
        <span class="note">(A GitHub account is required to create or participate in discussions)</span>
    </p>
</div>
<!-- DISCUSSION_LINK_END -->
