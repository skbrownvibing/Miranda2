# CHANGELOG

## Current development cycle

### 2026-04-15 — Homepage readability touch-up (secondary CTAs + score spacing)
- Increased legibility for homepage secondary actions (`Upload export file`, `Set up one-click refresh`) by brightening text/border contrast and slightly increasing button label emphasis.
- Tightened score headline spacing from `5% → 95%` to `5%→95%` for a more compact visual rhythm.

### 2026-04-15 — Homepage polish pass (desktop width, ghost motion, CTA hierarchy)
- Widened homepage container to a desktop-friendly centered layout (up to ~900px) to reduce the narrow/mobile feel.
- Replaced Ghost Slayer label treatment with a larger ghost visual near the title and added a one-time drop/glide animation (~1.8s).
- Slowed unanswered-number animation to ~1.5s while keeping the final value fixed at `143`.
- Removed redundant homepage copy lines and simplified typography hierarchy so `Reply or Die` remains the dominant text.
- Replaced the score block copy with `👻 5% → 95% ⚡` and `Ghost → Elite Responder`, plus a compact three-line improvement list.
- Updated CTA hierarchy so demo remains primary and both `Upload export file` and `Set up one-click refresh` are matching secondary buttons.
- Removed extra boxed treatment around one-click setup and shortened helper copy to `Connect once, then press Refresh`.

### 2026-04-15 — Homepage structure refresh + explicit demo-entry flow
- Replaced the homepage/import screen content with a clearer hierarchy: Ghost Slayer banner, hero/tagline, short description, feature line, score-range visual, and a primary demo CTA.
- Added a one-time Ghost Slayer count animation on homepage load (lottery-style for ~1 second) that always settles on `143`.
- Added **See Inbox with Demo Data** CTA wired to bundled demo JSON loading only (with existing demo timestamp shifting), independent from saved local sessions.
- Stopped auto-entering the inbox on startup so homepage now always appears first.
- Removed **Resume last session** from homepage UI while keeping underlying localStorage/session logic in code.
- Kept existing upload and one-click connected-source flows (connect/refresh/change source) without inbox logic refactors.

### 2026-04-15 — Top-tier label keeps trophy emoji
- Updated the highest score-tier copy to **ELITE responder 🏆**.

### 2026-04-15 — Score label copy tweak
- Changed the top score-tier label from **top 5% responder 🏆** to **ELITE responder**.

### 2026-04-14 — Bundled demo auto-load + relative timestamp shifting
- Added startup fallback to auto-load `data/miranda_demo.json` when there is no user-uploaded JSON saved locally.
- Added a minimal demo-only timestamp shifter so demo data always feels current on load.
- Shift logic computes `delta = now - exported_at` and applies it to `exported_at`, `conversation.last_message_at`, `conversation.latest_inbound_at`, and each `message.date`.
- Kept uploaded/imported JSON behavior unchanged.

### 2026-04-13 — Dismissed-thread checkpoint fallback hardened for legacy records
- Fixed a legacy-dismiss edge case where threads could reappear after reload when older dismiss records had no `inboundCheckpointAt`.
- Updated new-inbound detection to fall back to `dismissedAt` (when checkpoint is missing) instead of auto-treating every thread as having new inbound activity.
- Kept normal behavior unchanged for current exports that include `latest_inbound_at` and set checkpoint timestamps at dismiss time.

### 2026-04-09 — Ignored conversations now survive re-imports
- Refactored ignored-conversation persistence to store records keyed by stable participant identity instead of transient export thread IDs.
- Added an inbound-message checkpoint to each ignore record so ignored threads reappear only after a real new incoming text message arrives.
- Added fallback migration from legacy dismissed storage (`miranda2_dismissed_v1`) into the new persistence model when possible.
- Kept ignored conversations hidden across reload/refresh/re-import when underlying inbound text state has not changed.

### 2026-04-08 — Refresh split into two explicit actions + local export runner hook
- Added two separate connected-source actions:
  - **Run export + reload** (new): calls a local localhost runner to execute `export.command`, waits for completion, then reloads JSON.
  - **Reload current JSON** (existing fallback): re-reads the currently connected JSON file only.
- Added explicit refresh status messaging states in-app: idle, running export, reloading data, success, export failed, runner unavailable, and output unchanged.
- Kept `loadFile(file)` parsing/import flow intact and reused it for all reload behavior.
- Preserved last successful loaded data if export or reload fails.
- Updated source-panel copy/tooltips to remove ambiguity between rerunning export vs re-reading current JSON.

