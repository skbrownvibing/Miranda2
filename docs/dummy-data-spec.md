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
  - Group chats — **4 entries**
- **Archive**
  - Replied this week — **14 entries** (8 existing + 6 new)
  - Dismissed — **2 entries**
  - Auto-filtered — **70 entries** (35 delivery + 25 spam + 10 codes)

Style rules (apply to every new entry):

- Voice: dry, terse, character-true. Match Larry David / Michael Scott / Carrie
  Bradshaw cadence already in `CONTACTS`.
- "Me" replies are short — usually one to four words.
- Threads have 1–7 messages. Groups skew longer because multiple senders.
- Apostrophes use straight quotes (`'`) for parser sanity, not curly.
- `waitH` is hours since last inbound. For replied threads it tracks how long
  ago the last reply was sent (used for "Sent Xh ago" labels).
- Spam senders may misaddress the user (e.g. "Hi Sarah") on purpose — that is
  the joke and the realism.

---

## 1. Group chats (4 entries)

Schema additions for groups vs. 1:1 contacts:

- `isGroup: true`
- Each inbound message has a `sender` field (e.g. `sender: 'Phoebe'`)
- `name` is the **group name**, not a person
- The most recent sender appears alongside the group name in the inbox row
  (rendering hint, not a data field)

### G1 · Sunday Roast Crew

- **Last sender:** Phoebe
- **Last text:** "Thank you, the only person at this table with taste."
- **waitH:** 3
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

### G3 · WFH Survivors

- **Last sender:** Stanley
- **Last text:** "I am not on this chat."
- **waitH:** 8
- **AI suggested reply:** "we see you stanley"

| # | Sender  | From me? | Text | Ago |
|---|---|---|---|---|
| 1 | Pam     | no  | Anyone else hiding from a 'quick sync'? | 9h |
| 2 | Jim     | no  | Hiding is the sync. | 9h |
| 3 | Pam     | no  | Stanley you better not be on mute. | 9h |
| 4 | —       | yes | Solidarity. | 8h |
| 5 | Stanley | no  | I am not on this chat. | 8h |

### G4 · Bachelorette Recon

- **Last sender:** Samantha
- **Last text:** "Bring the skepticism, leave the cardigan."
- **waitH:** 1
- **AI suggested reply:** "cardigan staying home"

| # | Sender    | From me? | Text | Ago |
|---|---|---|---|---|
| 1 | Samantha  | no  | Vegas penthouse confirmed. Mood: feral but classy. | 2h |
| 2 | Carrie    | no  | Define classy. | 2h |
| 3 | Charlotte | no  | Heels and fuzzy slippers, I assume. | 1h |
| 4 | Miranda   | no  | I'm bringing snacks and skepticism. | 1h |
| 5 | —         | yes | Both required. | 1h |
| 6 | Samantha  | no  | Bring the skepticism, leave the cardigan. | 1h |

---

## 2. Replied this week (14 entries)

These are 1:1 conversations where the user **sent the last message**. They go
into the Archive group. No AI suggested reply needed — the thread is "closed"
from the user's side.

R1–R8 are existing threads from `data/miranda_demo.json` (those flagged
`i_replied_last: true`) — content kept verbatim where it already exists, and
short net-new content for Regina George and Lorelai Gilmore (who exist in the
JSON but had no canonical text). R9–R14 are net new contacts.

### Existing (8)

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

#### R5 · Regina George · +12125550115

- **Last text (from me):** "We persist."
- **waitH:** 7

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | Are we still doing pink Wednesdays or has the whole school given up. | 8h |
| 2 | yes | Still on. | 7h |
| 3 | no  | Good. I expected better from this institution. | 7h |
| 4 | yes | We persist. | 7h |

#### R6 · Lorelai Gilmore · +12125550116

- **Last text (from me):** "Drink up."
- **waitH:** 9

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | Is it weird if I order coffee from three places at once. | 10h |
| 2 | yes | Define weird. | 9h |
| 3 | no  | That's why we're friends. | 9h |
| 4 | yes | Drink up. | 9h |

