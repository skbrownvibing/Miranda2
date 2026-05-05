# Dummy data spec — inbox bucket population

This doc is the complete content reference for the demo inbox. Every contact,
every thread, every message, every suggested AI reply is listed below. The
intent is that any future implementation pass — wiring `docs/standalone.html`,
backfilling `data/miranda_demo.json`, or building a fresh data layer — can use
this as canonical source.

The buckets, in the order they appear in the rail:

- **Triage**
  - Waiting on you (existing) — 9 entries, unchanged
  - Critical (>3d) — derived filter
  - Today only — derived filter
  - Group chats — **8 new**
- **Archive**
  - Replied this week — **14** (6 existing + 8 new)
  - Dismissed — **6 new** (replaces the static "2")
  - Auto-filtered — **24** representative entries (12 delivery + 8 spam + 4 codes)

Style rules (apply to every new entry):

- Voice: dry, terse, character-true. Match Larry David / Michael Scott / Carrie
  Bradshaw cadence already in `CONTACTS`.
- "Me" replies are short — usually one to four words.
- Threads have 1–7 messages. Groups skew longer because multiple senders.
- Apostrophes use straight quotes (`'`) for parser sanity, not curly (`’`).
- `waitH` is hours since last inbound. For replied threads it tracks how long
  ago the last reply was sent (used for "Sent Xh ago" labels).

---

## 1. Group chats (8 entries)

Schema additions for groups vs. 1:1 contacts:

- `isGroup: true`
- Each inbound message has a `sender` field (e.g. `sender: 'Phoebe'`)
- `name` is the **group name**, not a person
- The most recent sender appears alongside the group name in the inbox row
  (rendering hint, not a data field)

### G1 · Sunday Roast Crew

- **Last sender:** Phoebe
- **Last text:** "Thank you, the only person at this table with taste."
- **waitH:** 4
- **AI suggested reply:** "next round on me"

| # | Sender | From me? | Text | Ago |
|---|---|---|---|---|
| 1 | Phoebe | no  | Smelly Cat is officially the brunch playlist now. | 4h |
| 2 | Joey   | no  | Phoebs you cannot keep doing this to us at 9am. | 4h |
| 3 | Phoebe | no  | It builds character. And appetite. | 4h |
| 4 | Joey   | no  | It builds nausea. | 4h |
| 5 | —      | yes | I'll allow it. | 3h |
| 6 | Phoebe | no  | Thank you, the only person at this table with taste. | 3h |

### G2 · The Bad Idea Bears

- **Last sender:** Barney
- **Last text:** "This is the best chat I am in."
- **waitH:** 2
- **AI suggested reply:** "beach suits is a billion dollar idea"

| # | Sender | From me? | Text | Ago |
|---|---|---|---|---|
| 1 | Barney | no  | What if — hear me out — we wear suits. To the beach. | 3h |
| 2 | Robin  | no  | Absolutely not. | 3h |
| 3 | Barney | no  | Robin. Robin. Beach suits. | 3h |
| 4 | Ted    | no  | I'd actually consider it. | 3h |
| 5 | Robin  | no  | Of course you would. | 2h |
| 6 | —      | yes | Suit up. | 2h |
| 7 | Barney | no  | This is the best chat I am in. | 2h |

### G3 · Closer Energy ⚓️

- **Last sender:** Roger
- **Last text:** "Best wrong group I've been in this year."
- **waitH:** 6
- **AI suggested reply:** "leaving you to it"

| # | Sender | From me? | Text | Ago |
|---|---|---|---|---|
| 1 | Don    | no  | We don't sell coffee. We sell mornings. | 7h |
| 2 | Peggy  | no  | Don. We literally sell coffee. | 7h |
| 3 | Roger  | no  | I'd buy a morning. Two if they came with bourbon. | 6h |
| 4 | Don    | no  | See. | 6h |
| 5 | —      | yes | Wrong group. | 6h |
| 6 | Roger  | no  | Best wrong group I've been in this year. | 6h |

### G4 · WFH Survivors

- **Last sender:** Stanley
- **Last text:** "I am not on this chat."
- **waitH:** 8
- **AI suggested reply:** "we see you stanley"

| # | Sender | From me? | Text | Ago |
|---|---|---|---|---|
| 1 | Pam     | no  | Anyone else hiding from a 'quick sync'? | 9h |
| 2 | Jim     | no  | Hiding is the sync. | 9h |
| 3 | Pam     | no  | Stanley you better not be on mute. | 9h |
| 4 | —       | yes | Solidarity. | 8h |
| 5 | Stanley | no  | I am not on this chat. | 8h |

### G5 · Wedding Logistics 9000

