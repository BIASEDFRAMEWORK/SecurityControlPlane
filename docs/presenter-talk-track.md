# Presenter Talk Track: Secrets Control Demo

Use this as the spoken script and live demo checklist. The goal is to show that a security team can use CI/CD to create three outcomes around secrets: explainability, prevention, and auditability.

## Before The Demo

Have these ready:

- A GitHub repo containing this project.
- A `main` branch protected by required checks.
- Required checks configured:
  - `Explainability - PR security intent`
  - `Prevention - secret scan`
  - `Auditability - enforcement evidence`
- A terminal open at the repo root.
- The GitHub pull request page open in a browser.

Optional local rehearsal:

```bash
bash scripts/run_three_outcomes_demo.sh
```

## Opening

Say:

> "AI is increasing the speed and volume of code change. That does not mean security can ask every team to stop and wait. It means security has to put repeatable controls where code already moves: repositories, pull requests, and CI/CD."

Say:

> "This demo uses a problem everyone understands: secrets. I am going to show three outcomes. First, the change has to explain whether it touches sensitive configuration. Second, the pipeline blocks a secret before it reaches the shared codebase. Third, the workflow leaves evidence of who changed it, what ran, what was blocked or approved, and when enforcement happened."

Action:

- Show the repo file list.
- Point out `.github/workflows/secrets-control.yml`.
- Point out `.github/pull_request_template.md`.

Transition:

> "The important thing is that this is not a separate security portal. It is inside the developer workflow."

## Outcome 1: Explainability

Say:

> "The first outcome is explainability. Before review, the developer has to describe whether the change touches secrets, credentials, tokens, environment variables, or sensitive configuration."

Action:

- Open `.github/pull_request_template.md`.
- Show the `Security intent` section.
- Point to the Yes/No question, areas touched, explanation, and validation evidence.

Say:

> "A template by itself is a nudge. The CI check turns it into an enforceable review requirement."

Action:

- Open a pull request with the security section incomplete, or show the existing failed workflow result.
- Click the `Explainability - PR security intent` check.
- Show the job summary with missing-field guidance.

Expected result to narrate:

> "The check is not saying the code is bad. It is saying the change did not explain itself yet. The developer gets specific feedback before review starts."

If running locally, use:

```bash
python3 scripts/validate_security_intent.py --body demo/pr-body-fail.md
python3 scripts/validate_security_intent.py --body demo/pr-body-pass.md
```

Transition:

> "Now that the developer has explained the change, the next question is whether the change is safe to merge."

## Outcome 2: Prevention

Say:

> "The second outcome is prevention. This is where a security check becomes a gate. If a secret is found, the PR cannot merge into `main`."

Action:

- In the terminal, create or use a demo branch.
- Generate the intentionally unsafe demo change:

```bash
git switch -c demo/block-secret
bash scripts/make_leaky_demo_change.sh
git add app/payment_provider.py
git commit -m "Demo: add provider integration"
git push -u origin demo/block-secret
```

Action:

- Open the pull request.
- Complete the PR security intent section with `Yes`.
- Wait for GitHub Actions to run.
- Open the `Prevention - secret scan` check.

Say:

> "This file contains a fake canary secret. It is not a real credential, but it behaves like the kind of value we want to keep out of shared history."

Expected result to narrate:

> "The prevention check failed. The secret-like value is redacted in the output, and the PR is blocked. The important part is timing: this happens before merge, before release, before production risk, and before an incident ticket."

Point out:

- The check failed.
- The output shows `[REDACTED]`.
- The merge button is blocked when checks are required.

If running locally, use:

```bash
bash scripts/make_leaky_demo_change.sh
python3 scripts/secret_scan.py --paths app/payment_provider.py --redact
```

Transition:

> "Blocking the change matters, but security also needs to prove what happened."

## Outcome 3: Auditability

Say:

> "The third outcome is auditability. The workflow should leave behind evidence: who made the change, what checks ran, what was blocked or approved, and when the control was enforced."

Action:

- Open the failed workflow run.
- Click `Auditability - enforcement evidence`.
- Show the job summary.
- Download or open the `security-enforcement-evidence` artifact if useful.

Expected result to narrate:

> "This is the record a security team can point to later. It shows the actor, pull request, commit, changed files, checks, decision, and timestamp. Even when a control fails, the audit job still runs and records the enforcement decision."

If running locally, use:

```bash
python3 scripts/audit_report.py --explainability-result success --prevention-result failure --output-dir evidence/demo-run/blocked
```

Transition:

> "Now I will fix the change the way we want developers to fix it."

## Fix Path

Say:

> "The fix is not to hide the value better in source. The fix is to remove it from source and read it from the runtime environment."

Action:

```bash
bash scripts/make_safe_demo_change.sh
git add app/payment_provider.py
git commit -m "Use runtime environment for provider token"
git push
```

Action:

- Return to the pull request.
- Wait for checks to rerun.
- Open `Prevention - secret scan`.
- Show that it passes.
- Open `Auditability - enforcement evidence`.
- Show that the decision is now approved.

Expected result to narrate:

> "The developer did not need a separate process. The PR gave them the feedback, they fixed the branch, and the same control produced new evidence showing the approved result."

## Close

Say:

> "This is the pattern I want you to remember. Security did not slow delivery by moving review into a separate system. Security used the CI/CD platform to make every change explain itself, to block a known risk before it entered the shared codebase, and to leave an audit trail of the control being enforced."

Say:

> "Secrets are the example, but the pattern generalizes: explain the security impact, enforce the policy as a required check, and record the result where the work already happens."

## Backup Plan If GitHub Actions Is Slow

Say:

> "While the hosted workflow runs, I can show the same controls locally because the checks are implemented as repo-owned scripts."

Run:

```bash
bash scripts/run_three_outcomes_demo.sh
```

Then say:

> "The local output is the same logic the GitHub Actions workflow runs in the PR."
