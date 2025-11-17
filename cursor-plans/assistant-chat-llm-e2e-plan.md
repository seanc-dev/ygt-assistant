# Assistant Chat & LLM Ops E2E Test Plan

## Test Sections

### 1. Assistant Chat Flows

#### 1.1 Happy Path (`assistant_chat_happy_path.yaml`)
- **Steps:**
  1. Reset state
  2. Send blank text → expect guidance message
  3. Send "scan" → expect approvals list
  4. Send "approve appr-1" → expect confirmation
  5. Send gratitude message → expect friendly response
- **Assertions:**
  - `messages` array contains expected content
  - `approvals` preview structure matches schema
  - `history` log entries created
- **Snapshot:** `llm_testing/snapshots/assistant_chat_happy_path.json`

#### 1.2 Edge Cases (`assistant_chat_edge_cases.yaml`)
- **Steps:**
  1. Reset state
  2. Send unknown command → expect helpful error
  3. Send "approve invalid-id" → expect not found message
  4. Send multiple consecutive scans → verify no duplicates
  5. Send "scan", then "scan agenda", then "skip appr-1" → verify state transitions
- **Assertions:**
  - Error messages are friendly and actionable
  - Approval statuses mutate correctly
  - No duplicate approvals created
- **Snapshot:** `llm_testing/snapshots/assistant_chat_edge_cases.json`

#### 1.3 Live Inbox Integration (`assistant_chat_live_inbox.yaml`)
- **Steps:**
  1. Reset state
  2. Enable `FEATURE_LIVE_LIST_INBOX`
  3. Inject inbox fixture (`fixtures/graph/inbox_small.json`)
  4. Send "scan" → verify proposals mirror inbox subjects
- **Assertions:**
  - Proposals match inbox items
  - No PII in responses (`must_not_contain` expectations)
- **Snapshot:** `llm_testing/snapshots/assistant_chat_live_inbox.json`

### 2. LLM Operations Flows

#### 2.1 Task Operations - Training Wheels (`llm_ops_task_training_wheels.yaml`)
- **Steps:**
  1. Reset state
  2. Seed workroom via `/dev/workroom/seed`
  3. Set trust level to `training_wheels`
  4. Call `/api/workroom/tasks/{task_id}/assistant-suggest` with multi-sentence message
  5. Verify operations split: `applied` (chat only) vs `pending` (create/update)
  6. Approve one pending operation via `/assistant-approve`
  7. Re-fetch task → verify status change
- **Assertions:**
  - Only low-risk ops auto-apply
  - Medium-risk ops require approval
  - Task state updates correctly
- **Snapshot:** `llm_testing/snapshots/llm_ops_task_training_wheels.json`

#### 2.2 Task Operations - Autonomous (`llm_ops_task_autonomous.yaml`)
- **Steps:**
  1. Reset state
  2. Seed workroom
  3. Set trust level to `autonomous`
  4. Call `/api/workroom/tasks/{task_id}/assistant-suggest` with message
  5. Verify all ops auto-apply
  6. Verify task count increases, statuses mutate
- **Assertions:**
  - All operations auto-apply
  - State changes persist
- **Snapshot:** `llm_testing/snapshots/llm_ops_task_autonomous.json`

#### 2.3 Queue Operations - Focus Action (`llm_ops_queue_focus.yaml`)
- **Steps:**
  1. Reset state
  2. Seed queue via `/dev/queue/seed`
  3. Get first action ID
  4. Call `/api/queue/{action_id}/assistant-suggest` with message
  5. Verify applied/pending split
  6. Approve one operation
  7. Edit one operation
  8. Verify `/api/queue/list` reflects changes
  9. Send multiple consecutive prompts → verify context preserved
- **Assertions:**
  - Operations respect trust level
  - Action state updates correctly
  - Multi-turn context maintained
- **Snapshot:** `llm_testing/snapshots/llm_ops_queue_focus.json`

## Snapshot Expectations

Each scenario captures:
- Full `transcript` JSON with all HTTP requests/responses
- Normalized timestamps (replaced with `"<timestamp>"`)
- Normalized UUIDs (replaced with `"<uuid>"`)
- Message content for conversational tone verification

## CI Integration

- Scenarios tagged with `@pytest.mark.chat_llm_e2e` or env flag `CHAT_LLM_E2E=true`
- Run in CI `llm-loop` job for every PR
- Full suite runs on merge to main via `llm-evals.yml`

