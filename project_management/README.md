# Project Management

This directory records how a two-person team plans, reviews, and develops a
modular Pac-Man implementation in Python and Pygame for the 42 curriculum.
It complements Jira task tracking with repository-level engineering decisions
and delivery evidence.

## Tracking and Methodology

- **Tooling:** Jira is used for issue tracking, user story estimation, and
  sprint management (issue keys prefix: `PK-`).
- **Workflow:** Jira-linked feature branches use peer-reviewed pull requests
  and automated checks before merging into `main`.
- **Branch rule:** Every pull request targets `main`. A branch is refreshed
  from the latest `main` before review instead of using another feature branch
  as its final target.
- **Documentation:** Completed phase history and engineering decisions are
  documented here. Sprint status, assignments, and active planning remain in
  Jira and the progressive planner.

## Shared Engineering Rules

- Treat a growing file as a signal to review its responsibilities. There is no
  fixed line limit, but a file should not become the default home for unrelated
  behaviour.
- Keep application state, rendering, runtime orchestration, gameplay rules,
  persistence, and external integrations separated by clear module boundaries.
- Keep functions focused on one behaviour. Split work when a function starts
  coordinating unrelated decisions, side effects, and presentation concerns.
- Extract a coherent responsibility rather than moving code only to reduce a
  line count. Names and dependencies should make the new boundary clear.
- Keep domain rules independent from pygame and other UI details so they can be
  tested without opening a window.
- Preserve public behaviour during structural refactoring. Run the complete
  test suite and both standard and strict lint checks before review.
- Organize tests by responsibility and scope. Keep reusable fakes in
  `tests/support` and distinguish focused rule tests from integration flows.
- Review architecture progressively as the project grows instead of waiting
  until the final phase for one large rewrite.

## Evidence

- [`phase_history.md`](phase_history.md) records delivered results and phase
  reviews.
