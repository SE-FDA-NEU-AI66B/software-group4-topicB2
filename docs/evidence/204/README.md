# #204 isolated database evidence

This directory contains execution evidence for the production database work,
using synthetic temporary SQLite storage only. No production database, backup
file, account export or secret is committed. See
[the persistence/runbook document](../../database-operations.md) for commands,
storage limits and remaining hosting verification.

- `pytest.txt` / `pytest.xml`: first full branch run, 206 passed in 56.91s,
  before integration of the ten deployment cases from main PR #226.
- `integrated-pytest.txt` / `integrated-pytest.xml`: full run after integrating
  main `6acf0dd`; see testing.md for the actual final count and duration.
- `restore-check.json`: actual CLI seed, backup and isolated restore commands,
  equality/integrity/FK results and recovered synthetic marker. Temporary paths
  identify the drill; the database files were removed after successful execution.

The operator was OpenAI Codex using Windows/Python 3.11.9, not an independent
teammate or a live Render deployment. Hosting, backup scheduling and secure
off-host transfer are not certified by these local artifacts.

Merge with main `83f76aa`: `merge-first-pytest.txt` / `.xml` preserve the
initial browser synchronization timeout (1 failed / 228 passed). `merge-pytest.txt`
/ `.xml` record the full rerun after explicitly waiting for both fetched rating
questions and checking their selected state. See testing.md for actual results.

`merge-second-pytest.txt` / `.xml` retain the second run (1 failed / 228 passed)
where the existing phone empty-answer test clicked Review before questions
loaded. The final rerun includes explicit loaded-form preconditions in that
test and the canonical-seed reload test; no assertions or cases are skipped.

Final `merge-pytest.txt` / `.xml`: **229 passed in 78.53s**, zero failures,
errors or skips, on main `83f76aa` plus #204 and both browser synchronization
corrections. Earlier files remain unchanged historical evidence.
