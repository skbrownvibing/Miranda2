# PRD: Local-First iMessage Responsiveness Tracker for Mac

## Overview

A local-first Mac app that helps users identify which 1:1 personal text conversations are still waiting on a reply, measure how responsive they are over time, and make the process feel motivating rather than stressful.

## Problem

iMessage is not designed to help users track response debt. Personal conversations get buried under logistics, spam, group chats, and low-priority noise, so users miss replies they intended to send and lose visibility into how responsive they actually are.

## Target user

Mac users who text frequently, primarily use iMessage for personal communication, and want a lightweight way to see which 1:1 conversations are waiting on them.

## Core value

The product makes texting responsiveness measurable and actionable by:

- showing which personal conversations are currently waiting on the user
- measuring reply behavior over time
- helping users reduce missed replies
- making the process feel motivating, satisfying, and easy to return to

## Current product

The current product has two components:

1. A local Mac export script that reads iMessage data and writes normalized JSON output
2. A local web app that reads the exported JSON and computes an action list, responsiveness score, and historical trends

The current product has no server, no user accounts, and no cloud sync. All data remains local to the user’s machine.

## Core behaviors

The app:
- filters out conversations unlikely to reflect personal response debt
- identifies 1:1 conversations where the latest relevant message is from the other person
- ranks those conversations into an action list
- computes a responsiveness score from historical reply behavior
- shows score history and trends over time
- lets users dismiss conversations that do not require a reply

## Decision rules

### 1:1 conversation

A 1:1 conversation is a thread with exactly one other participant and no group-chat metadata.

### Relevant message

A relevant message is a message that counts toward conversational response debt.

Relevant messages exclude:
- system-generated messages
- reactions, tapbacks, and similar non-message events
- messages classified as Automated
- messages classified as spam

### Waiting on you

A conversation is considered "waiting on you" when all of the following are true:

- it is a 1:1 conversation
- the latest relevant message was sent by the other person
- the conversation is not excluded from the action list
- the conversation has not been manually dismissed

For MVP, the product assumes that a latest incoming relevant message may require a reply, even if that is imperfect.

### Excluded conversations

A conversation is excluded from the action list and excluded from scoring when any of the following are true:

- it is a group chat
- it is classified as spam
- it is classified as Automated
- it contains no relevant conversational messages

### Automated classification

A conversation may be classified as Automated when its messages are primarily:
- delivery updates
- rideshare notifications
- appointment reminders or scheduling flows
- reservation confirmations
- verification or authentication messages
- other automated transactional messages that do not meaningfully reflect personal responsiveness

Automated texts that ask for confirmation, such as replying with a number to confirm an appointment or reservation, should still be excluded.

Human logistics messages are not excluded.

This classification is heuristic and may be overridden by the user.

### Unsaved numbers

Conversations with participants who are not saved as contacts are still eligible for the action list and scoring unless they are separately classified as spam or Automated.

### Dismissed conversations

A dismissed conversation is one the user has manually marked as not requiring a reply.

Dismissed conversations:
- do not appear in the action list
- do not count as unresolved conversations for scoring
- may reappear if a new relevant incoming message arrives later

### Manual overrides

User-applied overrides take precedence over automatic classification.

If a user manually reclassifies or dismisses a conversation, that override remains in effect until a new relevant message changes the state of the conversation.

## Product principles

- **Local-first:** all user data stays on device
- **Fast:** export and review should take minutes, with minimal setup
- **Focused:** optimize for personal response tracking, not full messaging replacement
- **Actionable:** every metric should help the user reply, triage, or improve habits
- **Enjoyable:** the product should feel motivating and light, not guilt-inducing
- **Gamified:** scores, streaks, and progress should make users want to come back

## MVP scope

### Included
- local iMessage export
- heuristic filtering for spam, Automated, and group chats
- contact protection for known contacts
- manual category overrides
- unreplied conversation action list
- responsiveness score
- score history, streaks, and trends
- timeline filters
- handoff to reply in Messages

### Excluded
- sending texts inside the product
- live sync with Messages
- iPhone support
- cloud backup
- user accounts

## Scoring model

The responsiveness score is a 0-100 measure of how consistently the user replies to personal 1:1 conversations.

The product should compute:
- a current overall score
- a daily score for each day
- score history over time

The score is based on three components:
- reply rate over the last 7 days
- average reply time over the last 7 days
- penalty for conversations currently waiting on the user

Excluded conversations do not affect the score. This includes group chats, spam, Automated conversations, and manually dismissed conversations.

### Reply rate

Reply rate measures how often the user responds when a conversation is waiting on them over the last 7 days.

Higher reply rates increase the score.

### Average reply time

Average reply time measures how long the user typically takes to reply after receiving a relevant incoming message over the last 7 days.

Faster replies increase the score. Slower replies reduce the score.

### Open conversation penalty

The score includes a penalty for conversations that are currently waiting on the user.

Older unresolved conversations should reduce the score more than newer unresolved conversations.

A single long-unanswered conversation should continue to hurt the score until the user replies or manually dismisses it.

### Daily score

The product should compute a daily score so users can see how their responsiveness changes day to day.

The daily score should reflect the user’s recent reply behavior and current unresolved conversations as of that day.

### Product requirements for scoring

The scoring model should be:
- stable enough to feel fair
- simple enough to explain to the user
- sensitive enough to reward improvement quickly
- motivating enough to encourage repeat use rather than guilt or avoidance

## Success criteria

- users can quickly see which conversations are waiting on them
- users feel the score roughly matches their real responsiveness
- repeated use reduces missed replies
- users check the product daily or near-daily
- setup is simple enough for non-technical users

## Constraints

- Mac only
- depends on exported iMessage data rather than live system sync
- Apple platform limitations make real-time sync and direct text sending difficult
- categorization is heuristic and imperfect

## Non-goals

- replacing iMessage
- judging emotional importance perfectly
- determining whether a user morally owes someone a reply
- supporting live texting across devices

## Edge cases to handle

- conversations with people not saved as contacts
- conversations with multiple phone numbers for one contact
- reactions, tapbacks, and other non-standard message events
- system or service messages
- chats with missing or incomplete contact names
- muted or pinned conversations
- exported data from multiple time periods
- conversations that are partly logistical and partly personal

## Future directions

### Near term
- reduce friction in import and export
- improve categorization accuracy
- make repeated use feel more seamless
- make the product feel more fun and habit-forming

### Longer term
- support replying inside the product
- explore lightweight reply drafting or response automation
- reduce delay between fresh message data and app state
- evaluate whether the product should evolve into a lightweight messaging workflow layer
