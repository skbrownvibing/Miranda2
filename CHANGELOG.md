# CHANGELOG

## Current development cycle

### 2026-03-28 — Fix: contacts incorrectly shown as unresponded when recent texts use attributedBody
- Root cause: `i_replied_last` and `last_message_at` were derived from `relevant_rows[0]` (the most recent *parseable* row) rather than `rows[0]` (the actual most-recent DB row). When `m.text = NULL` and `attributedBody` parsing fails, recent text messages were dropped from `relevant_rows`, making old attachment rows appear as the last signal — causing fully-replied conversations to show as unresponded.
- Fixed by reading timing and reply-direction signals from `rows[0]` (actual last message) and only using `relevant_rows[0]` for the preview text.
- Updated `relevant_rows` filter to also retain rows with a non-NULL `attributedBody` blob (real messages even if unparseable) so they contribute to the reply signal.
- Updated `msg_text()` to render `'💬'` instead of empty string when `attributedBody` is present but unparseable, so the preview shows something rather than nothing.
- Updated `messages` preview array to use `display_msgs` (filtered display rows) instead of raw `msg_list[:5]`.

### 2026-03-28 — Light mode default, dark mode toggle, and score labels
- Added score tier labels shown in lowercase before the numeric score using the format `label (score)`, with ranges from `actively ghosting 👻` through `top 5% responder 🏆`.
- Switched the app to light mode by default and tuned key surfaces (backgrounds, cards, text, borders, and inputs) for light-mode-first readability.
- Added a top-bar dark mode toggle with localStorage persistence so users can manually switch themes and keep their preference on reload.
- Increased score label visual emphasis by moving it to the left of the score ring, enlarging typography, and removing the duplicate numeric value from the label so only the big ring number shows the score.
- Hardened score-label rendering to strip any trailing `(number)` suffix if present, ensuring text like `bad texter 😬` never re-shows as `bad texter 😬 (34)`.
- Centralized score-label cleanup in a dedicated helper to consistently enforce label-only rendering across score updates.
- Fixed `renderScore()` reassigning `score-summary` multiple times; it now sets the cleaned label once so `(${score})` is not reintroduced.
### 2026-03-28 — Fix: messages with link previews show as "Attachment" instead of actual text
- Root cause: when an iMessage contains a URL, iMessage stores the actual message text in `m.attributedBody` (an NSKeyedArchiver binary blob) and leaves `m.text = NULL`. The exporter was only reading `m.text`, so it saw NULL, saw a real attachment join (the link preview card), and wrote "📎 Attachment" — even though the person sent a real text message.
- Added `extract_attributed_body()` helper that decodes the NSAttributedString binary plist and returns the plain text string.
- Updated `row_text()` to try `m.text` first and fall back to `attributedBody`.
- Updated both SQL queries to select `m.attributedBody`.
- Updated `relevant_rows` filter and all downstream row processing to use the resolved text.
- Re-export required to see correct message previews for affected conversations.

### 2026-03-27 — Fix old attachment rows in contact message preview
- Fixed the case where old photo/attachment rows from months ago appeared alongside a recent text message in the bubble view.
- Exporter: attachment-only rows that predate the most recent text message in the window are excluded from `messages`.
- Frontend: `recentPreviewMessages` applies the same filter on existing JSON so users do not need to re-export.


### 2026-03-27 — Product definition refresh
- Added a repo PRD documenting the current product scope, decision rules, scoring model, and future directions.
- Standardized product framing around responsiveness tracking rather than inbox triage.
- Clarified taxonomy so Logistics refers to automated or transactional texts, while human logistics messages remain in scope.
- Clarified longer-term direction around in-product reply workflows, while noting Apple platform constraints around real-time sync and import flow.
- Collapsed the score history/trend panel by default and added a Show/Hide score history toggle.
- Fixed Action Needed previews so attachments are only shown when they are inside the same last-5-message preview window (older attachments are no longer pulled into the preview).
- Added a new top-level Other texts section between Action needed and Auto-filtered texts, and limited Auto-filtered texts to Spam and Logistics only.
- Fixed Other texts routing to use the same uncategorized dataset as the previous Other review bucket.
- Updated Other texts to apply the same global timeline window and use expandable row behavior consistent with Action needed.
- Fixed Other texts routing to read the uncategorized bucket directly rather than routing through review panel logic, preventing accidental broadening or narrowing from changes to shared helpers.
- Hide the Other texts section entirely when there are no uncategorized conversations.

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
