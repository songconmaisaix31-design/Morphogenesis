"""Two fixed, trusted cases; caller owns ledger/lease admission."""

from collections.abc import Callable
from dataclasses import dataclass
import hashlib
from importlib.metadata import distribution
from pathlib import Path
from typing import Literal

from orchestration.experiments import linear_regression, nist
from orchestration.experiments.models import (
    CaseId, ExperimentCriteria, ExperimentEnvironment, ExperimentInput, ExperimentPlan,
    LinearRegressionCriteria, ScientificAssessment,
)

PYTHON_IMAGE = "python:3.12.13-slim@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36"
Role = Literal["author", "replication", "inheritance"]
Order = Literal["original", "reverse"]


def _assets(relative: str) -> Path:
    source = Path(__file__).resolve().parents[2] / relative
    if source.is_dir():
        return source
    return Path(str(distribution("morphogenesis").locate_file(relative)))


@dataclass(frozen=True)
class CaseDefinition:
    case_id: CaseId
    title: str
    problem: str
    claim: str
    template_summary: str
    file_policy_prefix: str
    code_source: str
    code_license: str
    data_source: str
    data_license: str
    _relative_directory: str
    _code_name: str
    _data_name: str
    _data_sha256: str
    _judge: Callable[[ExperimentPlan, bytes, bytes], ScientificAssessment]

    def build_plan(self, role: Role = "author", order: Order = "original",
                   directory: Path | str | None = None) -> ExperimentPlan:
        if self.case_id == "synthetic-linear-regression-v1" and order != "original":
            raise ValueError("unsupported_case_order")
        root = Path(directory).resolve() if directory is not None else _assets(self._relative_directory)
        code = root / self._code_name
        criteria = ExperimentCriteria() if self.case_id == "nist-numacc4-v1" else LinearRegressionCriteria()
        prefix = "nist-numacc4" if self.case_id == "nist-numacc4-v1" else "synthetic-linear-regression"
        return ExperimentPlan(plan_id=prefix + "-" + order + "-v1", role=role, claim=self.claim,
            code=ExperimentInput(local_path=str(code), name=self._code_name,
                sha256=hashlib.sha256(code.read_bytes()).hexdigest(), source=self.code_source),
            data=ExperimentInput(local_path=str(root / self._data_name), name=self._data_name,
                sha256=self._data_sha256, source=self.data_source),
            environment=ExperimentEnvironment(image=PYTHON_IMAGE), criteria=criteria, parameters=(order,))

    def validate_inputs(self, plan: ExperimentPlan, code: bytes, data: bytes) -> None:
        # Selection is from the trusted fixed registry, never a plan-supplied import/shell.
        if plan.criteria.version != self.case_id:
            raise ValueError("case_criteria_mismatch")
        if self.case_id == "synthetic-linear-regression-v1" and plan.parameters != ("original",):
            raise ValueError("unsupported_case_order")
        code_name = "experiment.ipynb" if plan.mode == "notebook" else self._code_name
        canonical = _assets(self._relative_directory) / code_name
        if (plan.data.name != self._data_name or hashlib.sha256(data).hexdigest() != self._data_sha256
                or plan.data.sha256 != self._data_sha256):
            raise ValueError("unregistered_case_input")
        if plan.code.name != code_name or not canonical.is_file():
            raise ValueError("unregistered_case_code")
        # Git checkout and packaged archives may use LF or CRLF. These are
        # two explicit registered byte representations; archived digests are
        # still verified against the original plan without normalization.
        lf = canonical.read_bytes().replace(b"\r\n", b"\n")
        if code not in (lf, lf.replace(b"\n", b"\r\n")):
            raise ValueError("unregistered_case_code")

    def assess(self, plan: ExperimentPlan, raw_input: bytes, raw_output: bytes) -> ScientificAssessment:
        plan = ExperimentPlan.model_validate(plan.model_dump(mode="json"))
        if plan.criteria.version != self.case_id:
            raise ValueError("case_criteria_mismatch")
        return self._judge(plan, raw_input, raw_output)


_NIST = CaseDefinition(
    case_id="nist-numacc4-v1", title="NIST NumAcc4 sample variance",
    problem="Reproduce NIST NumAcc4 sample variance using CPython statistics.variance.",
    claim="CPython 3.12 statistics.variance reproduces NIST NumAcc4 sample variance within 1e-9 absolute error.",
    template_summary="NIST NumAcc4 variance method; predeclared conditions only", file_policy_prefix="nist",
    code_source="Morphogenesis public CPU experiment v1; CPython statistics (PSF-2.0)", code_license="Apache-2.0",
    data_source="https://www.itl.nist.gov/div898/strd/univ/data/NumAcc4.dat",
    data_license="NIST SRD licensing statement; see docs/experiments/upstream.md",
    _relative_directory="demo/research_case", _code_name="experiment.py", _data_name="NumAcc4.dat", _data_sha256=nist.NIST_DATA_SHA256,
    _judge=nist.assess,
)
_LINEAR = CaseDefinition(
    case_id="synthetic-linear-regression-v1", title="Synthetic deterministic linear regression",
    problem="Fit the project-owned synthetic seven-point dataset using CPython statistics.linear_regression.",
    claim="On the fixed synthetic seven-point dataset, CPython 3.12 statistics.linear_regression yields slope 1.5, intercept 2, every raw residual and SSE 0.25 within 1e-12 absolute error.",
    template_summary="Synthetic linear regression; predeclared coefficients, raw residuals and SSE only",
    file_policy_prefix="synthetic-linear-regression",
    code_source="Morphogenesis project-authored synthetic OLS candidate v1; CPython 3.12 statistics (PSF-2.0)",
    code_license="Apache-2.0", data_source="Morphogenesis project-owned synthetic seven-point dataset v1",
    data_license="Apache-2.0", _relative_directory="demo/research_cases/synthetic_linear_regression",
    _code_name="linear_regression.py", _data_name="data.csv", _data_sha256=linear_regression.DATA_SHA256, _judge=linear_regression.assess,
)


def get_case(case_id: str) -> CaseDefinition:
    if case_id == _NIST.case_id:
        return _NIST
    if case_id == _LINEAR.case_id:
        return _LINEAR
    raise ValueError("unknown_registered_case")


def public_case(directory: Path | str, *, role: Role = "author", order: Order = "original") -> ExperimentPlan:
    return _NIST.build_plan(role=role, order=order, directory=directory)