- **Last sender:** Charlotte
- **Last text:** "I love a willing soldier. Spreadsheet incoming."
- **waitH:** 1
- **AI suggested reply:** "send spreadsheet"

| # | Sender | From me? | Text | Ago |
|---|---|---|---|---|
| 1 | Charlotte | no  | We need a backup officiant. And a backup backup. | 2h |
| 2 | Carrie    | no  | Why does this feel like a hostage negotiation. | 2h |
| 3 | Miranda   | no  | Because it is one. With centerpieces. | 2h |
| 4 | —         | yes | On it. | 1h |
| 5 | Charlotte | no  | I love a willing soldier. Spreadsheet incoming. | 1h |

### G6 · The Group Chat That Refuses To Die

- **Last sender:** Phoebe
- **Last text:** "Thank you. Mute the paleontologist."
- **waitH:** 11
- **AI suggested reply:** "muting ross"

| # | Sender | From me? | Text | Ago |
|---|---|---|---|---|
| 1 | Ross     | no  | Story time: how I met your dinosaurs. | 12h |
| 2 | Chandler | no  | Could you BE more historical. | 12h |
| 3 | Ross     | no  | It's RELEVANT. | 11h |
| 4 | —        | yes | It is never relevant. | 11h |
| 5 | Phoebe   | no  | Thank you. Mute the paleontologist. | 11h |

### G7 · Bachelorette Recon

- **Last sender:** Samantha
- **Last text:** "Bring the skepticism, leave the cardigan."
- **waitH:** 1
- **AI suggested reply:** "cardigan staying home"

| # | Sender | From me? | Text | Ago |
|---|---|---|---|---|
| 1 | Samantha  | no  | Vegas penthouse confirmed. Mood: feral but classy. | 2h |
| 2 | Carrie    | no  | Define classy. | 2h |
| 3 | Charlotte | no  | Heels and fuzzy slippers, I assume. | 1h |
| 4 | Miranda   | no  | I'm bringing snacks and skepticism. | 1h |
| 5 | —         | yes | Both required. | 1h |
| 6 | Samantha  | no  | Bring the skepticism, leave the cardigan. | 1h |

### G8 · Fantasy League: Layoff Survivors

- **Last sender:** Liz
- **Last text:** "It's been cooked since week two."
- **waitH:** 4
- **AI suggested reply:** "commissioner Lemon needs help"

| # | Sender | From me? | Text | Ago |
|---|---|---|---|---|
| 1 | Liz   | no  | I traded my best player for a bag of chips and dignity. | 5h |
| 2 | Jack  | no  | You should have called me first, Lemon. | 5h |
| 3 | Tracy | no  | I drafted myself. Twice. | 5h |
| 4 | —     | yes | This league is cooked. | 4h |
| 5 | Liz   | no  | It's been cooked since week two. | 4h |

---

## 2. Replied this week (14 entries)

