"""reflection_holo.pipeline: the end-to-end simulation pipeline (docs/05 sections 0, 4.5, 5).

    venv/bin/python -m reflection_holo.pipeline run --config C --out D [--variant V]
    venv/bin/python -m reflection_holo.pipeline dry-run --config C [--variant V]
    venv/bin/python -m reflection_holo.pipeline list-inputs --config C [--variant V]

Configuration schema and gate: ``pipeline.config``; engines: ``pipeline.engines``; the chain:
``pipeline.run``; quantification: ``pipeline.quantify``; resource estimates: ``pipeline.estimates``.
No default ever replaces a missing PROJECT_INPUT: such runs fail naming the docs/06 item.
"""
from reflection_holo.pipeline.config import (  # noqa: F401
    PipelineConfig, PipelineConfigError, list_inputs, load_pipeline_dict, load_pipeline_file,
    read_pipeline_file)
from reflection_holo.pipeline.run import OutputDirectoryError, run  # noqa: F401
