# PRD: Local-First iMessage Responsiveness Tracker for Mac

## Overview
A local-first Mac app that helps users identify which personal text conversations are still waiting on a reply, measure responsiveness over time, and make the process motivating and easy to return to.

## Problem
iMessage does not help users track response debt. Personal conversations get buried under logistics, spam, group chats, and noise, causing missed replies and poor visibility into responsiveness.

## Target user
Mac users who text frequently, primarily use iMessage for personal communication, and want a lightweight way to see which direct conversations and small group conversations are waiting on them.

## Core value
The product shows which conversations are waiting on the user, measures reply behavior over time, helps reduce missed replies, and creates a simple, repeatable habit loop.

## Current product
Two components:
1. Local Mac export script → normalized JSON
2. Local web app → action list, score, history

No server, accounts, or cloud sync.

## Core behaviors
The app filters conversations using classification (spam, Automated, large group chats), identifies eligible personal conversations where the latest normalized event is from someone else, ranks eligible conversations into an action list, computes a responsiveness score, shows score history, and allows dismissing conversations.

## Decision rules

### Normalized event
A normalized event is the canonical unit of conversation history. All chronology, latest-event display, and previews are based on normalized events. Includes all real conversation activity after export normalization (messages, attachments, etc.), regardless of parseability.

### Eligible conversation shape
Eligible conversation shapes include direct 1:1 conversations and small group conversations with fewer than 5 participants. Larger group chats are excluded because they are noisier and less likely to represent direct response debt.

### Waiting on you
A conversation is waiting on the user when it has an eligible conversation shape, the latest normalized event was sent by someone else, it is not excluded, and it is not dismissed. Filtering may be used for scoring logic but must not override the latest event.

### Excluded conversations
Excluded from action list and scoring if it is a group chat with 5 or more participants, classified as spam, classified as Automated, or contains no normalized events outside spam/Automated classification. Exclusion does not affect chronological event data.

### Automated classification
Automated includes delivery updates, rideshare notifications, appointment flows, reservations, verification messages, and other transactional system messages. These are excluded even if they request replies. Human logistics messages are not excluded. Classification is heuristic and user-overridable.

### Unsaved numbers
Conversations with unsaved participants are included. By default, eligible unsaved 1:1 conversations appear in **Other**; if waiting on the user they move to the action list; if spam/Automated they are excluded; manual overrides take precedence. Unsaved numbers can count toward scoring if eligible.

### Dismissed conversations
Dismissed conversations are removed from the action list, do not count as unresolved, and reappear if a new incoming normalized event occurs.

### Manual overrides
User overrides take precedence until a new normalized event changes state.

## Canonical data rules
- Latest event is always the newest normalized event and never derived from filtered or preview subsets
- Display, response state, and scoring are independent; display must not influence logic
- Preview is display-only and never used for scoring or response state
- Exporter defines message meaning; frontend only renders
- Score, action list, and stats use the same eligibility set
- Waiting-on-you is always derived from normalized events

## Scoring model
The responsiveness score is a 0–100 value computed over the currently selected time window using the same eligible conversation set as the action list.

It combines three components:
- **Reply rate (40%)**: percentage of conversations you replied to when a reply was expected
- **Reply speed (30%)**: how quickly you reply on average
- **Open conversations penalty (30%)**: penalty for conversations currently waiting on you, with older ones weighted more heavily

The final score is the weighted combination of these components scaled to 0–100. It excludes spam, Automated, group chats with 5 or more participants, and dismissed conversations, and must not depend on preview or display logic.

## Score history
One score snapshot is stored per day.

## Anti-patterns to avoid
- deriving state from preview data
- redefining latest event from filtered subsets
- duplicating eligibility logic
- compensating for exporter issues in frontend
- using different datasets for display vs logic

## Success criteria
Users can quickly identify conversations waiting on them, the score matches perceived responsiveness, repeated use reduces missed replies, users return frequently, and setup is simple.

## Constraints
Mac only, export-based (no live sync), heuristic classification.

## Non-goals
Sending messages, building a messaging client, real-time sync, emotional interpretation of conversations.

## Edge cases
Multiple numbers per contact, reactions/attachments/non-standard events, missing contact names, mixed personal and automated threads, partial exports.

## Next priorities
- Suggested reply + Copy
- Easier refresh (no manual export)
- Pagination (10 threads at a time)
- Larger-group controls and group-specific reply UX
- Waiting on others
- Work vs personal inbox
- Needs Action / Other polish

## Recently completed
- one-click local refresh via **Run export + reload** when a local runner is available, with **Reload current JSON** fallback
- dynamic score updates
- score labels
- light mode + toggle
- attachment fix
- Other routing fix

## Do not build
- sending messages
- Mac app / infra expansion
- UI editing tools
- multiple reply options
