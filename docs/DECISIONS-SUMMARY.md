# Design decisions

This is the public record of the decisions I made on this project. I worked with an AI assistant (Claude) as a researcher and reviewer: it proposed options, checked AWS and GitHub documentation, and flagged risks. **Every decision below is mine.** The third column lists what I turned down.

Detailed working notes, ADRs and runbooks are kept local; this file is the summary.

## Decisions

| Date (2026) | I decided | I rejected | Reason |
|---|---|---|---|
| 10-06 | Primary region `eu-west-1` | `us-east-1` (cheaper) | Keep data in the EU |
| 10-06 | Accept up to $0.10 a month for remote Terraform state in S3 | Local state | Remote, locked state is the production standard |
| 10-06 | Human access by IAM user with a passkey, no access keys, `aws login` and an assumed role | Identity Center (needs an Organization, which ends the Free plan); access keys | No long-lived credentials |
| 10-06 | Dropped the rule "no IAM users" | Keeping it | It could not hold on a Free-plan account |
| 10-06 | My own naming convention: `region-account-env-service-id`, a 7-character collision-free id, named-user prefixes | Ad-hoc names | Parseable, unique, enforceable by script and CI |
| 10-07 | Two-phase deny on the state bucket: first block deleting it and its versions, then block versioning and lifecycle changes once it exists | One deny from day one (it would block the first apply); no deny | Protect state history without blocking my own bootstrap |
| 10-11 | State bucket lifecycle: expire old versions after 20 days, never expire the current one | Longer retention | Bound storage |
| 10-12 | No region deny in the permission boundary; protect the baseline instead (dependency checks before removal, no disabling versioning, no budget edits, TLS only) | An EU-only region lock | Real accounts use many regions |
| 10-12 | Credits may fund short-lived paid resources (ECS, not EKS), under budget limits and destroyed after each lab | Zero credits; EKS | Realistic architectures within a hard cost limit |
| 10-26 | Everything, including IAM roles, goes through Terraform | Creating the execution role by hand | Hand-made resources drift |
| 10-26 | Just-in-time elevation role: only my named user, fresh MFA, 15-minute session, root as break-glass only | Root grants a temporary policy every time; widening the everyday role | Fewer root sessions, named accountability |
| 10-26 | Stopped the lab-by-lab plan and re-scoped after an interview: a deployed landing zone applied by a pipeline | Continuing the manual labs | Hand-built IAM drifted from how enterprises work |
| 10-26 | The proof must be deployed infrastructure; the Free plan is fixed | Design-only as proof; moving to the Paid plan | Credibility |
| 10-26 | Mandatory approval gate on every apply | Branch protection and a manual trigger only | Match an enterprise setup as closely as the Free plan allows |
| 10-26 | Bootstrap by Terraform: one root session widens the elevation role, then a bootstrap root creates the OIDC provider, pipeline roles and boundary; the scenario is documented | Hand-created pipeline roles then imported | Everything created by code, documented end to end |
| 10-26 | One public repo that holds the code and deploys; account ID and role ARNs only in secrets; no plan output in public comments | Two repos; paying for GitHub Pro | The gate needs a public repo on GitHub Free; I accepted the account ID being semi-public |
| 10-26 | Simplified the project rules and tracking to three files | A larger rule set | It had become impossible to follow |

## How I worked

- I wrote the IAM policies myself and revised them after review (the elevation role's trust policy went through two versions, its permissions policy through four).
- I pushed back on proposals, for example the hand-made execution role.
- I asked for the interview that reset the project around what I actually wanted.
