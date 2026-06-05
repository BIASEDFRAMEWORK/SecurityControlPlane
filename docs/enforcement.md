# Enforcement Setup

Use branch protection or a repository ruleset for `main` and require the three checks below.

Required status checks:

- `Explainability - PR security intent`
- `Prevention - secret scan`
- `Auditability - enforcement evidence`

Recommended settings for the demo:

- Require a pull request before merging.
- Require the status checks above to pass before merging.
- Require branches to be up to date before merging if you want to show the checks rerun after new commits.
- Include administrators or bypass actors only if you want to discuss exception handling.

Why this matters:

- The PR template encourages the right explanation, but the workflow makes it enforceable.
- The secret scan is useful on its own, but it becomes a prevention control only when it is a required check.
- The audit job runs with `if: always()`, so it still produces evidence when explainability or prevention fails.
- The workflow includes `merge_group` so required checks can run in repositories that use GitHub merge queue.

Official GitHub references:

- Pull request templates: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository
- Status checks: https://docs.github.com/articles/about-statuses
- Protected branches: https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches
- Workflow artifacts: https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts
- Job summaries: https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions
