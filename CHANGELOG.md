# CHANGELOG

## Current development cycle

### 2026-04-23 — Start screen redesign pass (phase 1 of new Reply or Die design)
- Fully redesigned the Home/start screen visual system to match the new editorial Reply or Die direction (darker canvas, serif headline treatment, lime primary accent, and cleaner hierarchy).
- Replaced the previous score-card hero on the start screen with a simpler launch-focused composition while keeping core entry actions intact.
- Preserved existing start-screen behavior and wiring: **See Inbox with Demo Data**, **Upload Export File**, and **Set up One-Click Refresh** continue using the same logic and handlers.

### 2026-04-17 — Top hero compacted vertically to surface Action needed sooner
- Reduced top hero vertical footprint by tightening score-section padding, internal gaps, and score-history spacing.
- Slightly reduced score ring size and headline/card sizing to keep hierarchy while bringing the next section higher on screen.
- Tightened metric-card vertical stack spacing/padding so the right column remains readable but more compact.

### 2026-04-17 — Inbox top section switched to compact 2-column score/metrics layout + light mode fix
- Fixed light-mode visual tokens so the updated dashboard styling remains readable and intentional when theme is set to light.
- Updated the score hero area to a desktop 2-column layout: left column now groups score label + score ring, right column stacks the three metric cards vertically.
- Reduced top-section vertical footprint so **Action needed** appears higher on the page while keeping all content, controls, and logic unchanged.
- Kept mobile behavior stacked/vertical and preserved existing runtime scoring/data behavior.

### 2026-04-17 — Inbox dashboard visual system restyled to match homepage
- Restyled the loaded inbox/dashboard experience with a darker gradient background and restrained glow treatment for stronger homepage alignment.
- Reworked the score hero hierarchy so the score label reads as a clear headline and the circular score ring acts as the main visual anchor.
- Upgraded the score ring to a branded cyan→purple→pink gradient treatment with subtle glow, while keeping score behavior and calculations unchanged.
- Converted metric, history, and list containers to restrained glass-style panels (low-opacity backgrounds, soft tinted gradients, blur, and softer borders).
- Reduced top-bar visual weight with quieter controls and de-emphasized branding treatment so content hierarchy leads the page.
- Applied consistent typography hierarchy and spacing polish across top section, score history, and action/review sections without changing information architecture or controls.

### 2026-04-17 — Homepage hero emoji size bump
- Increased the hero score-card emojis (ghost + trophy) by ~30% for clearer visual emphasis.

### 2026-04-17 — Homepage CTA dedupe + center arrow/emoji polish
- Removed the extra lower **Continue with last export** box from the homepage so demo entry is routed through the single main CTA.
- Kept **See Inbox with Demo Data** as the demo/saved inbox entry path.
- Refined the center arrow between score cards to render as a crisp circular arrow (not a glow blob).
- Explicitly preserved the ghost/trophy emojis above **YOU RIGHT NOW** and **YOUR GOAL**.

### 2026-04-17 — Homepage CTA behavior cleanup (single primary path + setup-only action)
- Changed **See Inbox with Demo Data** to always enter inbox: it now loads saved/current data when available, or fetches bundled demo data, saves it, and then opens inbox.
- Changed **Set up One-Click Refresh** to setup-only behavior: it opens/scrolls to the connected-source setup panel on the homepage and does not auto-enter inbox.
- Kept **Upload Export File** on the existing import flow (file picker → load/import → save current data → enter inbox).
- Hid the lower connected-source setup panel by default and only show it after the setup CTA is used, reducing duplicate/confusing entry points.

### 2026-04-17 — Homepage hero fit fix (title clipping + additional downscale)
- Fixed top-of-page clipping by making the home hero container start from the top with padding and scroll-safe overflow instead of vertically centering with hard viewport clipping.
- Reduced hero scale again (headline, cards, arrow, CTA/buttons, footer) so the full title remains visible and the page feels less zoomed.

### 2026-04-17 — Homepage hero sizing and cleanup pass
- Reduced oversized hero typography and card/control scaling so the home screen keeps the same horizontal composition but no longer appears zoomed in.
- Kept the top hero brand copy explicit and unchanged: **Reply or Die** + **Stop ghosting. Start responding.**
- Removed the bottom helper sentence on the home screen (`Run export.command first... All data stays local.`) to reduce visual clutter.

