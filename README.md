# Secrets Control Demo for GitHub Actions

This repo is a small demo project for the deck `AI Made Developers Faster, Security Must Make Delivery Safer`.

The demo shows how a security team can use the CI/CD platform to create three concrete outcomes around a problem every engineering audience understands: secrets.

| Outcome | Demo mechanism | Visible proof |
| --- | --- | --- |
| Explainability | Pull request template plus a required PR-body validation check | Developers must state whether the change touches secrets, credentials, tokens, environment variables, or sensitive configuration before review. |
| Prevention | Required secret scan on pull requests | A fake canary secret is blocked before it can merge into `main`. |
| Auditability | Evidence job that runs even when controls fail | The workflow records who changed it, which checks ran, what was blocked or approved, and when enforcement happened. |

## What to show

1. Open a pull request with an incomplete security section.
   The `Explainability - PR security intent` check fails and tells the developer what is missing.
2. Push the intentionally leaky demo change from `scripts/make_leaky_demo_change.sh`.
   The `Prevention - secret scan` check fails before the secret reaches the shared branch.
3. Open the `Auditability - enforcement evidence` job summary or artifact.
   It shows actor, PR, commit, changed files, check outcomes, decision, and timestamp.

## Local rehearsal

Run these from the repo root:

```bash
bash scripts/run_three_outcomes_demo.sh
```

Or run the individual checks:

```bash
python3 scripts/validate_security_intent.py --body demo/pr-body-pass.md
python3 scripts/validate_security_intent.py --body demo/pr-body-fail.md
python3 scripts/secret_scan.py --paths app/main.py
bash scripts/make_leaky_demo_change.sh
python3 scripts/secret_scan.py --paths app/payment_provider.py
bash scripts/make_safe_demo_change.sh
python3 scripts/secret_scan.py --paths app/payment_provider.py
python3 scripts/audit_report.py --explainability-result success --prevention-result success
```

The leaky script writes a fake canary secret, not a real credential. Use it only on a short-lived demo branch.

## GitHub setup

After pushing this repo to GitHub, configure branch protection or a repository ruleset for `main` and require these status checks:

- `Explainability - PR security intent`
- `Prevention - secret scan`
- `Auditability - enforcement evidence`

Detailed presenter flow: [docs/demo-script.md](docs/demo-script.md)

Spoken talk track and live demo actions: [docs/presenter-talk-track.md](docs/presenter-talk-track.md)

Enforcement setup notes: [docs/enforcement.md](docs/enforcement.md)
