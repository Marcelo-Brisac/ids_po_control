"""Mule-branded models (vendor=mule).

Models exposed under /vendors/mule/* on MuleRouter. Currently:
- Muledance 2.0 / 2.0-fast: brand-wrapped ByteDance Doubao Seedance 2.0
  for text-to-video, image-to-video, reference-to-video.

Directory names contain dots/hyphens so we load each generation.py via
importlib (mirroring models/alibaba/__init__.py).
"""

import contextlib
import importlib.util
from pathlib import Path

_package_dir = Path(__file__).parent

_model_files = [
    # Muledance 2.0 (standard)
    "muledance-2-0-t2v/generation.py",
    "muledance-2-0-i2v/generation.py",
    "muledance-2-0-r2v/generation.py",
    # Muledance 2.0 Fast
    "muledance-2-0-fast-t2v/generation.py",
    "muledance-2-0-fast-i2v/generation.py",
    "muledance-2-0-fast-r2v/generation.py",
]


def _import_model_file(model_file: str) -> None:
    """Import a model file to register its endpoint."""
    file_path = _package_dir / model_file
    if not file_path.exists():
        return

    module_name = model_file.replace("/", "_").replace("-", "_").replace(".", "_")
    spec = importlib.util.spec_from_file_location(
        f"models.mule.{module_name}",
        file_path,
    )
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)


for _model_file in _model_files:
    with contextlib.suppress(Exception):
        _import_model_file(_model_file)
