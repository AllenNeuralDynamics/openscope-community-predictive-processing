# 🧠 Predictive Processing Project Tracking

This document tracks the progress and key aspects of our Predictive Processing project, which involves the collection and analysis of new data related to the neural mechanisms of predictive processing.

---

## Project Management Workflow

We use a [GitHub Kanban board](https://github.com/orgs/AllenNeuralDynamics/projects/149/views/4) to track individual tickets and provide visibility into the progress of the project. The board organizes tickets added to the repository and follows a standard workflow.

<div class="github-project-link" style="text-align: center; margin: 20px 0; padding: 15px; background-color: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 6px;">
    <h3>🔄 Live Project Board</h3>
    <p>View our current tasks and progress on the live GitHub project board:</p>
    <a href="https://github.com/orgs/AllenNeuralDynamics/projects/149/views/4" target="_blank" style="display: inline-block; padding: 10px 20px; background-color: #2ea44f; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 10px 0;">Open GitHub Project Board</a>
    <p style="font-size: 0.9em; color: #586069; margin-top: 10px;">Note: You need to be logged into GitHub and have appropriate permissions to view the board.</p>
</div>

### Workflow Overview:
1. **Create a GitHub Issue**:
    - Each task or deliverable should be created as a GitHub issue in the repository.
    - Clearly define the task, its scope, and any relevant details.
    - Provide estimated start and end dates, to be updated as the project progresses.
    - Assign the issue to the appropriate team member(s) and indicate the Laboratory that will be performing the task.
    - Use labels to categorize issues (e.g., `data-analysis`, `stimulus-design`, `documentation`).

2. **Track on the Kanban Board**:
    - All issues are automatically added to the [Kanban board](https://github.com/orgs/AllenNeuralDynamics/projects/149/views/7).
    - The board is organized into columns representing different stages of the workflow:
        - **To Do**: Tasks that are planned but not yet started.
        - **In Progress**: Tasks currently being worked on.
        - **Review**: Tasks that are completed and awaiting review.
        - **Done**: Tasks that are completed and approved.

3. **Update Regularly**:
    - Team members should update the status of their issues on the Kanban board as they progress through the workflow.
    - Add comments to issues to provide updates or request feedback.

---

## Data Collection and Management Projects

### Project 1: Data Collection and Stimulus Design

**🎯 Title & Goal:**  
*Design and implement stimuli for investigating predictive processing mechanisms across multiple experimental paradigms.*

**👥 Contributors:**  
@jeromelecoq @rcpeene @Sarruedi

**📝 Description:**  
This project focuses on developing and implementing four key experimental paradigms to investigate different aspects of predictive processing:
 
1. **Standard Mismatch**: Habituating animals to drifting gratings of the same orientation with occasional mismatch stimuli
2. **Sensorimotor Mismatch**: Establishing closed-loop visuo-motor interactions with occasional mismatches
3. **Sequence Mismatch**: Testing responses to disruptions in learned sequences of stimuli
4. **Temporal Mismatch**: Investigating responses to unexpected timing changes in sensory inputs

Each stimulus paradigm is implemented in Bonsai and includes appropriate control conditions to isolate specific predictive mechanisms.

**Progress:**
- ✅ Standard oddball and sensorimotor oddball stimuli implemented in Bonsai
- ✅ Initial SLAP2 recordings completed with mouse #794237 and #787727
- 🔄 Ongoing refinement of temporal mismatch stimuli
- Temporal sequence not started

### Project 2: Data Curation and Sharing

**🎯 Title & Goal:**  
*Ensure all data and metadata are properly curated, formatted, and shared through public repositories.*

**👥 Contributors:**  
@jeromelecoq @rcpeene

**📝 Description:**  
This project focuses on the critical task of data management, ensuring that all datasets are released without embargo, following the community policy.  
This includes standardizing data in NWB format, uploading datasets to the Allen Institute or DANDI/NWB archives, and providing comprehensive documentation.

Key data types include:
- Two-photon calcium imaging data from pan-excitatory and pan-inhibitory lines
- Neuropixels recordings with SST-optotagging
- Recordings of pyramidal cell somata and dendrites using SLAP2

**Progress:**
- 🔄 Initial data curation pipeline established
- 🔄 Working on metadata standardization for SLAP2 experiments
- 🔄 One experiment shared on DANDI

---

## Analysis Projects (Aligned with Analysis Plan)

### Project 3: Information Encoding in Mismatch Responses

**🎯 Title & Goal:**  
*Determine what kind of information is encoded by mismatch responses across different experimental paradigms.*

**👥 Contributors:**  
*Seeking contributors*

**📝 Description:**  
This project addresses the first main question in our analysis plan: "What kind of information is encoded by mismatch responses?" We will analyze how neurons represent prediction errors by distinguishing between:

1. **Multiplicative Novelty**:
    - Analyze whether mismatch responses scale with tuning curve preference
    - Fit tuning curves with multiplicative gain parameters
    - Test if neurons with strong preference for standard stimuli show larger mismatch responses

2. **Additive Novelty**:
    - Test if mismatch responses reflect a generalized "alert" signal
    - Evaluate whether responses increase uniformly across all stimulus conditions
    - Fit tuning curves with additive offset parameters

3. **Subtractive Novelty (True Prediction Error)**:
    - Quantify if responses represent the difference between expected and actual stimuli
    - Build predictive models of expected neural activity and compare with actual activity
    - Test if response magnitude correlates with feature distance between expected and actual stimuli

**Analysis Methods:**
- Event-triggered averaging for calcium imaging data
- Peri-stimulus time histograms for Neuropixels data
- Tuning curve analysis with parametric models
- Bootstrap resampling for statistical validation

### Project 4: Categories of Neural Predictions

**🎯 Title & Goal:**  
*Distinguish between detailed stimulus predictions and statistical ensemble deviations in neural responses.*

**👥 Contributors:**  
*Seeking contributors*

**📝 Description:**  
This project addresses the second main question in our analysis plan: "What categories of predictions are made by neurons?" We will investigate whether neural activity reflects:

1. **Detailed Stimulus Predictions**:
    - Compare responses in closed-loop vs. open-loop conditions
    - Analyze whether neurons encode precise expectations about upcoming stimuli
    - Test if predictive signals differ across visual features (orientation, motion)

2. **Ensemble Probability Deviations**:
    - Apply population decoding and mutual information analyses
    - Calculate how well neural activity encodes individual mismatch stimuli vs. general novelty
    - Compare information content across experimental conditions

3. **Predictive Learning Dynamics**:
    - Track response changes to repeated oddball stimuli over time
    - Apply decay models to quantify adaptation rates
    - Use tensor component analysis to identify population-level learning patterns

4. **Pattern Completion Mechanisms**:
    - Analyze neural activity during stimulus omission periods
    - Test if omission responses depend on preceding stimulus patterns
    - Evaluate evidence for predictive filling-in of expected stimuli

**Analysis Methods:**
- Cross-condition comparisons (closed-loop vs. open-loop)
- Information-theoretic measures (mutual information, entropy)
- Machine learning decoders (SVMs, neural networks)
- Time series analysis of learning dynamics

### Project 5: Cross-Paradigm Comparison of Mismatch Responses

**🎯 Title & Goal:**  
*Compare neural responses across different prediction paradigms to determine if they engage shared or distinct mechanisms.*

**👥 Contributors:**  
*Seeking contributors*

**📝 Description:**  
This project addresses the third main question in our analysis plan: "How do mismatch responses differ across prediction types?" We will perform comprehensive comparisons across our experimental paradigms to determine:

1. **Shared vs. Distinct Neural Ensembles**:
    - Track the same neurons across multiple paradigms
    - Apply dimensionality reduction to identify shared response subspaces
    - Test if the same neurons encode different types of prediction errors

2. **Mismatch Type Specificity**:
    - Compare responses to different mismatch types (orientation, motion, temporal, omission)
    - Analyze population response patterns across mismatch types
    - Test if responses are feature-specific or generalize across mismatch types

3. **Passive vs. Active Prediction Differences**:
    - Directly compare oddball vs. sensorimotor mismatch responses
    - Analyze differences in response magnitude, timing, and cell-type specificity
    - Evaluate if motor-based predictions use different mechanisms than passive predictions

4. **Temporal Dynamics Analysis**:
    - Compare response onset, duration, and oscillatory patterns across paradigms
    - Perform time-frequency analysis of response dynamics
    - Test if different prediction types share temporal signatures

**Analysis Methods:**
- Multi-session registration of neural populations
- Dimensionality reduction techniques (PCA, t-SNE, UMAP)
- Response similarity metrics across paradigms
- Time-frequency analysis of neural dynamics

### Project 6: Computational Modeling of Predictive Processing

**🎯 Title & Goal:**  
*Develop and validate computational models that integrate multiple predictive mechanisms.*

**👥 Contributors:**  
*Seeking contributors*

**📝 Description:**  
This project focuses on creating and testing computational models that simulate and explain the neural processes underlying predictive processing:

1. **Predictive Coding Models**:
    - Implement hierarchical prediction networks with explicit error computation
    - Model distinct error channels for different types of prediction violations
    - Compare model predictions with neural response patterns

2. **Reinforcement Learning Models**:
    - Implement models with prediction error as a teaching signal
    - Focus on learning dynamics during repeated exposure to prediction violations
    - Test whether learning rates differ across prediction types

3. **Dynamical Systems Models**:
    - Create recurrent network models capable of generating predictions
    - Model connectivity structures between excitatory and inhibitory neurons
    - Determine minimal circuit requirements for different types of prediction errors

**Analysis Methods:**
- Parameter fitting and cross-validation
- Model comparison using information-theoretic criteria (AIC, BIC)
- Simulations of neural network dynamics
- Testing model predictions against experimental data

---

## Related Documents

- **[Experimental Plan](experimental-plan.md)**: Overview of experimental paradigms and approaches
- **[Analysis Plan](analysis-plan.md)**: Detailed methods for analyzing the collected data 
- **[Experiment Summary](experiment-summary.md)**: Overview of all conducted and planned experiments
- **[Hardware Overview](hardware-overview.md)**: Information about the recording platforms used

<!-- DISCUSSION_LINK_START -->
<div class="discussion-link">
    <hr>
    <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions/new?category=q-a&title=Discussion%3A%20project-tracking" target="_blank">
            💬 Start a discussion for this page on GitHub
        </a>
        <span class="note">(A GitHub account is required to create or participate in discussions)</span>
    </p>
</div>
<!-- DISCUSSION_LINK_END -->
