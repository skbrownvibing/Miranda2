# Architecture: iMessage Responsiveness Tracker

This document defines the core data flow and required helper functions.  
All logic in the system must route through these functions.  
Do not duplicate or bypass them.

---

## Core model

The system operates on **normalized events** exported from iMessage.

- A **normalized event** is the canonical unit of conversation history
- All chronology, state, and scoring are derived from normalized events
- No logic should rely on filtered subsets as a source of truth

---

## Core invariants

- Latest event = newest normalized event (never filtered)
- Preview = display-only (never used for state or scoring)
- Response state is derived from normalized events only
- Score, action list, and stats share the same eligibility set
- Exporter owns normalization; frontend does not reinterpret message semantics

---

## Required functions

These functions define the system. All features must use them.

---

### 1. `getLatestEvent(thread)`

**Purpose:**  
Return the actual latest event in a conversation.

```js
function getLatestEvent(thread)
