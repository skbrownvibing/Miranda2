# CHANGELOG

## Current development cycle

### 2026-03-27 — Product definition refresh
- Added a repo PRD documenting the current product scope, decision rules, scoring model, and future directions.
- Standardized product framing around responsiveness tracking rather than inbox triage.
- Clarified taxonomy so Logistics refers to automated or transactional texts, while human logistics messages remain in scope.
- Clarified longer-term direction around in-product reply workflows, while noting Apple platform constraints around real-time sync and import flow.

### v0.11 — Category Review Panel (Mar 26, 2026)
- Added a review workflow for auto-filtered texts below the action list.
- Added category tabs with counts for Spam, Logistics, and Other.
- Added reclassification actions so users can move conversations back to Personal or into Spam.
- Persisted overrides in localStorage.
- Limited review lists to the 50 most recent texts per category.

### v0.10 — Score History + Gamification (Mar 26, 2026)
- Added score history with one saved score per day, stored locally for up to 90 days.
- Added a trend chart showing first session, latest session, and personal best.
- Added summary stats for all-time best, average score, and total sessions.
- Added delta vs. previous session.
- Added current streak and longest streak.

### v0.9 — Responsiveness Score Redesign (Mar 25, 2026)
- Repositioned the product from inbox triage to responsiveness tracking.
- Added a 0–100 responsiveness score based on reply rate, average wait time, and hanging conversations weighted by age.
- Replaced the old inbox-style workflow with an action list of unreplied 1:1 personal texts, sorted by urgency.
- Added dismiss state for “No reply needed.”
- Excluded group chats, spam, and delivery/logistics texts from scoring.
- Moved timeline filtering into the top bar.

## Earlier major changes

### v0.8 — Two-Line Previews (Mar 25, 2026)
- Added separate preview lines for the latest message from them and the latest message from you.
- Showed only their line when no reply exists.

### v0.7 — Tighter Spam/Delivery Categorization (Mar 25, 2026)
- Added client-side re-categorization on JSON load, so classification updates do not require a fresh export.
- Expanded spam detection for political outreach, recruiter cold outreach, marketing promos, scams, dating spam, real estate blasts, medical marketing, short codes, and email senders.
- Expanded delivery/logistics detection for receipts, appointment confirmations, ride notifications, reservations, billing alerts, and verification codes.
- Preserved contact protection so these rules do not apply to saved contacts.
- Kept manual overrides as the highest-priority classification rule.
- Moved 350+ conversations from Other into Spam or Delivery.

### v0.6 — Group Chat Support (Mar 25, 2026)
- Added a hide-groups filter to remove group chats from the main list.
- Improved group labeling and display names for named and unnamed groups.

### v0.5 — Timeline Filter (Mar 25, 2026)
- Added timeline presets for 24 hours, 3 days, 7 days, 30 days, 3 months, 1 year, and all time.
- Added custom date range support.
- Defaulted the view to the last 7 days so old conversations do not dominate.

### v0.4 — Contact-Based Category Protection (Mar 25, 2026)
- Prevented saved contacts from being auto-classified as Spam or Delivery.
- Kept manual overrides above contact protection.

### v0.3 — Persistence + Visual Refresh (Mar 25, 2026)
- Added localStorage persistence for imported conversation data.
- Added a returning-user flow with “Continue with last export.”
- Added badges and stats for newly imported conversations.
- Refreshed the import screen and visual design.

### v0.2 — Categorization Fix (Mar 25, 2026)
- Changed saved contacts to default to Personal.
- Extended the lookback window from 30 to 90 days.
- Lowered the fallback threshold for unknown numbers from 5 to 3 messages.
- Expanded the number of conversations classified as Personal.

### v0.1 — MVP (Mar 25, 2026)
- Built a Mac export script that reads iMessage data, resolves contacts, auto-categorizes conversations, and outputs JSON locally.
- Built a single-file local web app with no external dependencies.
- Added conversation list, category tabs, search and filtering, dashboard stats, detail view, “Open in Messages,” and manual category overrides.
