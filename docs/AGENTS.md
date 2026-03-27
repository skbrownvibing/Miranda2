# AGENTS.md

## Source of truth
Read `docs/prd.md` before making product changes.
Read `CHANGELOG.md` for recent product and implementation context.

If implementation appears to conflict with the PRD, flag the mismatch before making major changes.

## Working style
Explain the plan before coding.
Make the smallest viable change.
Do not rewrite unrelated files.
Do not make large architectural changes unless explicitly asked.

This is a learning project. Assume the user is non-technical.
When making changes:
- explain what you are changing in plain English
- explain which files you changed and why
- explain important technical concepts briefly and clearly
- prefer simple solutions over clever ones
- surface tradeoffs instead of silently choosing more complexity

## Product guardrails
This product is a local-first Mac tool for measuring and improving text responsiveness.

Key product rules:
- focus on 1:1 personal conversations
- exclude group chats and spam from scoring and action lists
- exclude Logistics conversations only when they are automated or transactional
- human logistics messages remain in scope
- reactions, tapbacks, and similar non-message events do not count as messages requiring a response
- dismissed conversations should not count against the user until a new relevant incoming message arrives
- do not expand the product into a full messaging client unless explicitly asked

## Technical guardrails
Keep the product local-first.
Do not introduce servers, user accounts, or cloud sync unless explicitly requested.
Prefer minimal, understandable changes over large refactors.
Avoid unnecessary dependencies.
When possible, keep the code easy for a non-expert to read and modify.

## Documentation
After making a meaningful change:
- update `CHANGELOG.md` for shipped behavior changes
- update `docs/prd.md` if product definition, decision rules, scoring logic, or scope has changed
- flag stale documentation if you notice it

## Commands
Install: [fill in]
Dev: [fill in]
Test: [fill in]
Lint: [fill in]
Build: [fill in]