#### R7 · Elaine Benes · +12125550117

- **Last text (from me):** "Also I support the anti-dancing stance."
- **waitH:** 11

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | Do not let me go back to that office party. | 12h |
| 2 | yes | I won't. | 12h |
| 3 | no  | Thank you. | 12h |
| 4 | yes | Also I support the anti-dancing stance. | 11h |

#### R8 · Miranda Priestly · +12125550118

- **Last text (from me):** "Understood."
- **waitH:** 16

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | By all means move at a glacial pace. You know how that thrills me. | 17h |
| 2 | yes | Understood. | 16h |

### New (6)

#### R9 · Rory Gilmore · +12125550119

- **Last text (from me):** "Honestly proud of you."
- **waitH:** 4

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | Read four books this weekend. Am I okay. | 5h |
| 2 | yes | Define okay. | 4h |
| 3 | no  | Touché. | 4h |
| 4 | yes | Honestly proud of you. | 4h |

#### R10 · Hannah Horvath · +12125550120

- **Last text (from me):** "I see you."
- **waitH:** 24

| # | From me? | Text | Ago |
|---|---|---|---|
| 1 | no  | I think I'm having a Feeling about a cheese plate. | 1d |
| 2 | yes | Validating. | 1d |
| 3 | no  | Thank you for seeing me. | 1d |
| 4 | yes | I see you. | 1d |

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

## 3. Dismissed (2 entries)

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

---

## 4. Auto-filtered (70 entries)

These are the texts the app correctly suppresses — delivery notifications,
political fundraising, dental reminders, 2FA codes, etc. Cards live here only
so the user can audit what got filtered. No AI reply.

Sender names are **the brand or short code**, not a contact name. There's no
phone field — these arrive from short codes or random long numbers.

### Delivery / orders / confirmations (35)

| # | Sender | waitH | Text |
|---|---|---:|---|
| F1  | DoorDash      | 2  | Your DoorDash order from Joe's Pizza is 4 minutes away. Your Dasher's name is also Joe. Coincidence? |
| F2  | Uber Eats     | 3  | Uber Eats: your order from Sweetgreen has arrived. The kale is judging you. |
| F3  | Grubhub       | 5  | Grubhub: your order from Bagel Pub is being prepared. ETA 22 min, give or take a bagel. |
| F4  | Instacart     | 6  | Instacart: your shopper is at Trader Joe's. They cannot find the chili crisp. Suggest substitution? |
| F5  | Postmates     | 8  | Postmates: your order from Levain Bakery is on the way. Cookies still warm. Probably. |
| F6  | Seamless      | 10 | Seamless: order from Joe's Shanghai out for delivery. The soup dumplings will not survive transit. |
| F7  | Caviar        | 12 | Caviar: your order from Lucali has been picked up. ETA 38 min, vibes intact. |
| F8  | Sweetgreen    | 14 | Sweetgreen: your order is ready for pickup. The kale is resting. |
| F9  | Drizly        | 16 | Drizly: your order from Astor Wines is on the way. ETA 22 min. |
| F10 | Gopuff        | 18 | Gopuff: your 2am order will arrive in 18 minutes. No judgment. |
| F11 | Whole Foods   | 20 | Whole Foods: order ready for pickup at Bowery. Parking is a war. |
| F12 | Wegmans       | 22 | Wegmans: curbside pickup ready at slot 7. Pop the trunk. |
| F13 | Amazon        | 24 | Your Amazon package was delivered. Hidden behind a planter, like a treat. |
| F14 | USPS          | 26 | USPS Tracking: your package is now 'In Transit, Arriving Late' which is also a state of mind. |
| F15 | FedEx         | 28 | FedEx: signature required tomorrow between 8am and the heat death of the universe. |
| F16 | UPS           | 30 | UPS Choice: your driver is 4 stops away and looking aggressive. |
| F17 | DHL           | 32 | DHL: your package has cleared customs. Vibes uncertain. |
| F18 | Lyft          | 34 | Lyft: your driver Kyle is here. Kyle would like to discuss the sound system. |
| F19 | Uber          | 36 | Uber: Marcus is arriving in a Prius. 3 stars, personality. |
| F20 | Resy          | 38 | Resy: your reservation at Don Angie tomorrow at 7:30. The pinwheel awaits. |
| F21 | OpenTable     | 40 | OpenTable: Carbone confirmed Saturday 9pm. Do not be late. The spicy rigatoni doesn't wait. |
| F22 | Tock          | 42 | Tock: Atomix tasting menu Thursday confirmed. Mortgage adjusted. |
| F23 | Yelp          | 44 | Yelp Reservations: your booking at Via Carota is held. Don't bail. |
| F24 | Delta         | 46 | Delta: flight DL422 is now boarding at gate B17. Group 8, as always. |
| F25 | United        | 48 | United: flight UA2241 boarding zone 4, also known as last. |
| F26 | JetBlue       | 50 | JetBlue: flight B61407 delayed 40 min. Blame Newark. |
| F27 | Amtrak        | 52 | Amtrak: train 2156 to Boston now boarding track 9. |
| F28 | Apple Pay     | 54 | Apple Pay: $42 to Joe's Pizza. You tipped 11%. Brave. |
| F29 | Venmo         | 56 | Venmo: Charlotte paid you $38 for "girls' night (allegedly)". |
| F30 | Zelle         | 58 | Zelle: $200 incoming from Mom. Memo: groceries. |
| F31 | Cash App      | 60 | Cash App: $15 sent to $Schmidt$. Memo: cologne tax. |
| F32 | Walgreens     | 62 | Walgreens: Rx ready for pickup. Store closes at 10. |
| F33 | CVS Pharmacy  | 64 | CVS: refill ready for pickup. Photos still printing. Forever. |
| F34 | iCloud        | 66 | iCloud: storage 99% full. As planned. |
| F35 | Peloton       | 68 | Peloton: Cody class booked 7am. May god help you. |