These are 1:1 conversations where the user **sent the last message**. They go
into the Archive group. No AI suggested reply needed (the thread is already
"closed" from the user's side).

The first 6 are existing threads from `data/miranda_demo.json` and
`docs/standalone.html`'s data — kept verbatim. The next 8 are net new.

### Existing (6)

#### R1 · Rachel Green · +12125550111

- **Last text (from me):** "Always."
- **waitH:** 5

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | I bought boots I absolutely did not need. | 5h |
| 2 | yes | Respect. | 5h |
| 3 | no  | Thank you for supporting me in my journey. | 5h |
| 4 | yes | Always. | 5h |

#### R2 · Blair Waldorf · +12125550112

- **Last text (from me):** "Do we need to dress up?"
- **waitH:** 3

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | Brunch at one. Be on time, or at least be impressive. | 4h |
| 2 | yes | I can do one. | 3h |
| 3 | no  | Good. | 3h |
| 4 | yes | Do we need to dress up? | 3h |

#### R3 · Jess Day · +12125550113

- **Last text (from me):** "Honestly yes."
- **waitH:** 10

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | Important: do adults need a glue gun in their home at all times? | 10h |
| 2 | yes | Honestly yes. | 10h |

#### R4 · Joey Tribbiani · +12125550114

- **Last text (from me):** "How many sandwiches are we talking?"
- **waitH:** 13

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | You wanna get sandwiches? | 13h |
| 2 | yes | Yes. | 13h |
| 3 | no  | Nice. | 13h |
| 4 | yes | How many sandwiches are we talking? | 13h |

#### R5 · Elaine Benes · +12125550115

- **Last text (from me):** "Also I support the anti-dancing stance."
- **waitH:** 11

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | Do not let me go back to that office party. | 12h |
| 2 | yes | I won't. | 12h |
| 3 | no  | Thank you. | 12h |
| 4 | yes | Also I support the anti-dancing stance. | 11h |

#### R6 · Miranda Priestly · +12125550116

- **Last text (from me):** "Understood."
- **waitH:** 16

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | By all means move at a glacial pace. You know how that thrills me. | 17h |
| 2 | yes | Understood. | 16h |

### New (8)

#### R7 · Rory Gilmore · +12125550117

- **Last text (from me):** "Honestly proud of you."
- **waitH:** 4

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | Read four books this weekend. Am I okay. | 5h |
| 2 | yes | Define okay. | 4h |
| 3 | no  | Touché. | 4h |
| 4 | yes | Honestly proud of you. | 4h |

#### R8 · Hannah Horvath · +12125550118

- **Last text (from me):** "I see you."
- **waitH:** 24

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | I think I'm having a Feeling about a cheese plate. | 1d |
| 2 | yes | Validating. | 1d |
| 3 | no  | Thank you for seeing me. | 1d |
| 4 | yes | I see you. | 1d |

#### R9 · Andy Dwyer · +12125550119

- **Last text (from me):** "Banger title."
- **waitH:** 30

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | I named my new song 'The Pit, Revisited.' Thoughts. | 1d |
| 2 | yes | Banger title. | 1d |

#### R10 · Mindy Lahiri · +12125550120

- **Last text (from me):** "Bangs first."
- **waitH:** 50

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | Should I get bangs or a divorce. | 2d |
| 2 | yes | Bangs first. | 2d |

#### R11 · Olivia Pope · +12125550121

- **Last text (from me):** "It always is."
- **waitH:** 80

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | It's handled. | 3d |
| 2 | yes | It always is. | 3d |

#### R12 · Ron Swanson · +12125550122

- **Last text (from me):** "Sending now."
- **waitH:** 100

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | I require a recommendation for a reliable belt. Leather. American. No nonsense. | 4d |
| 2 | yes | Sending now. | 4d |

#### R13 · Pam Beesly · +12125550123

- **Last text (from me):** "Worth it."
- **waitH:** 130

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | Update from accounting: I drew a cat on the toner request. | 5d |
| 2 | yes | Iconic. | 5d |
| 3 | no  | Kevin laughed. Toby filed a complaint. | 5d |
| 4 | yes | Worth it. | 5d |

#### R14 · Nick Miller · +12125550124

- **Last text (from me):** "Send pics."
- **waitH:** 150

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | I bought a fish. The fish has opinions. | 6d |
| 2 | yes | What kind of opinions. | 6d |
| 3 | no  | Loud ones. | 6d |
| 4 | yes | Send pics. | 6d |

---

## 3. Dismissed (6 entries)

The user has actively waved these away — the cards land here on first load.
Each is a single inbound message; the user has not replied and intentionally
won't. (When a *new* inbound arrives on a dismissed thread, it should re-pop
back into Triage per the existing dismissal logic.)

#### D1 · Gretchen Wieners

- **waitH:** 24
- **Last text:** "So like, are we doing a group costume or are we doing chaos again. Last year was chaos and Karen still hasn't apologized."

#### D2 · Schmidt

- **waitH:** 48
- **Last text:** "Quick favor: rate this cologne in one word. Be honest. Be kind. Be specific. Three nouns max. I'm not above bribery."

#### D3 · Dwight Schrute

- **waitH:** 72
- **Last text:** "Reminder: we have not yet scheduled the quarterly beet inventory. This is unacceptable. Confirm availability Tuesday 0600."

#### D4 · Niles Crane

- **waitH:** 96
- **Last text:** "I find myself in possession of two opera tickets and an unwillingness to attend alone. I'm not above pity company."

#### D5 · Phil Dunphy

- **waitH:** 120
- **Last text:** "Trampoline arrived. Claire said no. I said yes. Need a tiebreaker. You're it. No pressure but kind of a lot of pressure."

#### D6 · Hank Moody

- **waitH:** 144
- **Last text:** "You up? (For a thoughtful, mutually beneficial exchange of ideas. Not a booty call. Unless.)"

---

## 4. Auto-filtered (24 entries)

These are the texts the app correctly suppresses — delivery notifications,
political fundraising, dental reminders, 2FA codes, etc. Cards live here only
so the user can audit what got filtered. No AI reply.

Sender names are **the brand or short code**, not a contact name. There's no
phone field — these arrive from short codes or random long numbers.

### Delivery / orders (12)

#### F1 · DoorDash · waitH 2

"Your DoorDash order from Joe's Pizza is 4 minutes away. Your Dasher's name is also Joe. Coincidence?"

#### F2 · Uber Eats · waitH 9

"Uber Eats: your order from Sweetgreen has arrived. The kale is judging you."

#### F3 · Grubhub · waitH 27

"Grubhub: your order from Bagel Pub is being prepared. ETA 22 min, give or take a bagel."

