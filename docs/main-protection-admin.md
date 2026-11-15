# #207 administrator handoff

The current actor `lesyhuy2k6-gif` has push permission but no admin permission.
Current rules enforce PR/one approval without required CI checks. This is an
access blocker, not a completed settings change. Keep #207 open until verified.

An organization/instructor administrator, or repository administrator who can
add repository rules, must apply the reviewed supplemental ruleset in
[.github/main-protection.json](../.github/main-protection.json). Existing
organization rules remain unchanged. No bypass actor is granted by this proposal.

After the implementation PR has green named checks, in an administrator's
trusted checkout, using the administrator's existing secret environment:

```bash
python tools/main_protection.py --apply
python tools/main_protection.py
```

The token is supplied privately through `GH_TOKEN`/`GITHUB_TOKEN`, with repository
administration write permission and organization access if required. Do not put
it in arguments, Git, screenshots or chat. The helper first verifies admin
permission, then creates/updates only `main-ci-protection`; non-admins cannot
mutate anything. Read-back must report `verified: true` with `CI gate`,
`Python tests`, and `No secrets committed`, strict/up-to-date enforcement and
at least one approval. GitHub Actions App ID is 15368.

Alternatively use GitHub Repository Settings → Rules → Rulesets → New branch
ruleset: Active; only `main`; require PR/one approval; dismiss stale approvals;
require approval for latest push; block force push/deletion; no bypass; require
the three checks above from GitHub Actions, with branches up to date. Repository
rules supplement the inherited organization rules and cannot weaken them.

Retain the actual applied ruleset ID/URL, API read-back and a **new screenshot**
of those settings with approval/required checks expanded. The committed baseline
screenshot proves only the old settings, not the administrator's future action.
Verify that a red PR cannot merge without attempting to bypass the rules or
merge the intentionally failing rehearsal. Ask another teammate to approve the
implementation; do not approve or merge it as its author.

Official references: [ruleset capabilities/access](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets),
[rules REST API](https://docs.github.com/en/rest/repos/rules). The tool's JSON
proposal is reviewable configuration, not proof of applied settings.
