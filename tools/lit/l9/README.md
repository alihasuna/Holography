# L9 detector numbers (report docs/agent_reports/L9_microscope_detector.md)

Scripts written by agent L9 and copied here by the orchestrator so that the numbers in the report are
reproducible from committed code. `digitise_paton_fig8.py` reads Fig. 8 of Paton et al. 2021
(Ultramicroscopy 227, 113298; CC BY) from the Glasgow accepted-manuscript PDF
(eprints.gla.ac.uk/240505/1/240505.pdf; SHA-256 recorded in the script docstring), which is not
committed: download it to `pdf/Paton2021_gla_AAM.pdf` next to the scripts before rerunning.
`fit_mtf.py` fits the digitised MTF; `l9_numbers.py` derives the fringe-contrast and phase-noise
factors. The `.out` files are the outputs of the runs quoted in the report.
