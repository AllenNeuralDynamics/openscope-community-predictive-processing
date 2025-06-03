# Frequently Asked Questions (FAQ)

This page addresses common questions about the OpenScope Community Predictive Processing project, its data, and how to get involved.

## General Project Questions

### What is the OpenScope Community Predictive Processing project?
The OpenScope Community Predictive Processing project is a collaborative effort to investigate the neural mechanisms underlying predictive processing in the brain. Through carefully designed experiments using in-vivo two-photon imaging and electrophysiological recordings, the project aims to test whether mismatch stimuli engage shared or distinct mechanisms. 

For more details, see:

- [Project Overview](index.md#scientific-context)
- [Our arXiv paper](https://arxiv.org/abs/2504.09614)

### Who is involved in this project?
The project involves researchers from multiple institutions, including the Allen Institute and various collaborating laboratories (Bastos lab, Najafi lab, Ruediger lab, and Oweiss lab). We also welcome contributions from the broader research community.

For more information:

- [Project Team](people.md)
- [How to Contribute](how_to_contribute.md)

### What are the main research questions?
The project addresses several key questions:

* Do temporal, motor, and omission mismatch stimuli engage shared or distinct neural mechanisms?
* How do these mechanisms differ across species (mice vs. primates)?
* What computational primitives (stimulus adaptation, dendritic computation, E/I balance, hierarchical processing) are central to predictive processing?

Learn more:

- [Experimental Plan](experimental-plan.md)
- [Analysis Plan](analysis-plan.md)

## Data and Resources

### How can I access the experimental data?
Specific access instructions and links will be provided on this website as datasets become available.

Access data here:

- [Experiment Summary](experiment-summary.md)
- [OpenScope Data Portal](https://portal.brain-map.org/explore/circuits/visual-coding-neuropixels)

### What types of data are being collected?
The project collects several types of data:

* Two-photon calcium imaging data from pan-excitatory and pan-inhibitory lines
* Neuropixels recordings with SST-optotagging
* Voltage imaging recordings of pyramidal cell somata and dendrites
* Behavioral data (running speed, eye movements)

See our methods:

- [Hardware Overview](hardware-overview.md)
- [Detailed Methods](detailed-experimental-plan.md)

### In what format are the data stored?
Data are standardized in Neurodata Without Borders (NWB) format to ensure interoperability and ease of use across the research community.

### Are there code samples for working with the data?
Yes, we will provide example scripts in the [`code/data-access`](https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing/tree/main/code/data-access) directory of our GitHub repository. These scripts demonstrate how to load, preprocess, and visualize the data.

## Getting Involved

### How can I contribute to the project?
There are several ways to contribute:

* Analyze existing datasets and share your findings
* Develop or validate computational models using our data
* Contribute to the codebases for data analysis or visualization
* Conduct complementary experiments in your own lab

Get started here:

- [How to Contribute](how_to_contribute.md)
- [Ways to Get Involved](how_to_contribute.md#ways-to-get-involved)

### How do I report issues or suggest improvements?
Issues can be reported on our [GitHub Issues page](https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing/issues). For discussions and suggestions, please use our [GitHub Discussions](https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing/discussions).

### How do I cite this project in my publications?
Please cite our [arXiv paper](https://arxiv.org/abs/2504.09614) when using data or code from this project:

For details on authorship in future publications, please review our [Collaboration Policy](collaboration-policy.md).

## Technical Questions

### What stimulus paradigms are used in the experiments?
Four main experimental paradigms are used:

* **Standard Mismatch**: Drifting gratings with occasional orientation changes
* **Sensorimotor Mismatch**: Closed-loop visuo-motor interactions with occasional mismatches
* **Sequence Mismatch**: Learned sequences with occasional disruptions
* **Temporal Mismatch**: Stimuli with unexpected timing changes

Explore our approach:

- [Experimental Plan](experimental-plan.md)
- [Detailed Methods](detailed-experimental-plan.md)

### What hardware is used for the recordings?
The project uses three primary recording systems:

* SLAP2 (Scanned Line Angular Projection) for high-speed subcellular imaging
* Neuropixels probes for high-density electrophysiological recordings
* Mesoscope for wide-field calcium imaging

See the [Hardware Documentation](hardware-overview.md) for more details.

### How are the stimuli implemented?
All stimuli are implemented using the Bonsai framework. The stimulus code is available in the [`code/stimulus-control/src`](https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing/tree/main/code/stimulus-control/src) directory of our GitHub repository. See the [Bonsai Instructions](stimuli/bonsai_instructions.md) for more information.

<!-- DISCUSSION_LINK_START -->
<div class="discussion-link">
    <hr>
    <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions/new?category=q-a&title=Discussion%3A%20faq" target="_blank">
            💬 Start a discussion for this page on GitHub
        </a>
        <span class="note">(A GitHub account is required to create or participate in discussions)</span>
    </p>
</div>
<!-- DISCUSSION_LINK_END -->
