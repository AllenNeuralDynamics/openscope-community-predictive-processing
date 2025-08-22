# Experiment Session Notes

- **Mouse ID:** TBD
- **Date:** 2025-08-22
- **Experimenter:** @amshelton @jeromelecoq 
- **Rig / Setup ID:** SLAP2
- **Stimulus version:** [https://raw.githubusercontent.com/AllenNeuralDynamics/openscope-community-predictive-processing/eb4f723e4dbb7725d0e0f65a45f615072f8b69d8/code/stimulus-control/src/Standard_oddball_slap2_version2.bonsai](https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing/blob/8305c5f016eecdc8850950c042d0fbba916755f5/code/stimulus-control/src/Standard_oddball_slap2_version2.bonsai)
NOTE AGAIN (Forgot to commit): We fixed a bug in the oddball block to make sure standard orientation alternated. Not On github yet.
The code fix bug with camera file closure and fake initial pulses sent to SlAP. 
- - **Protocol followed:** Glutamate (Green fluorophore) imaging, 65 min experiment
- **Notes & Issues:**
    - Same experiment as last time. We record behavior videos (body, eye, face) with HARP timestamps aligned with the other events. 
    - SLAP2 was ran with SLAP trials to avoid analysis pipeline issues (30 seconds each, longer than before). 
    - Screen is Gamma calibrated.
    - This design : https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing/discussions/98
    - Orientation 1  : 60 trials
    - Oddball block 1 : Standard 0deg (1443 trials), 45 and 90 oddballs, omission (30 trials) shuffled, Oddball occurs on average every  11s
    - Orientation 2  : 33 trials
    - Oddball block 2 : Standard 0deg (1443 trials), 0 and 45 oddballs, omission (30 trials) shuffled, Oddball occurs on average every  11s
    - Orientation 3  : 33 trials
    - Nb Receptive fields : 10

    Total Expected duration = 65 min
  
    - XXXX mouse is labelled with GluSNF4 with viruses injection, injected in V1. We will image GluSNF4 with two photon. Expression is controled by Cre. PXXX today. 
    - injected with Exp32222-hSyn-Flex-iGluSnFR4.v9601.NGR virus injected on XX/XX/2025. 
    - DMDXXX is superficial XXX - 50um. DMDXXX is deeper - 215 um
    - Head fixation started at about XX:XX
    - Experiment started at XX:XX
    - We ended exactly on time at XX:XX
