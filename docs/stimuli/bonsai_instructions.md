This repository stores Bonsai code to run visual stimuli that are part of this community effort: [Neural mechanisms of predictive processing](https://arxiv.org/abs/2504.09614).

## Organization

All Bonsai workflows should go into the [`code/stimulus-control/src`](https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing/tree/main/code/stimulus-control/src) folder, along with the `Extensions` folder.

## Deployment

### Initial Setup (Important!)

1. To deploy the Bonsai code, run [`code/stimulus-control/bonsai/setup.cmd`](https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing/blob/main/code/stimulus-control/bonsai/setup.cmd).  
   This small script will download and regenerate the current Bonsai environment ([see tutorial for further details](https://bonsai-rx.org/docs/articles/environments.html)).

2. **CRITICAL: Only use the Bonsai.exe that is downloaded by the setup script.** This ensures that you're using the correct version with all required packages.
   - The script will create a local Bonsai installation in the `code/stimulus-control/bonsai` folder
   - Launch Bonsai by double-clicking the `Bonsai.exe` within this folder, not from any other installation on your system

3. The setup script will automatically install all required packages specified in the `Bonsai.config` file. Do not manually install additional packages unless absolutely necessary.

### Avoiding Common Issues

- **Version conflicts**: Using multiple versions of Bonsai on the same system can lead to package conflicts. Always use the version downloaded by the setup script.

### Troubleshooting

If you encounter issues:
1. Close all instances of Bonsai
2. Delete the file in `code/stimulus-control/bonsai` that are not present on the GitHub repository.
3. Run the setup.cmd script again to get a fresh installation
4. Open your workflow using the newly downloaded Bonsai.exe

### Updating Dependencies

Each time you change a project dependency via the `Package Manager`, the `Bonsai.Config` file will be updated, and you can choose to commit these changes. However, take care when adding new packages as this might create dependencies that others will need to install.

---

## Prerequisites

These should only need to be installed once on a fresh new system and are not required if simply refreshing the install or deploying to a new folder.

- **Operating System**: Windows 10 or 11
- **Tools**:
    - [Visual Studio Code](https://code.visualstudio.com/) (highly recommended for editing code scripts and Git commits)
    - [Git for Windows](https://gitforwindows.org/) (highly recommended for cloning and manipulating this repository)
    - [.NET Framework 4.7.2 Developer Pack](https://dotnet.microsoft.com/download/dotnet-framework/thank-you/net472-developer-pack-offline-installer) (required for IntelliSense when editing code scripts)
    - [Visual C++ Redistributable for Visual Studio 2012](https://www.microsoft.com/en-us/download/details.aspx?id=30679) (native dependency for OpenCV)

### Hardware Specific:
These are needed to run Bonsai workflows on the Allen Institute rigs with HARP devices:
- [FTDI CDM Driver 2.12.28](https://www.ftdichip.com/Drivers/CDM/CDM21228_Setup.zip) (serial port drivers for HARP devices)
- [Spinnaker SDK 1.29.0.5](https://www.flir.co.uk/support/products/spinnaker-sdk/#Downloads) (device drivers for FLIR cameras)
    - On the FLIR website: `Download > Archive > 1.29.0.5 > SpinnakerSDK_FULL_1.29.0.5_x64.exe`
- [NI-DAQmx 19.0](https://www.ni.com/en-gb/support/downloads/drivers/download.ni-daq-mx.html#301173) (drivers for NI-DAQ devices)

---

## Related Documents

- **[Experimental Plan](../experimental-plan.md)**: Overview of experimental paradigms using these stimuli
- **[Standard Oddball Stimulus](standard-oddball.md)**: Details of the standard oddball paradigm implementation
- **[Sensory-Motor Closed-Loop](sensory-motor-closed-loop.md)**: Information about sensorimotor paradigm implementation
- **[List of Bonsai Scripts](list_scripts.md)**: Catalog of all available stimulus scripts

<!-- DISCUSSION_LINK_START -->
<div class="discussion-link">
    <hr>
    <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions/new?category=q-a&title=Discussion%3A%20stimuli/bonsai_instructions" target="_blank">
            💬 Start a discussion for this page on GitHub
        </a>
        <span class="note">(A GitHub account is required to create or participate in discussions)</span>
    </p>
</div>
<!-- DISCUSSION_LINK_END -->
