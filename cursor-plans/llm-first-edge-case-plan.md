# LLM-First Edge Case Handling Plan

## Philosophy: Pure LLM-First with Graceful Degradation

**Core Principle**: The LLM should handle ALL parsing. No rule-based fallbacks. When in doubt, ask for clarification rather than guess.

**Priority Order**:

1. **LLM handles edge case gracefully** (ideal)
2. **LLM asks for clarification** (good)
3. **LLM returns clear error with helpful suggestions** (acceptable)
4. **System crashes or gives unhelpful error** (unacceptable)

**NO RULE-BASED PARSING**: Eliminate all regex/rule-based parsing. The LLM is the single source of truth for command interpretation.

## LLM-First Approach

### 1. Enhanced LLM Prompting

**Current Issue**: Basic system prompt doesn't handle edge cases well and still falls back to rule-based parsing.

**Solution**: Create comprehensive system prompts that:

- Explicitly handle common edge cases
- Ask for clarification when uncertain
- Provide helpful suggestions
- NEVER fall back to rule-based parsing

**Enhanced System Prompt**:

```
You are a calendar assistant. Handle user requests intelligently and gracefully.

EDGE CASE HANDLING:
- Misspellings: "shedule" → understand as "schedule"
- Poor grammar: Extract the core intent, ignore extra words
- Ambiguous dates: Ask for clarification ("which Monday?")
- Vague requests: Ask specific questions ("what type of meeting?")
- Past dates: Warn and suggest correction
- Invalid dates: Explain the issue and suggest format

WHEN TO ASK FOR CLARIFICATION:
- Multiple possible interpretations
- Missing critical information
- Ambiguous references ("it", "that meeting")
- Unclear intent
- Invalid or impossible dates/times

RESPONSE FORMAT:
- Success: {"action": "create_event", "details": {...}}
- Clarification needed: {"action": "clarify", "details": {"question": "Which Monday?", "context": "..."}}
- Error: {"action": "error", "details": {"message": "Invalid date format", "suggestion": "Use YYYY-MM-DD"}}

NEVER fall back to rule-based parsing. Always provide a helpful response.
```

### 2. New Function Definitions

**Add new functions for edge case handling**:

```python
calendar_functions = [
    # ... existing functions ...
    {
        "name": "clarify",
        "description": "Ask user for clarification when request is ambiguous",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Specific question to ask user"},
                "context": {"type": "string", "description": "Context about what was unclear"},
                "options": {"type": "array", "items": {"type": "string"}, "description": "Available options if applicable"}
            },
            "required": ["question"]
        }
    },
    {
        "name": "error",
        "description": "Return error with helpful message when request cannot be processed",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Error message"},
                "suggestion": {"type": "string", "description": "Helpful suggestion for user"},
                "reason": {"type": "string", "description": "Reason for the error"}
            },
            "required": ["message"]
        }
    }
]
```

### 3. Edge Case Categories for LLM Training

#### A. Input Normalization (LLM should handle)

- **Misspellings**: "shedule" → "schedule", "meeting" → "meetin"
- **Poor grammar**: "meeting tomorrow at 2pm I need" → extract core intent
- **Mixed case/whitespace**: Normalize automatically
- **Punctuation**: Handle gracefully, ignore irrelevant punctuation

#### B. Date/Time Ambiguity (LLM should clarify)

- **Ambiguous dates**: "next Monday" when today is Monday
- **Relative dates**: "in 3 days", "this weekend"
- **Time ambiguity**: "noon" vs "12pm", "lunch time"
- **Invalid dates**: Detect and explain the issue

#### C. Context Dependencies (LLM should ask)

- **Vague references**: "move it to Friday" → "What would you like to move?"
- **Multiple matches**: "delete team meeting" when multiple exist
- **Unclear intent**: "do something with my calendar" → ask for specifics

#### D. Complex Requests (LLM should break down)

- **Multi-step**: "schedule meeting and invite John" → handle step by step
- **Conditional**: "if I'm free tomorrow, schedule meeting" → check availability first
- **Bulk operations**: "delete all meetings this week" → confirm before proceeding

### 4. Graceful Degradation Strategy

**Level 1**: LLM handles edge case perfectly
**Level 2**: LLM asks for clarification
**Level 3**: LLM returns helpful error with suggestions
**Level 4**: System provides generic error message

**NO RULE-BASED FALLBACK**: If LLM fails, return error with suggestion to rephrase.

## Testing Strategy

### Phase 1: Comprehensive Edge Case Testing

**Create test suite covering all edge case categories**:

1. **Input normalization tests** (misspellings, grammar, whitespace)
2. **Date/time ambiguity tests** (invalid dates, ambiguous times)
3. **Context dependency tests** (vague references, multiple matches)
4. **Complex request tests** (multi-step, conditional logic)
5. **System resilience tests** (API errors, timeouts)

**Test Format**:

```python
def test_edge_case_misspelling():
    """Test LLM handles 'shedule' → 'schedule'"""
    result = interpret_command("shedule meeting tomorrow")
    assert result["action"] == "create_event"
    assert "meeting" in result["details"]["title"]

def test_edge_case_invalid_date():
    """Test LLM returns error for invalid dates"""
    result = interpret_command("schedule meeting on 2024-13-45")
    assert result["action"] == "error"
    assert "Invalid date" in result["details"]["message"]

def test_edge_case_ambiguous_date():
    """Test LLM asks for clarification on ambiguous dates"""
    result = interpret_command("schedule meeting next Monday")
    # Should ask for clarification if today is Monday
    if today_is_monday():
        assert result["action"] == "clarify"
        assert "which Monday" in result["details"]["question"]
```

### Phase 2: LLM Enhancement

**Based on test results, enhance LLM prompting**:

1. **Identify common failure patterns**
2. **Update system prompts** to handle specific edge cases
3. **Add clarification logic** for ambiguous inputs
4. **Implement timeout handling** for API calls

### Phase 3: Implementation

**Only after comprehensive testing**:

1. **Update LLM prompts** based on test results
2. **Add clarification handling** in main loop
3. **Add timeout handling** for API calls
4. **Add helpful error messages** and suggestions
5. **Remove all rule-based parsing**

## Success Metrics

- **Edge Case Success Rate**: > 90% of edge cases handled gracefully
- **Clarification Rate**: < 10% of inputs need clarification
- **Error Rate**: < 5% of inputs result in unhelpful errors
- **User Experience**: All responses are helpful and actionable
- **Zero Rule-Based Fallbacks**: 100% LLM-driven parsing

## Implementation Order

1. **Create comprehensive edge case test suite**
2. **Add timeout handling** to prevent hanging
3. **Run tests against current LLM implementation**
4. **Analyze failure patterns and common issues**
5. **Enhance LLM prompts** based on test results
6. **Add clarification and error functions**
7. **Remove all rule-based parsing**
8. **Test end-to-end** with real user scenarios

This approach ensures we're building a truly LLM-first system that gracefully handles edge cases while maintaining excellent user experience.