#### F4 · Instacart · waitH 34

"Instacart: your shopper is at Trader Joe's. They cannot find the chili crisp. Suggest substitution?"

#### F5 · Amazon · waitH 50

"Your Amazon package was delivered. Hidden behind a planter, like a treat."

#### F6 · USPS · waitH 60

"USPS Tracking: your package is now 'In Transit, Arriving Late' which is also a state of mind."

#### F7 · FedEx · waitH 75

"FedEx: signature required tomorrow between 8am and the heat death of the universe."

#### F8 · UPS · waitH 90

"UPS Choice: your driver is 4 stops away and looking aggressive."

#### F9 · Caviar · waitH 100

"Caviar: your order from Lucali has been picked up. ETA 38 min, vibes intact."

#### F10 · Lyft · waitH 110

"Lyft: your driver Kyle is here. Kyle would like to discuss the sound system."

#### F11 · Resy · waitH 120

"Resy: your reservation at Don Angie tomorrow at 7:30. The pinwheel awaits."

#### F12 · Delta · waitH 130

"Delta: your flight DL422 is now boarding at gate B17. Group 8, as always."

### Spam (8) — fake-politician fundraising + sundries

#### F13 · Spencer Pratt for Senate · waitH 4

"URGENT: Spencer Pratt for Senate needs $3 by midnight. The crystals are telling him it's close. Reply YES to donate."

#### F14 · Bryan Johnson 2028 · waitH 12

"Bryan Johnson 2028: vote for the man who has not aged since 2019. Reply YES to donate $7 and 12 minutes of your circadian rhythm."

#### F15 · MR BEAST 2028 · waitH 28

"MR BEAST FOR GOVERNOR: help us give away one (1) state to a deserving subscriber. Reply YES to enter."

#### F16 · Logan Paul 2028 · waitH 36

"Logan Paul 2028 — A Vote For Logan Is A Vote For Maverick. Reply STOP to end texts (you can't)."

#### F17 · Gary Vee for Comptroller · waitH 50

"Gary Vee for Comptroller. Hustle. Vote. Hustle. Vote. Reply YES to hustle."

#### F18 · Joe Rogan Independent · waitH 70

"Joe Rogan Independent 2028: it's gonna be a thing, man. Reply YES to support open dialogue."

#### F19 · Jen at Randstad · waitH 80

"Hi Sarah, this is Jen from Randstad. I'd love to chat about your career goals over a quick 15-min call."

#### F20 · Family Smiles Dental · waitH 100

"Family Smiles Dental: it's time for your check-up & cleaning. Reply YES to book."

### Verification codes / 2FA (4)

#### F21 · Google · waitH 5

"Your Google verification code is 884201. Do not share."

#### F22 · Discord · waitH 18

"Your Discord login code is 339712. If this wasn't you, ignore this."

#### F23 · Chase · waitH 40

"Your Chase verification code is 884201. Do not share. Do not screenshot. Do not even think about it."

#### F24 · Slack · waitH 60

"Your Slack one-time password is 412909. Expires in 5 minutes, like joy."

---

## Counts summary

| Bucket | Before | After |
|---|---:|---:|
| Waiting on you | 9 | 9 |
| Critical (>3d) | 3 | 3 |
| Today only | 4 | 4 |
| Group chats | 1 | 8 |
| Replied this week | 14 | 14 |
| Dismissed | 2 | 6 |
| Auto-filtered | 70 | 24 |

Note on **Auto-filtered**: original static label said 70. The actual underlying
data here is 24 representative entries. If a true 70 is desired, that count can
be reached programmatically (template fan-out) or by hand-authoring more entries
following the same three sub-categories.

---

## Implementation notes (for whoever wires this up next)

The current iframe (`docs/standalone.html`) ships a single `CONTACTS` JS array.
None of the buckets in this doc except "Waiting on you" are wired to a data
source — Group chats / Replied / Dismissed / Auto-filtered are static labels.

To make the rail buckets render this data, the iframe needs:

1. New JS arrays alongside `CONTACTS`: `GROUPS`, `REPLIED`, `DISMISSED`,
   `FILTERED`.
2. `data-filter` attributes on the Archive section's three rail-chip buttons
   (currently they have no filter wiring).
3. `id` attributes on the count `<span>`s so they can be updated dynamically.
4. `filteredContacts()` extended to switch on the new filter values.
5. `renderMsgList()` updated to refresh all rail count badges.
6. Bubble render extended to show a sender label above the first bubble of
   each new sender's run, when `m.sender` is present (groups only).

The existing `data/miranda_demo.json` already has most of this content from a
previous pass, so it can be the source of truth if/when we wire the iframe to
read from JSON via parent `postMessage`. Until then this doc is the canonical
content reference.
