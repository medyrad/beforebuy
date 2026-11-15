# Bounded conversational UX contract

FR-084/085: Message.reply_actions is an optional list (2–5) of server-authored `{id,label,kind,value,
conversation_id,question_id,revision}`. Kinds are SET_CATEGORY, SET_RECIPIENT, CONFIRM_BUDGET,
KEEP_BUDGET, CONFIRM_NEED, CORRECT_NEED. POST messages optionally includes `answer: {question_id, action_id, revision}`.
The existing conversation URL supplies ownership. Server requires the latest FINAL assistant question, no newer
accepted user turn, current revision, no brief update after the question, matching label and allowlisted stored action. Invalid/stale actions return 409;
malformed input 422. Idempotency hash includes answer; an exact replay precedes stale checks. A double click cannot
apply the action twice. Plain text has the same acceptance/publication path.

ShoppingBrief.conversation_state holds a pending budget `{budget_toman,source_message_id}` or a `correcting_need` flag. First explicit budget
is user-stated/unconfirmed; conflict leaves current budget intact. Bounded grammar accepts one decimal Persian/Arabic/
Latin numeric amount, optional thousand/million, explicit toman/rial and an explicit budget phrase or standalone
amount (not prices, ranges or ambiguous multi-amount text). Rial conversion is exact and integral. Confirmation or
keep-current is an explicit answer (chip or its exact displayed text), not inferred sentiment. Changes advance revision,
reset confirmed and invalidate prior context/choices. Confirm-need is explicit and never starts research.

DELETE /conversations clears only this guest's conversations (including expired rows), invalidates active work and
cascades derived memory under existing deletion semantics. Independent settings, credentials and spend ledgers survive.
List remains paginated; UI search explicitly covers loaded titles only. Read detail returns latest 200 messages in
chronological order and discloses truncation, so current questions remain reachable in long conversations.