### 2026-04-07 — Top-bar actions simplified for main workflow
- In the loaded app header, kept only **Refresh messages** and **Home** as primary actions.
- Renamed **New export** to **Home** and removed **Connect export file** / **Change source** from the loaded-app top bar.
- Kept source-management actions on the Home/import view (**Connect export file**, **Change source**), with refresh still available there.
- Kept a single freshness label in the header and clarified copy to **Last updated: ...**.

### 2026-04-07 — Partial UX rename to “Reply or Die”
- Updated the two primary in-app brand labels from **Miranda2** to **Reply or Die** (import screen title and top-bar brand).
- Kept internal naming and file/export identifiers unchanged for this pass.

### 2026-03-31 — Refresh reliability + single-source top-bar time
- Simplified top-bar freshness display to a single source of truth: **Last exported: …** (derived from `exported_at`), removing conflicting secondary "updated" copy.
- Renamed connected-source refresh action to **Re-read export file** to clarify that it re-reads the selected JSON and does not run `export.command`.
- Hardened connected-source refresh/connect flow by making `loadFile(file)` return a Promise and awaiting it in one-click actions, so parse/read failures are surfaced instead of failing silently.
- Simplified connected-source status text to only show the connected file name in the drop-screen panel.
- Fixed one-click support gating to depend on File System Access availability (not IndexedDB), so Chrome no longer falls back to “unsupported” when persistence is blocked.
- Added clearer source-state messaging for context restrictions and session-only mode when IndexedDB is unavailable.
### 2026-03-31 — Filtered-out review UX simplified (Spam + Logistics merged in UI)
- Replaced separate **Spam** and **Logistics** tabs in Auto-filtered texts with one **Filtered out** tab showing the combined total.
- Kept categorization behavior unchanged (`spam` and `delivery` rules/overrides stay the same); this is a presentation-only merge.
- Added per-row reason badges (`Spam` or `Logistics`) inside the combined filtered list so users can still see why each thread was filtered.
- Simplified expanded row actions in **Action needed** and **Other texts** by replacing separate `→ Logistics` and `→ Spam` buttons with one **Filter out** menu.

### 2026-03-30 — Top bar de-duplicated back to one row
- Fixed an accidental duplicated top-bar layout that showed the app name twice and rendered duplicate **dark mode** + timeline controls.
- Restored a single-row top bar with one `Miranda2` title on the left and one control cluster on the right.
- Kept existing controls in that single row (`dark mode`, timeline filter, freshness labels/source actions, and **New export**) so functionality stays the same while the header is cleaner.

### 2026-03-29 — Connected source top-bar cleanup (Phase 1 UX polish)
- Simplified the connected-source top bar into two rows: row 1 (title, dark mode, timeline filter) and row 2 (`Updated X ago`, Refresh, Change source).
- Removed persistent connected-file labeling from the top bar and removed the **New export** top-bar button.
- Switched connected-source freshness copy to short relative format (`Updated 2m ago`) instead of long absolute timestamps.
- Kept import behavior unchanged; this is a UI-only cleanup on top of the existing Phase 1 connected-source flow.

### 2026-03-29 — Phase 1 connected export file refresh flow
- Added a one-time **Connect export file** flow using the File System Access API so users can pick `miranda2_messages.json` once, then refresh with one click.
- Persisted the connected file handle in IndexedDB with minimal metadata (`fileName`, `lastRefreshedAt`) and restored connected state on app load.
- Added connected/disconnected source UI states with **Refresh messages** and **Change source** actions, plus connected status and last updated display.
- Wired both Connect and Refresh flows to produce a `File` and pass it into the existing `loadFile()` import handoff (no parallel import pipeline).
- Added graceful fallback messaging for unsupported browsers, permission failures, missing source, and refresh/read failures while keeping manual import and drag/drop intact.
### 2026-03-29 — Suggested Reply now uses real AI generation with broader coverage
- Replaced the deterministic Suggested Reply stub (question-mark-only canned output) with an async model call in the existing button flow.
- Kept UI behavior unchanged (Generate reply, Generating… state, suggested output, Copy, and no-regenerate behavior).
- Kept context builder behavior to use the latest non-empty chronological messages (up to 15) with explicit `Me` / `Them` labels.
- Removed attachment-keyword and long-message skip heuristics; generation now attempts broadly and only skips for empty context, last message from `Me`, or AI failure.
- Added temporary `REPLY_CONTEXT_AUDIT` console logging so input context can be verified during testing.
- Added temporary `REPLY_MODEL_OUTPUT_AUDIT` logging for generated copy quality checks (without logging secrets).
- Added a minimal AI config path using `window.MIRANDA2_AI_CONFIG` (apiKey/model/endpoint) with localStorage fallback keys for API key and model.
- Added explicit local-only warning in code comments: browser-side API keys are exposed and not suitable for shareable/public deployment.

