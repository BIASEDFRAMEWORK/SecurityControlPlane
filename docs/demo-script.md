# Presenter Demo Script

For the spoken version with live stage directions, use [presenter-talk-track.md](presenter-talk-track.md).

## Setup

1. Push this repo to GitHub.
2. Configure `main` with branch protection or a repository ruleset.
3. Require these checks:
   - `Explainability - PR security intent`
   - `Prevention - secret scan`
   - `Auditability - enforcement evidence`

The controls are split into three teaching-sized workflow files:

- `.github/workflows/secrets-explainability.yml`
- `.github/workflows/secrets-prevention.yml`
- `.github/workflows/secrets-auditability.yml`

For local rehearsal before the live GitHub demo:

```bash
bash scripts/run_three_outcomes_demo.sh
```

Set `NO_PAUSE=1` to run it without presenter pauses:

```bash
NO_PAUSE=1 bash scripts/run_three_outcomes_demo.sh
```

## Demo 1: Explainability

Create a branch and open a pull request with the security section left incomplete.

Expected result:

- `Explainability - PR security intent` fails.
- The job summary tells the developer exactly which security intent fields are missing.
- Presenter line: "Before review, the developer has to say whether this change touches secrets, credentials, tokens, environment variables, or sensitive configuration."

## Demo 2: Prevention

Create a short-lived branch:

```bash
git checkout -b demo/block-secret
bash scripts/make_leaky_demo_change.sh
git add app/payment_provider.py
git commit -m "Demo: add provider integration"
git push -u origin demo/block-secret
```

Open a pull request to `main` and complete the PR security section with `Yes`.

Expected result:

- `Explainability - PR security intent` passes because the developer explained the sensitive change.
- `Prevention - secret scan` fails because the branch contains a fake canary secret.
- The PR cannot merge when the checks are required.
- Presenter line: "This is not a ticket after the fact. The credential is stopped before it enters shared history."

## Demo 3: Auditability

Open the failed auditability workflow run and select `Auditability - enforcement evidence`.

Expected result:

- The job summary shows actor, event, PR number, commit, changed files, checks, decision, and UTC timestamp.
- The `security-enforcement-evidence` artifact contains Markdown and JSON versions of the same record.
- Presenter line: "The control leaves evidence: who changed it, what ran, what was blocked, and when enforcement happened."

## Fix Path

Update the same branch with the safe version:

```bash
bash scripts/make_safe_demo_change.sh
git add app/payment_provider.py
git commit -m "Use runtime environment for provider token"
git push
```

Expected result:

- Secret scan passes.
- Audit evidence decision changes from `blocked` to `approved`.
- The PR can merge when all required checks pass.
