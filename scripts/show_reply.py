"""Print one stored reply from the results database: python -m scripts.show_reply <run_id> <case>"""

import sys
import textwrap

from evals import store

row = next(r for r in store.load_results(sys.argv[1]) if r["case_id"] == sys.argv[2])
failed = [name for name, ok in row["checks"].items() if not ok]
print(f"{sys.argv[2]} in {sys.argv[1]}   failed: {', '.join(failed) or 'nothing'}\n")
print(textwrap.fill(row["reply"], 100))
