# Registered research cases

The trusted operator selects a case before registering the acceptance plan. Native tool
input cannot change that selection, criteria, resources, images or permissions. There are
exactly two fixed definitions; no dynamic registration, validator command or import path.

```python
from pathlib import Path
from orchestration.experiments.case import get_case

definition = get_case("synthetic-linear-regression-v1")
plan = definition.build_plan(role="author", order="original", directory=None)
candidate = Path(plan.code.local_path).read_bytes().decode("utf-8")
```

`CaseDefinition` is a frozen dataclass. Public metadata fields are strings:
`case_id`, `title`, `problem`, `claim`, `template_summary`, `file_policy_prefix`,
`code_source`, `code_license`, `data_source`, `data_license`. `case_id` is also the
typed `plan.criteria.version`; `claim` and `plan.claim` come from the same definition.
`build_plan(role="author", order="original", directory=None)` returns `ExperimentPlan`.
Roles remain author/replication/inheritance. All three positive role plans use original
order and the same code, data, criteria, environment and seed; only role changes.
Unknown IDs raise `ValueError("unknown_registered_case")`. Unknown criteria/validator
fields fail Pydantic validation. Invalid registered code/data fails before backend create.

| ID / criteria version | Installed relative directory | Candidate / data | Order |
|---|---|---|---|
| `nist-numacc4-v1` | `demo/research_case` | `experiment.py`, `NumAcc4.dat` | original/reverse |
| `synthetic-linear-regression-v1` | `demo/research_cases/synthetic_linear_regression` | `linear_regression.py`, `data.csv` | original only |

`directory=None` locates these included assets in the source checkout or installed
distribution. Explicit `directory=Path(...)` means the case's input directory, containing
the named candidate and data directly, not the repository or demo parent. It does not
register new code or datasets. Candidate text always comes from `plan.code.local_path`;
B/P must not copy a separate template or judge. Packaging uses the existing `demo/**`
include; no dependency, lock, core pyproject or distribution checker change is needed.

The original `public_case(directory, *, role="author", order="original")` delegates to
NIST and retains the exact original claim, plan ID, sources, defaults and file names.
NIST problem/template summary and `file_policy_prefix="nist"` preserve B's existing
strings and `nist-{role}-files-v1` policy. The old criteria default and archives lacking
the default version remain readable. `scientific.observations` and `NIST_DATA_SHA256`
are compatibility exports; NIST's actual formulas live in `experiments.nist` unchanged.
Mean/variance/raw residual tolerances remain 1e-8/1e-9/1e-8, count 1001, original/reverse
ordering and the Naive cancellation control remain intact. Notebook's registered NIST
`experiment.ipynb`, the existing nbclient runner and Code Interpreter protocol remain.
Optional backend capabilities remain explicit; this change adds no backend capability.

Both cases use the same ExperimentExecutor, OpenSandbox 1.1.0, fixed images,
`shlex.join` command adapter, once budget, identity/fencing and archive/read_result.
The common output file is `metrics.json`; its scientific contents belong to each judge.
read_result verifies plan/context and original raw byte digests, then recomputes the
assessment from archived raw inputs/outputs. Registered source candidates permit the
two LF/CRLF checkout representations; archives are never normalized or rewritten and
must still match their original code digest. This is integrity checking, not attestation
of an untrusted archive. The evidence root and installed registry must be host protected.

## Synthetic case: predeclared conditions and provenance

The dataset is project authored, synthetic, deterministic, Apache-2.0 under the repository
LICENSE, version 1. It is not an external scientific discovery or an algorithm comparison.
The case-local Git attribute preserves CSV bytes across Windows checkouts and wheels.
Seven rows use x=-3,-2,-1,0,1,2,3 and y=1.5*x+2+e, where
e=(1/4,-1/4,0,0,0,-1/4,1/4). The exact committed CSV is independently identified and
parsed by the host; header, row count, ordering, unique x values and full rank are fixed.
The seed remains 0; no randomness is used. Raw inputs are separate from output files.

Candidate version 1 is project authored Apache-2.0 Python. It calls mature CPython
3.12 `statistics.linear_regression` (PSF-2.0), without copying upstream implementation.
The existing image is CPython 3.12.13 at the unchanged pinned digest. The host judge uses
`fractions.Fraction` and the independently written exact OLS equations:
slope=sum((x-mean_x)*(y-mean_y))/sum((x-mean_x)^2), intercept=mean_y-slope*mean_x,
residual=y-(slope*x+intercept), SSE=sum(residual^2). It verifies slope=3/2,
intercept=2 and SSE=1/4 from original input, then checks every reported raw residual.
Coefficient, residual and SSE absolute tolerances are each fixed at 1e-12. Criteria
cannot loosen these values. Candidate outputs contain count/slope/intercept/residuals/sse;
missing raw residuals, booleans, nonfinite numbers, wrong coefficients/SSE and fake
summary/verdict fields fail trusted assessment. The candidate never reports passed.

`ScientificAssessment` keeps shared verdict/reasons/metrics/criteria_version fields.
NIST metrics stay NIST-owned; synthetic metrics report coefficient and SSE errors.
Scientific failure remains distinct from failed/timeout/unknown/unsupported execution
and missing artifacts. No not_evaluated result is promoted to passed. Unknown remote
effects, cleanup, exit, usage and cost semantics remain unchanged; no automatic replay.
Offline mock evidence is contract_local only. Two-case task_live requires I's new,
authorized run from the cumulative frozen product; no such run is performed by C.