### 2026-04-17 — Homepage hero visual refresh to match Reply or Die design
- Rebuilt the Home/import hero into a centered, dark-indigo layout with restrained glow and stronger visual hierarchy.
- Updated the hero to include the two translucent score cards (👻 YOU RIGHT NOW 5 and 🏆 YOUR GOAL 95) with an overlapping center arrow.
- Kept existing onboarding actions but remapped the hero controls to the intended labels:
  - **See Inbox with Demo Data** → loads bundled/saved demo data
  - **Upload Export File** → opens JSON picker
  - **Set up One-Click Refresh** → connects export file when needed, or runs refresh when already connected
- Preserved existing local-first behavior and source panel/status/error wiring; this change is visual/entry-flow polish only.
### 2026-04-17 — Action-needed count copy now uses people-focused wording
- Updated the Action needed header count text from `N texts` to `N people waiting for your response` (with singular `1 person` handling).
- This is a copy-only UI change; action-list logic and counts are unchanged.

### 2026-04-15 — AI prompt grounded with concrete reply style examples
- Updated the AI reply prompt with explicit input→reply examples to anchor tone and style to concrete outputs.
- Replaced the prior long rule list with a tighter constraint set: normal text-message voice, direct response to latest messages, avoid polished/formal phrasing, no em dashes, and witty/funny tone.
- Kept UX and product behavior unchanged (same API route, allowlist gating, button visibility behavior, failure handling, regenerate flow, and homepage behavior).
### 2026-04-15 — Homepage-first startup restored for bundled demo load
- Fixed startup behavior so first load stays on the Home/import screen instead of auto-opening the inbox when bundled demo data is available.
- Bundled demo JSON is still preloaded and time-shifted on first run, but it is now saved for explicit **Continue with last export** use rather than immediately rendering the loaded app.
- Preserved normal in-app navigation and file import flows after the user intentionally enters the inbox.

### 2026-04-15 — Prompt/validation tweak for em-dash avoidance
- Updated AI reply prompt guidance to explicitly favor short, natural, normal text-message phrasing and avoid em dashes.
- Added client-side validation rejection when model output contains an em dash (`—`).
- Audited regenerate path for allowlisted demo threads (including Kendall Roy): regenerate still calls the same async generation function and is not gated by prior-attempt state.

### 2026-04-15 — AI demo trigger fixes for Michael/Fleabag + repeat clicks
- Added `iMessage;-;+12125550102` (Michael Scott) and `iMessage;-;+12125550108` (Fleabag) to the AI demo allowlist.
- Removed the no-op guard that blocked repeated clicks on the main **AI Suggested Reply** trigger after a prior generation attempt.

### 2026-04-15 — AI trigger visibility is now allowlist-only and always shown
- Ensured **AI Suggested Reply** trigger is always rendered for every allowlisted demo thread, independent of inbound/outbound or message-type conditions.
- Moved/duplicated AI trigger rendering into stable thread detail action areas so allowlisted threads in both **Action needed** and **Other texts** show the button consistently.
- Kept generate-time constraints unchanged; blocked threads still show the existing blocked-state card after click.

### 2026-04-15 — AI Suggested Reply trigger always visible on allowlisted demo threads
- Updated AI button visibility so allowlisted seeded demo threads always show the **AI Suggested Reply** trigger, even when latest message is outbound.
- Kept generation constraints unchanged; generation still requires an inbound plain-text latest message.
- Added a small AI state card when generation is not currently possible: **Can't generate a reply for this message** plus **Need an incoming text to reply to**.

### 2026-04-15 — AI Suggested Reply endpoint switched to Vercel API route
- Replaced frontend AI call target from localhost runner to same-origin `POST /api/ai-suggest-reply`.
- Added a Vercel-compatible server endpoint at `api/ai-suggest-reply.js` that calls OpenAI using server env var `OPENAI_API_KEY`.
- Removed localhost-runner AI proxy endpoint usage so AI generation no longer depends on `http://127.0.0.1:8765` in deployed environments.

### 2026-04-15 — Demo-only AI Suggested Reply now uses server-side model calls
- Replaced the visible **Generate reply** demo action with **AI Suggested Reply** for an explicit allowlist of seeded demo thread IDs only.
- Added explicit v1 gating: AI UI renders only when an allowlisted seeded thread’s latest visible plain-text message is inbound.
- Updated interaction flow to user-triggered generation only (no auto-generate on open), with **Generating...** loading, **Use**, and **Regenerate** actions.
- Added a centralized AI pipeline in the web app for allowlist checks, prompt/context construction (last ~6 text messages), output validation, and suppression of invalid outputs.
- Switched AI calls to server-side via the local runner (`POST /ai-suggest-reply`) so API keys are no longer read from browser config/localStorage.
- Added a new runner endpoint that forwards prompt requests to OpenAI using `OPENAI_API_KEY` from the runner environment.

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
