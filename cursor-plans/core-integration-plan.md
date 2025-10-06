# Core Integration — Phase One Implementation Plan

## Vision

Transform the reactive calendar assistant into a proactive, intelligent agent with semantic memory, narrative awareness, and long-term recall. Core will be the inference layer that embeds and indexes life data, starting with calendar events and expanding to reminders, email, and conversations.

## Foundation: Current Status ✅

- **Working Apple Calendar integration** with full conversational control
- **EventKit + GPT-4o pipeline** live and tested
- **Prototype driven by tests** with comprehensive coverage
- **Cursor auto-mode** in place for rapid iteration
- **LLM-first approach** established with edge case handling
- **Embedding tech** not yet implemented but central to the vision

## Phase One Goals & Implementation

### 1. Create First Embedding Index

#### Technical Implementation

- **Data Extraction**: Extract titles + descriptions from past calendar events

  - Use EventKit to fetch historical events (last 6-12 months)
  - Extract event title, description, location, attendees
  - Include recurring event patterns and frequency
  - Capture event duration and time patterns

- **Embedding Strategy**: Use OpenAI embeddings or similar

  - OpenAI `text-embedding-3-small` for cost efficiency
  - Create embeddings for each event's full context
  - Store metadata alongside embeddings (date, duration, attendees)
  - Batch processing for efficiency

- **Storage Solution**: Local vector database
  - **Option A**: ChromaDB for full vector database features
  - **Option B**: Simple JSON + numpy arrays for lightweight approach
  - **Option C**: SQLite with vector extensions
  - **Recommendation**: Start with ChromaDB for rapid prototyping

#### Implementation Steps

1. **Create `core/embedding_manager.py`**

   ```python
   class EmbeddingManager:
       def __init__(self, vector_db_path="core/memory.db")
       def extract_event_data(self, events: List[EKEvent]) -> List[Dict]
       def create_embeddings(self, event_data: List[Dict]) -> List[float]
       def store_embeddings(self, embeddings: List[float], metadata: List[Dict])
       def search_similar(self, query: str, top_k: int = 5) -> List[Dict]
   ```

2. **Add embedding pipeline to calendar operations**

   - Hook into `create_event`, `delete_event`, `move_event`
   - Update embeddings when events change
   - Maintain embedding index consistency

3. **Create test suite for embedding functionality**
   - Test data extraction accuracy
   - Test embedding similarity search
   - Test performance with large datasets

### 2. Implement recall() Function

#### Semantic Search Capabilities

- **Similar Event Search**: Find past events similar to current request
- **Pattern Recognition**: Identify recurring patterns and preferences
- **Context-Aware Suggestions**: Use past events to inform current decisions

#### Use Cases

- **"Schedule my usual Tuesday check-in with B"**

  - Search for past "check-in" events with "B"
  - Extract usual time, duration, location
  - Suggest similar scheduling

- **"I need to prepare for the team meeting"**

  - Find past team meetings
  - Extract typical agenda items, attendees, duration
  - Suggest preparation tasks

- **"When do I usually have lunch?"**
  - Search for lunch-related events
  - Identify patterns in timing and duration
  - Provide personalized lunch scheduling

#### Implementation

```python
class CoreMemory:
    def recall(self, query: str, context: Dict = None) -> List[Dict]:
        """Semantic search for similar past events"""

    def get_patterns(self, event_type: str) -> Dict:
        """Extract patterns from past events"""

    def suggest_similar(self, current_request: str) -> Dict:
        """Suggest similar past events for current request"""
```

### 3. Contextual Nudging

#### Proactive Intelligence

- **Time-Based Suggestions**: "You usually check email around this time"
- **Pattern Recognition**: "You typically have team standup on Mondays"
- **Conflict Prevention**: "You have 5 meetings back-to-back, want me to add buffer time?"
- **Habit Reinforcement**: "You mentioned wanting to exercise more, should I schedule gym time?"

#### Implementation Strategy

1. **Time Pattern Analysis**

   - Analyze when user typically performs certain activities
   - Build time-based suggestion engine
   - Respect user's natural rhythms

2. **Context Awareness**

   - Track current context (time, day, recent activities)
   - Match context to past patterns
   - Generate relevant suggestions

3. **User Preference Learning**
   - Learn which suggestions are helpful vs annoying
   - Adapt suggestion frequency and timing
   - Respect user's preference for proactive vs reactive assistance