### 2026-03-28 — Score history now uses a fixed local 7-day snapshot
- Standardized score history saves to always compute from a fixed trailing 7-day window, independent of the currently selected UI timeline filter.
- Kept one score snapshot per local calendar day with same-day overwrite behavior (latest save wins).
- Switched the daily history key from UTC date to local date to avoid wrong-day saves around midnight.
- Clarified Score history UI copy to explicitly label trend snapshots as 7-day scores.

### 2026-03-28 — Fix: preview rows now use true last 1–2 chronological messages
- Root cause: preview rows were built as "latest from Them" plus "latest from You", then rendered in fixed sender order, which could imply the wrong person replied last.
- Fixed by selecting the last 1–2 actual non-empty message events from each thread and rendering them oldest-first with `Them:` / `You:` labels based on each event's sender.
- Follow-up: preview selection now reads from the full exported `messages` array before taking the last 2 displayable rows, so it does not depend on an extra UI-side `slice(-5)` window.
- Follow-up: added explicit `PREVIEW_INCLUDE_ATTACHMENT` toggle and `previewTextIncluded()` helper to make collapsed-preview inclusion rules intentional and easy to adjust.
- Result: previews now reflect real thread chronology (including same-sender pairs like Them→Them or You→You) without forcing one line per sender.
### 2026-03-28 — Top-bar “Last updated” freshness indicator
- Added a minimal `Last updated: …` label in the top-right action area next to **New export**.
- Uses `exported_at` from the loaded JSON as the primary freshness source, with `savedAt` fallback only when `exported_at` is missing.
- Keeps the default UI to a single relative timestamp and shows the exact local timestamp on hover.
- Updates the relative label dynamically over time (minutes → hours → days).
- Applies subtle visual de-emphasis when the loaded export is older than 24 hours.
- Hides the indicator when no data is loaded.

### 2026-03-28 — Fix: score now updates when non-contact threads leave Needs Action
- Root cause: score computation filtered out threads without `contact_name`, while Needs Action state and other stats already include eligible unsaved-number 1:1 threads.
- Fixed by removing the `contact_name` requirement from `allPersonalInTimeline()`, so score calculation uses the same in-scope conversation set (excluding only spam, Logistics, and group chats) as the rest of the responsiveness state.
- Result: marking a thread as **No reply needed** (or moving it out of Needs Action via similar state changes) now immediately updates the main score and score label without refresh.

### 2026-03-28 — Ensure expanded message rows render as plain text blocks
- Added explicit `.detail-messages > div` reset styles (no background, border, border-radius, or padding) so expanded rows render as simple text lines rather than bubble-like containers.
- Kept timestamps visible and message-row rendering logic unchanged (plain text rows with empty-text filtering).
### 2026-03-28 — Fix: JSON import flow blocked by script parse error
- Root cause: a stray chained `.map(...)` remained in both `renderActions()` and `renderOtherTexts()` after the plain-text row rendering update, causing a JavaScript parse error (`Unexpected token '.'`) that prevented app initialization.
- Fixed by removing the orphaned `.map(...)` blocks so the script initializes and file import works again.

### 2026-03-28 — Action needed expanded rows now render plain text lines
- Changed Action needed expanded rows to render message text as plain inline text (no chat-bubble styling).
- Kept per-message timestamps visible.
- Skipped empty/blank message rows so no empty message containers are shown.

### 2026-03-28 — Literal chronology for thread display (separate from response status)
- Changed thread display to use literal chronology only: the latest item shown in each thread is the true newest source event, even when it is a reaction, attachment, blank-ish row, or other odd terminal event.
- Changed expanded conversation previews to render the literal newest 5 chronological events with no relevance filtering or semantic substitution.
- Added dedicated display fields to export output: `latest_event_at`, `latest_event_text`, `latest_event_from_me`, and `recent_events`.
- Kept response-status logic separate (`i_replied_last`, dismissal, scoring inputs), so status no longer controls which latest event is displayed.

### 2026-03-28 — Compact score history card header
- Reduced the collapsed Score history card height by tightening card padding.
- Moved the collapsed header content to a single row so `Score history` and `Last score` sit side-by-side for a compact footprint.
- Added top spacing before expanded trend details so the open state still breathes.
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
- Redefined Other texts to show unknown 1:1 senders in timeline that are not Action needed and not Spam/Logistics.
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
