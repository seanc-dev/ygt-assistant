# Edge Case Testing Plan

## Overview

Comprehensive testing plan to make the calendar agent bulletproof against edge cases, misspellings, poor grammar, and non-standard requests.

## Test Categories

### 1. Input Normalization Tests

**Misspellings:**

- "shedule meeting" → should correct to "schedule meeting"
- "meeting" → "meetin" → should handle gracefully
- "tomorrow" → "tomorow" → should correct
- "calender" → "calendar" → should understand intent

**Poor Grammar:**

- "meeting tomorrow at 2pm I need" → should extract "meeting tomorrow at 2pm"
- "schedule meeting for tomorrow please" → should handle extra words
- "I want to have a meeting" → should extract meeting intent

**Mixed Case & Whitespace:**

- "SCHEDULE MEETING" vs "schedule meeting" vs "Schedule Meeting"
- " schedule meeting tomorrow " → should normalize whitespace
- "schedule\nmeeting\ttomorrow" → should handle various whitespace

**Punctuation:**

- "schedule meeting, tomorrow at 2pm!" → should handle gracefully
- "delete meeting?" → should handle question marks
- "move meeting..." → should handle ellipsis

### 2. Date/Time Edge Cases

**Invalid Dates:**

- "schedule meeting on 2024-13-45" → should error gracefully
- "schedule meeting on 2024-02-30" → should detect invalid date
- "schedule meeting on 2023-02-29" → should detect leap year issue

**Past Dates:**

- "schedule meeting yesterday" → should warn or suggest correction
- "schedule meeting last week" → should handle appropriately
- "schedule meeting on 2020-01-01" → should detect past date

**Ambiguous Dates:**

- "next Monday" when today is Monday → should clarify
- "this weekend" → should resolve to Saturday/Sunday
- "in 3 days" → should calculate correctly

**Time Ambiguity:**

- "noon" vs "12pm" vs "12:00" → should handle all
- "midnight" vs "12am" → should handle both
- "lunch time" → should suggest default time
- "2pm" vs "14:00" → should handle both formats

### 3. Event Management Edge Cases

**Duplicate Events:**

- "schedule team meeting" when one already exists → should detect and ask
- "schedule daily standup" when recurring exists → should handle

**Event Not Found:**

- "delete meeting" when no meeting exists → should provide helpful message
- "move team meeting" when no team meeting exists → should suggest alternatives

**Multiple Matches:**

- "delete team meeting" when multiple team meetings exist → should list options
- "move meeting" when multiple meetings today → should ask for clarification

**Recurring Event Conflicts:**

- "move daily standup" → should clarify which occurrence
- "delete weekly meeting" → should ask: series or single occurrence?

### 4. Natural Language Edge Cases

**Vague Commands:**

- "do something with my calendar" → should ask for clarification
- "help me organize" → should provide suggestions
- "what should I do?" → should ask for more context

**Context Dependencies:**

- "move it to Friday" → what is "it"? → should ask for clarification
- "delete that meeting" → should maintain context or ask

**Multi-step Requests:**

- "schedule a meeting tomorrow, then remind me to prepare" → should handle both
- "create meeting and invite John" → should handle both actions

**Complex Requests:**

- "copy my meeting tomorrow to next week and invite John" → should break down
- "if I'm free tomorrow, schedule a meeting" → should check availability first

### 5. System Integration Edge Cases

**Calendar Access Issues:**

- EventKit permissions not granted → should provide helpful error
- Calendar not found → should suggest alternatives
- Network connectivity issues → should handle gracefully

**API Issues:**

- OpenAI API timeout → should fall back to regex parsing
- Rate limiting → should handle gracefully
- Invalid API key → should use fallback parsing

**Performance Issues:**

- Large calendar (1000+ events) → should handle efficiently
- Memory issues → should handle gracefully
- Concurrent access → should handle multiple CLI instances

### 6. User Experience Edge Cases

**Empty States:**

- "show my events" when no events exist → should show helpful message
- "delete all meetings" when no meetings → should handle gracefully

**Overflow Protection:**

- "list all events" when 1000+ events → should paginate or limit
- "search meetings" with many results → should provide summary

**Confirmation Dialogs:**

- "delete important meeting" → should ask for confirmation
- "delete all meetings this week" → should ask for confirmation
- "move recurring meeting" → should clarify scope

### 7. Missing Features (Need Implementation)

**Event Copying:**

- "copy team meeting to next week" → implement copy_event function
- "duplicate yesterday's meeting" → implement copy with date logic

**Bulk Operations:**

- "delete all meetings this week" → implement bulk_delete
- "move all meetings to next week" → implement bulk_move

**Event Templates:**

- "schedule a 1:1 meeting" → implement template system
- "create standup meeting" → implement predefined templates

**Attendee Management:**

- "invite john@email.com to the meeting" → implement attendee functions
- "add Sarah to team meeting" → implement attendee lookup

**Search & Filter:**

- "find meetings about project X" → implement fuzzy search
- "show meetings with John" → implement attendee filtering

**Undo Operations:**

- "undo last action" → implement undo stack
- "revert that change" → implement action history

## Implementation Priority

### Phase 1: Critical Edge Cases

1. Input normalization (misspellings, grammar)
2. Invalid date/time handling
3. Event not found scenarios
4. System error handling

### Phase 2: User Experience

1. Confirmation dialogs
2. Empty state handling
3. Overflow protection
4. Context clarification

### Phase 3: New Features

1. Event copying
2. Bulk operations
3. Search & filtering
4. Undo operations

## Test Implementation

### Unit Tests

- Create test cases for each edge case category
- Mock dependencies for isolated testing
- Test both success and failure scenarios

### Integration Tests

- Test full pipeline with edge case inputs
- Verify error messages are helpful
- Test fallback mechanisms

### End-to-End Tests

- Test real user scenarios with edge cases
- Verify system resilience under stress
- Test concurrent access scenarios

## Success Metrics

- **Error Rate**: < 5% of edge cases should cause crashes
- **User Experience**: All error messages should be helpful
- **Recovery**: System should gracefully handle 95% of edge cases
- **Performance**: Edge case handling should not significantly impact performance
