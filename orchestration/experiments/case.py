"""The registered public case; caller owns ledger/lease admission."""

from pathlib import Path
from typing import Literal

from orchestration.experiments.executor import digest
from orchestration.experiments.models import ExperimentEnvironment, ExperimentInput, ExperimentPlan
from orchestration.experiments.scientific import NIST_DATA_SHA256


PYTHON_IMAGE = "python:3.12.13-slim@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36"


def public_case(directory: Path | str, *, role: Literal["author", "replication", "inheritance"] = "author",
                order: Literal["original", "reverse"] = "original") -> ExperimentPlan:
    root = Path(directory).resolve()
    code = root / "experiment.py"
    data = root / "NumAcc4.dat"
    return ExperimentPlan(plan_id="nist-numacc4-" + order + "-v1", role=role,
        claim="CPython 3.12 statistics.variance reproduces NIST NumAcc4 sample variance within 1e-9 absolute error.",
        code=ExperimentInput(local_path=str(code), name="experiment.py", sha256=digest(code.read_bytes()),
                             source="Morphogenesis public CPU experiment v1; CPython statistics (PSF-2.0)"),
        data=ExperimentInput(local_path=str(data), name="NumAcc4.dat", sha256=NIST_DATA_SHA256,
            source="https://www.itl.nist.gov/div898/strd/univ/data/NumAcc4.dat"),
        environment=ExperimentEnvironment(image=PYTHON_IMAGE), parameters=(order,))
