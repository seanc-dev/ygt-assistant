# Conversation Memory & Session State Plan

## Overview

Implement a two-tier memory system to support conversational context:

1. **Ephemeral Working Memory** (`ConversationState`)

   - Session-only context stored in memory (no I/O)
   - Stores last N user/assistant turns (raw messages + parsed intents)
   - Powers reference resolution ("it", "that meeting") and multi-step flows
   - Implement as an in-memory deque or ring buffer

2. **Persistent Long-Term Memory** (`CoreMemory`)
   - Embedding-backed storage for semantic recall
   - Holds:
     - Past calendar events (embedded)
     - Learned preferences, intentions, commitments
     - Conversation snippets worth remembering (e.g. "no meetings before 11am")
   - Backed by a vector store (ChromaDB or similar)
   - Enables recall() and proactive nudges based on patterns

## Integration Flow

On each user turn:

1. Retrieve the last M turns from `ConversationState.get_context_window()` and include them in the LLM prompt.
2. Parse user input; if intent requires historical context, call `CoreMemory.recall(query)`.
3. Send combined prompt to LLM (with context + function definitions).
4. Receive LLM function call response.
5. Dispatch action; update `ConversationState.append_turn(user_input, action_output)`.
6. If calendar data changed, update embeddings via `EmbeddingStore`.

## Module Structure (in `core/`)

```
core/
├── conversation_manager.py    # Ephemeral memory (ConversationState)
├── memory_manager.py         # Long-term embedding-backed memory (CoreMemory)
├── embedding_store.py        # Abstraction over ChromaDB or JSON storage
├── recall_engine.py          # High-level memory interface (recall, suggest)
└── types.py                  # Shared data types for conversations and memory
```

## Next Steps

1. **Define `ConversationState`**

   - `append_turn(user: str, assistant: str)`
   - `get_context_window(n: int) -> List[Turn]`
   - `resolve_reference(pronoun: str) -> context_object`

2. **Wire into CLI Loop**

   - Load context window before each LLM call
   - Append each new turn after dispatch

3. **Update Core Integration Plan**

   - Add step in Phase One to integrate `ConversationState` into prompts

4. **Decide on Session Embeddings (optional)**

   - If semantic similarity is needed for short-term context, embed recent turns
   - Store in a lightweight in-memory vector table

5. **Document End-to-End Flow**
   - Diagram or sequence of: input → ConversationState → LLM → action → update memories

This plan ensures robust, session-level context handling while delegating long-term semantic memory to the Core engine.