### Spam (25) — fake-politician fundraising + sundries

| # | Sender | waitH | Text |
|---|---|---:|---|
| F36 | Spencer Pratt for Senate     | 4   | URGENT: Spencer Pratt for Senate needs $3 by midnight. The crystals are telling him it's close. Reply YES to donate. |
| F37 | Bryan Johnson 2028           | 12  | Bryan Johnson 2028: vote for the man who has not aged since 2019. Reply YES to donate $7 and 12 minutes of your circadian rhythm. |
| F38 | MR BEAST 2028                | 28  | MR BEAST FOR GOVERNOR: help us give away one (1) state to a deserving subscriber. Reply YES to enter. |
| F39 | Logan Paul 2028              | 36  | Logan Paul 2028 — A Vote For Logan Is A Vote For Maverick. Reply STOP to end texts (you can't). |
| F40 | Jake Paul 2028               | 42  | Jake Paul 2028: Maverick is a movement. Reply STOP, doesn't work. |
| F41 | Gary Vee for Comptroller     | 50  | Gary Vee for Comptroller. Hustle. Vote. Hustle. Vote. Reply YES to hustle. |
| F42 | Joe Rogan Independent        | 70  | Joe Rogan Independent 2028: it's gonna be a thing, man. Reply YES to support open dialogue. |
| F43 | Pete Davidson 2028           | 76  | Pete Davidson 2028 endorses naps. Reply YES to nap with Pete. Platform is forthcoming. |
| F44 | Martha Stewart for Mayor     | 84  | Martha Stewart for Mayor: I will personally regrout your sidewalk. Reply YES to donate $25. |
| F45 | Chrissy Teigen for Council   | 92  | Chrissy Teigen for City Council: bringing pasta water to the people. Reply YES to chip in $15. |
| F46 | Snoop Dogg for Lt. Gov.      | 100 | Snoop Dogg for Lt. Governor: reply YES if u know what I'm sayin. |
| F47 | Guy Fieri 2028               | 108 | Guy Fieri 2028: taking us all to Flavortown via the legislative branch. Reply YES for $5. |
| F48 | RuPaul for Governor          | 116 | RuPaul for Governor: sashay to the polls. Reply YES, condragulations on civic duty. |
| F49 | Dwayne Johnson 2028          | 124 | Dwayne Johnson 2028: finally a candidate who can carry the bill. Reply YES to donate. |
| F50 | Kim K for AG                 | 132 | Kim K for Attorney General: justice reform but make it iconic. Reply YES for $10. |
| F51 | Jen at Randstad              | 80  | Hi Sarah, this is Jen from Randstad. I'd love to chat about your career goals over a quick 15-min call. |
| F52 | Family Smiles Dental         | 100 | Family Smiles Dental: it's time for your check-up & cleaning. Reply YES to book. |
| F53 | CarShield                    | 110 | CarShield: extended warranty available on the vehicle you do not own. Final notice. |
| F54 | Indeed Recruiter             | 115 | Hi Sarah, found a perfect role for someone with your background. 5 min call? |
| F55 | Marriott Vacations           | 125 | Marriott Vacations: you are pre-approved for a tropical getaway. Reply YES to learn more. |
| F56 | IRS Final Notice             | 135 | IRS FINAL NOTICE: settlement required. Call 1-800-NOT-REAL today to avoid action. |
| F57 | Property Bros LLC            | 145 | We will buy your house, sight unseen, for cash. Reply YES, no obligation. (There is obligation.) |
| F58 | Kars4Kids                    | 155 | Donate your vehicle to Kars4Kids. The jingle is included free of charge. |
| F59 | Free Cruise Co.              | 165 | Congratulations! You've won a complimentary 4-night cruise. Conga line included. Claim by Friday. |
| F60 | AT&T Loyalty                 | 175 | AT&T: as a loyal customer you've been pre-selected for a device upgrade. Reply YES to redeem. |

### Verification codes / 2FA (10)

| # | Sender | waitH | Text |
|---|---|---:|---|
| F61 | Google     | 5  | Your Google verification code is 884201. Do not share. |
| F62 | Discord    | 18 | Your Discord login code is 339712. If this wasn't you, ignore this. |
| F63 | Chase      | 40 | Your Chase verification code is 502184. Do not share. Do not screenshot. Do not even think about it. |
| F64 | Slack      | 60 | Your Slack one-time password is 412909. Expires in 5 minutes, like joy. |
| F65 | Apple      | 14 | Your Apple ID code is 605137. Do not share with anyone, including Apple. |
| F66 | GitHub     | 22 | Your GitHub authentication code is 718022. Sign-in attempt from a new device. |
| F67 | Microsoft  | 35 | Microsoft account security code: 248391. If you didn't request this, change your password. |
| F68 | AmEx       | 48 | American Express verification code: 130475. Never share this code. |
| F69 | Robinhood  | 70 | Your Robinhood verification code is 902614. The market is closed but the codes are not. |
| F70 | Coinbase   | 90 | Coinbase verification: 461029. Use this code to confirm your sign-in. |

---

## Counts summary

| Bucket | Label (before) | Data (after) |
|---|---:|---:|
| Waiting on you | 9 | 9 |
| Critical (>3d) | 3 | 3 |
| Today only | 4 | 4 |
| Group chats | 1 | 4 |
| Replied this week | 14 | 14 |
| Dismissed | 2 | 2 |
| Auto-filtered | 70 | 70 |

"Label (before)" = the static rail-chip badge currently rendered in
`docs/standalone.html`. "Data (after)" = number of fully-authored entries in
this spec. The two columns now match — no reconciliation is needed when wiring
the iframe to read live data.

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

`data/miranda_demo.json` already contains the 8 existing replied threads
(R1–R8), 4 unrelated group chats (Pawnee Planning Committee, Burn Book
Editorial Board, Coffee Emergency, The Crows Have Texted), and a few
delivery/spam stubs. When porting this spec to JSON, decide whether to
**replace** the existing groups with G1–G4 here, or **keep both** sets — they
don't overlap by name. Everything else in this spec is additive: no JSON entry
is contradicted, only extended.
