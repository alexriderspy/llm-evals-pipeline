"""Pretty-print one case from the golden set: python -m scripts.show_case h12"""

import json
import sys

from evals.cases import load_cases

case = next(c for c in load_cases() if c.id == sys.argv[1])
print(json.dumps(case.model_dump(), indent=1, ensure_ascii=False))
