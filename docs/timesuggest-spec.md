# TimeSuggest spec

A small, single-page tool that reads your Google Calendar and produces a
copy-pasteable list of free meeting slots in a specific email-friendly format.

Lives at `timesuggest.html` at the repo root, alongside `index.html`. Not wired
into Reply or Die — separate tool, same repo.

## Why this exists

Suggesting times in an email is repetitive: open calendar, eyeball gaps, type
them out, get the timezone abbreviation right, do it again next email.
TimeSuggest reads your real calendar, computes the gaps, and formats them.

## What it is not

- Not an email client plugin (no Gmail add-on, no Mail.app bundle).
- Not a scheduling page (no link for the recipient to click).
- Not a calendar-blocking tool (does not create hold events).

The simpler-than-a-plugin approach: open a page, click **Copy**, paste into any
email anywhere.

## Output format

```
Tuesday 3/3: 10am-12pm and 2-7pm PT
Wednesday 3/4: 9:30am-3pm PT
Thursday 3/5: 10am-12pm, 2pm-5pm PT
Friday 3/6: 10am-12pm PT
```

Rules:

- `Weekday M/D:` prefix. Full day name. No leading zeros on month/day.
- Lowercase `am` / `pm`.
- Drop minutes when on the hour (`10am`, not `10:00am`).
- Drop am/pm on the start of a range when both halves share it (`2-7pm`, not
  `2pm-7pm`). Keep both when the range crosses noon (`10am-12pm`).
- Join 2 ranges per day with ` and `; 3+ ranges with `, ` (no oxford).
- Timezone label appended once per line, configurable string (defaults to
  short form like `PT`, `ET`).
- Days with zero qualifying free slots are omitted entirely.

## Settings (persisted in localStorage)

| Setting | Default | Notes |
| --- | --- | --- |
| Google OAuth Client ID | (empty) | User-supplied, one-time |
| Timezone (IANA) | browser TZ | Dropdown of common + free-text |
| Timezone label | inferred (PT/ET/…) | Editable string used in output |
| Look-ahead days | 7 | 1–30 |
| Working hours | 9am–7pm | Per-day window |
| Extended hours | 7am–10pm | Toggle to swap working hours for the wider window |
| Minimum slot | 30 min | 15 / 30 / 45 / 60 / 90 |
| Weekdays only | on | Mon–Fri |
| Range separator style | "and" for 2 / commas for 3+ | Or "all commas" |
| Calendars to include | `primary` | After sign-in, list other calendars with checkboxes |

## Auth

Google Identity Services (GIS), in-browser OAuth.

- Scope: `https://www.googleapis.com/auth/calendar.readonly`.
- Token lives in browser memory only. Not persisted to localStorage.
- Nothing is sent to any server other than `googleapis.com`.
- User supplies their own OAuth Client ID (5-minute Google Cloud setup; the
  page links to instructions).

## Data flow

1. Sign in with Google → access token in memory.
2. `GET /calendar/v3/users/me/calendarList` once → populate calendar
   checkboxes.
3. `POST /calendar/v3/freeBusy` for `[now, now + N days]` with the selected
   calendar IDs and the user's timezone.
4. Walk each day in the user's TZ, take the working-hours window, subtract
   busy intervals that overlap, drop free gaps shorter than the min slot.
5. Format and render a live preview + **Copy to clipboard** button.

## Timezone handling

All slicing into days uses the selected IANA timezone (not the browser's
local time), so DST and travel work correctly. Implemented with
`Intl.DateTimeFormat` + a small "zoned local time → UTC" helper using
`formatToParts` to recover the offset at any instant. No timezone library.

## Privacy

- No server. The page talks directly to Google.
- Token is in-memory; gone when you close the tab.
- No analytics. No third-party scripts other than Google's GIS loader.

## Out of scope (for now)

- Creating tentative hold events on the calendar.
- Multiple-attendee free/busy (i.e. finding mutual free times).
- Recurring template emails / per-recipient defaults.
- Detecting buffer-around-existing-events (e.g. always 15 min after a meeting).

Each of these is easy to bolt on later without changing the data flow.
