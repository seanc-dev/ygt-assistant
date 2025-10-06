# Core Engine — TDD Plan

## Sections
- Store: CRUD, feature flag `CORE_ENABLE_VECTORS`
- Retrieval: by_key, similar (flagged), context_for
- Writer: episodic, semantic, procedural, narrative
- Policy: risk flags, redaction
- Glue: prompt builders 

## Test Outline

describe('Core Engine')
  describe('Store')
    it('creates and retrieves items by id and key')
    it('updates last_used_at on access')
    it('respects CORE_ENABLE_VECTORS flag')
  describe('Retrieval')
    it('recall.by_key returns correct item')
    it('recall.similar returns top_k when vectors enabled')
    it('context_for aggregates items by level')
  describe('Writer')
    it('write.episodic persists event with meta')
    it('write.semantic persists fact with source')
    it('write.procedural persists how_to with source')
    it('write.narrative persists journal with tags')
  describe('Policy')
    it('redacts sensitive fields when risk > threshold')
  describe('Glue')
    it('injects recall results deterministically into prompts')
