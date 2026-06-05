# Deck Context

Source reviewed: `/Users/dustingaspard/Documents/Talks/AIMakesUsFasterSecurityMakesUsSafer.pptx`

The deck argues that AI increases the speed and volume of code change, so security needs controls where code already moves: repositories, branches, pull requests, and CI/CD.

The demo is built around the deck's sequence:

| Deck idea | Demo translation |
| --- | --- |
| Every change should explain itself before it ships. | Required PR-body check asks whether the change touches secrets, credentials, tokens, environment variables, or sensitive configuration. |
| Stop risky changes before they merge. | Required secret scan fails the pull request when a fake canary secret appears in changed code. |
| Keep secrets out of shared history. | The blocked PR never merges into `main`; the bad value stays confined to the demo branch. |
| Build it, test it, scan it, validate it, record the result. | Workflow job summaries and artifacts record the check outcomes and enforcement decision. |

Presenter framing:

> "The security team is not asking developers to leave their workflow. The control appears where review already happens, gives immediate feedback, and leaves evidence behind."