#### Technical Implementation

```python
class ContextualNudger:
    def analyze_time_patterns(self) -> Dict[str, List[TimePattern]]
    def generate_suggestions(self, current_context: Dict) -> List[Suggestion]
    def learn_preferences(self, user_feedback: Dict)
    def should_nudge(self, context: Dict) -> bool
```

### 4. Structured Memory Types

#### Memory Schema Design

Define comprehensive memory types that Core will hold:

1. **Past Events** (calendar, reminders, emails)

   ```json
   {
     "type": "past_event",
     "title": "Team Standup",
     "description": "Daily team sync",
     "date": "2024-01-15",
     "duration": 30,
     "attendees": ["Alice", "Bob", "Charlie"],
     "location": "Conference Room A",
     "embedding": [0.1, 0.2, ...],
     "tags": ["recurring", "team", "sync"]
   }
   ```

2. **Intentions** (e.g. "I want to get fitter")

   ```json
   {
     "type": "intention",
     "content": "I want to get fitter",
     "date_created": "2024-01-10",
     "priority": "high",
     "related_events": ["gym_sessions"],
     "progress_tracking": true
   }
   ```

3. **Commitments** (e.g. "follow up with Anna")

   ```json
   {
     "type": "commitment",
     "content": "follow up with Anna about project status",
     "date_created": "2024-01-12",
     "due_date": "2024-01-20",
     "status": "pending",
     "priority": "medium"
   }
   ```

4. **Preferences** (e.g. "no meetings before 11am")
   ```json
   {
     "type": "preference",
     "category": "scheduling",
     "content": "no meetings before 11am",
     "strength": 0.9,
     "date_learned": "2024-01-08",
     "context": "work_schedule"
   }
   ```

#### Implementation Approach

1. **Start with JSON logging** from tests and user inputs
2. **Define schema** for each memory type
3. **Implement storage** in structured format
4. **Add retrieval** and search capabilities
5. **Integrate with embedding system**

## Technical Architecture

### Core Components

```
core/
├── embedding_manager.py      # Embedding creation and storage
├── memory_manager.py         # Memory type management
├── recall_engine.py          # Semantic search and retrieval
├── nudge_engine.py           # Contextual suggestions
├── schema.py                 # Memory type definitions
└── tests/                    # Comprehensive test suite
```

### Integration Points

- **EventKit Integration**: Hook into calendar operations
- **LLM Integration**: Enhance prompts with Core memory
- **CLI Integration**: Add Core commands to main loop
- **Test Integration**: Comprehensive testing of Core features

## Success Metrics

### Technical Performance

- **Embedding Accuracy**: > 90% relevant search results
- **Search Speed**: < 500ms for semantic searches
- **Memory Efficiency**: Handle 10,000+ events efficiently
- **Storage Size**: < 100MB for 1 year of data

### User Experience

- **Recall Accuracy**: > 85% of recalled events are relevant
- **Suggestion Quality**: > 70% of nudges are helpful
- **Pattern Recognition**: Correctly identify user patterns
- **Proactive Value**: Users find suggestions genuinely helpful

### Business Impact

- **Time Savings**: Reduce scheduling time by additional 20%
- **User Satisfaction**: > 4.5/5 rating for intelligent features
- **Adoption Rate**: > 60% of users use Core features daily
- **Productivity**: Measurable improvement in scheduling efficiency

## Implementation Timeline

### Week 1: Foundation

- [ ] Set up ChromaDB or vector storage
- [ ] Create embedding manager
- [ ] Implement basic event data extraction
- [ ] Add embedding pipeline to calendar operations

### Week 2: Core Features

- [ ] Implement recall() function
- [ ] Add semantic search capabilities
- [ ] Create memory type schemas
- [ ] Build basic memory storage

### Week 3: Intelligence

- [ ] Implement contextual nudging
- [ ] Add pattern recognition
- [ ] Create suggestion engine
- [ ] Integrate with LLM prompts

### Week 4: Integration & Testing

- [ ] Full integration with existing system
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] User experience validation

## Next Steps

1. **Start with embedding infrastructure** - foundation for all Core features
2. **Implement basic recall()** - most immediate user value
3. **Add contextual nudging** - transforms reactive to proactive
4. **Expand memory types** - enables full Jarvis-like capabilities

This Core integration will transform the calendar assistant from a reactive tool into a proactive, intelligent agent with true semantic memory and contextual awareness.
