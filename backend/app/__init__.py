"""Backend spectra. Adapter sumber data diimpor dari data-pipeline/scripts/sources/ (tidak disalin)."""

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[2] / "data-pipeline" / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
