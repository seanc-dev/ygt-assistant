# LLM-to-LLM Testing Framework Plan

## Overview

The LLM-to-LLM Testing Framework is a semi-continuous automated testing system that uses synthetic user personas and goal-driven test prompts to evaluate the calendar assistant's behavior and reasoning quality. This framework will enable data-driven improvements to the assistant's capabilities.

## Core Components

### 1. Personas (`llm_testing/personas.py`)

**Purpose**: Define realistic test users with distinct traits, goals, behaviors, and quirks.

**Structure**:

```python
@dataclass
class Persona:
    name: str
    traits: List[str]  # e.g., ["busy executive", "health conscious", "family oriented"]
    goals: List[str]    # e.g., ["optimize productivity", "maintain work-life balance"]
    behaviors: List[str] # e.g., ["prefers morning meetings", "avoids back-to-back calls"]
    quirks: List[str]   # e.g., ["forgets to add travel time", "likes 15-minute breaks"]
    communication_style: str  # e.g., "direct", "detailed", "casual"
    tech_savviness: int  # 1-5 scale
    time_preferences: Dict[str, str]  # e.g., {"work_hours": "9-5", "lunch": "12-1"}
    accessibility_needs: List[str]  # e.g., ["low_vision", "neurodivergent", "mobility"]
    language_fluency: str  # e.g., "native", "fluent", "basic", "learning"
    challenge_type: str  # e.g., "standard", "timezone_shifter", "contradictory", "edge_case"
```

**Initial Personas**:

- **Alex (Executive)**: Busy tech executive, prefers efficiency, values clear communication
- **Sam (Creative)**: Freelance designer, flexible schedule, values work-life balance
- **Jordan (Student)**: Graduate student, budget-conscious, needs study time
- **Casey (Parent)**: Working parent, family-oriented, needs childcare coordination
- **Taylor (Remote Worker)**: Digital nomad, timezone-aware, values flexibility
- **Morgan (Accessibility)**: Low-vision user, prefers audio descriptions, needs clear navigation
- **Riley (Neurodivergent)**: ADHD, needs structure, prefers detailed explanations
- **Kai (Language Learner)**: Non-native English speaker, learning technical terms
- **Jordan (Timezone Shifter)**: Travels frequently, changes timezones mid-scenario
- **Avery (Contradictory)**: Changes preferences mid-conversation, tests adaptability

**Diversity Considerations**:

- **Accessibility Needs**: Low-vision, neurodivergent, mobility, hearing impairments
- **Language Fluency**: Native, fluent, basic, learning English
- **Challenge Personas**: Timezone shifters, contradictory users, edge case testers
- **Cultural Context**: Different cultural approaches to time and scheduling
- **Age Groups**: Different tech comfort levels and communication preferences

### 2. Scenarios (`llm_testing/scenarios.py`)

**Purpose**: Define test scenarios that exercise different aspects of the assistant's capabilities.

**Structure**:

```python
@dataclass
class Scenario:
    name: str
    persona: Persona
    goals: List[str]
    initial_context: Dict[str, Any]
    test_prompts: List[TestPrompt]
    expected_behaviors: List[ExpectedBehavior]
    success_criteria: List[SuccessCriterion]
    difficulty: str  # "easy", "medium", "hard"
    category: str    # "scheduling", "conflict_resolution", "optimization", "edge_cases"
    ground_truth: Dict[str, Any]  # Golden transcript for deterministic reference
    version: str  # Scenario version for tracking changes
```

**Scenario Categories**:

- **Basic Scheduling**: Simple event creation and modification
- **Conflict Resolution**: Handling scheduling conflicts and preferences
- **Optimization**: Suggesting better times, detecting patterns
- **Edge Cases**: Unusual requests, error handling, invalid inputs
- **Integration**: Multi-step workflows, complex scenarios
- **Accessibility**: Testing with accessibility needs
- **Language**: Testing with varying language fluency
- **Challenge**: Timezone shifts, contradictory instructions

**Sample Scenarios**:

1. **"Morning Routine Setup"**: Alex wants to establish a consistent morning routine
2. **"Travel Planning"**: Taylor needs to coordinate across timezones
3. **"Family Coordination"**: Casey needs to balance work and family commitments
4. **"Study Schedule"**: Jordan needs to optimize study time around classes
5. **"Creative Flow"**: Sam wants to maintain creative energy throughout the day
6. **"Accessible Scheduling"**: Morgan needs audio-friendly calendar management
7. **"Structure for ADHD"**: Riley needs detailed, structured scheduling
8. **"Language Learning"**: Kai needs help with technical calendar terms
9. **"Timezone Challenge"**: Jordan changes timezones mid-conversation
10. **"Contradictory User"**: Avery changes preferences and tests adaptability

**Ground-Truth Anchors**:
Each scenario includes a "golden transcript" with expected assistant responses and actions, providing deterministic reference points for success criteria evaluation.

### 3. Test Prompts (`llm_testing/prompts.py`)

**Purpose**: Define specific test prompts that exercise the assistant's capabilities.

**Structure**:

```python
@dataclass
class TestPrompt:
    prompt: str
    context: Dict[str, Any]
    expected_actions: List[str]
    expected_qualities: List[str]  # e.g., ["clear", "helpful", "efficient"]
    difficulty: str
    category: str
    template_vars: Dict[str, Any]  # For dynamic prompt generation
    failure_mode: str  # e.g., "invalid_input", "ambiguous", "edge_case"
```

**Prompt Types**:

- **Direct Requests**: "Schedule a meeting with John tomorrow at 2pm"
- **Ambiguous Requests**: "I need to meet with the team sometime this week"
- **Complex Requests**: "Find the best time for a 2-hour workshop that works for everyone"
- **Error Recovery**: "I made a mistake, can you fix that meeting time?"
- **Optimization Requests**: "I'm feeling overwhelmed, can you help me organize my week?"
- **Invalid Inputs**: "Schedule a meeting yesterday at 3pm"
- **Accessibility Requests**: "Can you describe my schedule in detail?"
- **Language Learning**: "What does 'recurring' mean in calendar terms?"

**Dynamic Prompt Generation**:

```python
class PromptTemplate:
    def __init__(self, template: str, slot_fillers: Dict[str, List[str]]):
        self.template = template
        self.slot_fillers = slot_fillers

    def generate_variations(self, count: int = 5) -> List[TestPrompt]:
        # Generate multiple prompt variations with different slot fillers
        # Useful for fuzz-testing the assistant
```

**Failure Modes**:

- **Invalid Inputs**: Past dates, impossible times, malformed requests
- **Ambiguous Requests**: Vague descriptions, missing context
- **Edge Cases**: Extremely long events, unusual locations, special characters
- **Contradictory Instructions**: Changing preferences mid-conversation
- **Accessibility Challenges**: Testing with different accessibility needs

### 4. Scoring Agent (`llm_testing/evaluator.py`)

**Purpose**: A third LLM that reviews assistant outputs against goals and explains failures.

**Structure**:

```python
class ScoringAgent:
    def __init__(self, config: TestingConfig):
        self.primary_model = config.scoring_model
        self.fallback_model = config.fallback_model
        self.rubric = self._load_rubric()
        self.calibration_data = self._load_calibration()

    def evaluate_response(self, scenario: Scenario, assistant_response: str,
                        expected_behaviors: List[ExpectedBehavior]) -> EvaluationResult:
        # Route to appropriate model based on difficulty
        # Evaluate against rubric with detailed scoring
        # Generate comprehensive feedback
        # Log intermediate scores for regression tracking
```

**Mixed Evaluation Tiers**:

- **Low-Stakes**: GPT-3.5 for basic scenarios (cost control)
- **Medium-Stakes**: GPT-4 for complex scenarios
- **High-Stakes**: GPT-4 with detailed analysis for edge cases
- **Calibration**: Regular sampling to prevent bias against verbose responses

**Evaluation Rubric**:

- **Clarity** (1-5): How clear and understandable is the response?
- **Helpfulness** (1-5): Does the response address the user's needs?
- **Efficiency** (1-5): Is the response concise and actionable?
- **Accuracy** (1-5): Are the suggestions and information correct?
- **Persona Alignment** (1-5): Does the response match the persona's style?
- **Goal Achievement** (1-5): Does the response advance the user's goals?
- **Accessibility** (1-5): How well does it accommodate accessibility needs?
- **Error Handling** (1-5): How gracefully does it handle invalid inputs?

**Calibration & Bias Prevention**:

- Regular sampling of scoring agent prompts
- Tuning rubric weights based on performance analysis
- Preventing bias against verbose but helpful responses
- Logging intermediate scores for regression detection

**Explainability**:

- Detailed scoring breakdown for each rubric category
- Specific examples of what worked and what didn't
- Confidence scores for each evaluation
- Historical comparison with previous runs

### 5. Evaluation Loop (`llm_testing/evaluation_loop.py`)

**Purpose**: Orchestrate the testing process and track results over time.

**Structure**:

```python
class EvaluationLoop:
    def __init__(self, assistant_client, scoring_agent, config: TestingConfig):
        self.assistant = assistant_client
        self.scorer = scoring_agent
        self.config = config
        self.results_db = ResultsDatabase(config.results_storage)
        self.ci_integration = CIIntegration()

    def run_scenario(self, scenario: Scenario) -> ScenarioResult:
        # Execute scenario with assistant
        # Evaluate responses with appropriate scoring tier
        # Store results with version tracking
        # Generate alerts for performance drops

    def run_batch(self, scenarios: List[Scenario]) -> BatchResult:
        # Run multiple scenarios in parallel
        # Aggregate results with statistical analysis
        # Generate insights and recommendations
        # Update dashboards and alerts

    def generate_report(self, results: BatchResult) -> EvaluationReport:
        # Create detailed report with trends
        # Identify regressions and improvements
        # Generate actionable recommendations
        # Update meta-tracker with insights
```

**CI/CD Integration**:

- **Nightly Runs**: Full test suite execution
- **PR Smoke Tests**: Lightweight tests on every pull request
- **Performance Alerts**: Automatic notifications for score drops
- **Dashboard Updates**: Real-time metric updates

**Dashboards & Alerts**:

- **Key Metrics**: Average score, failure rate, improvement trends
- **Threshold Alerts**: "Overall score dips below 3.5"
- **Regression Detection**: Automatic identification of performance drops
- **Success Rate Tracking**: Per-scenario and per-persona success rates

### 6. Meta-Tracker (`llm_testing/meta_tracker.py`)

**Purpose**: Track evolving insights from testing to shape roadmap and feature design.

**Structure**:

```python
class MetaTracker:
    def __init__(self, config: TestingConfig):
        self.insights_db = InsightsDatabase(config.insights_storage)
        self.trend_analyzer = TrendAnalyzer()
        self.issue_tracker = IssueTracker()
        self.version_tracker = VersionTracker()

    def track_insight(self, insight: Insight):
        # Store with version information
        # Update trend analysis
        # Generate actionable recommendations
        # Link to issue tracker when appropriate

    def generate_recommendations(self) -> List[Recommendation]:
        # Analyze patterns across tests
        # Identify priority improvements
        # Suggest feature enhancements
        # Create actionable tickets
```

**Insight Versioning**:

- Tag each insight with code version and model version
- Track when patterns first emerged
- Correlate insights with specific changes
- Maintain historical context for trend analysis

**Actionables**:

- Link high-confidence insights to backlog items
- Create automatic tickets for performance issues
- Prioritize improvements based on impact
- Track implementation of recommendations

**Insight Types**:

- **Performance Patterns**: Areas where the assistant consistently excels or struggles
- **User Experience Insights**: How different personas interact with the assistant
- **Feature Gaps**: Missing capabilities that would improve performance
- **Prompt Engineering**: How different prompt styles affect outcomes
- **Integration Opportunities**: Ways to better integrate with existing systems
- **Accessibility Insights**: How well the assistant serves diverse users
- **Language Support**: Effectiveness with varying language fluency

## Implementation Phases

### Phase 1: Foundation (Week 1)

- [ ] Create `llm_testing/` module structure
- [ ] Implement basic `Persona` and `Scenario` classes with diversity support
- [ ] Create initial set of 10 personas (including accessibility and challenge personas)
- [ ] Define 15 basic scenarios with ground-truth anchors
- [ ] Implement dynamic prompt generation with template system
- [ ] Create basic evaluation loop with CI/CD hooks
- [ ] Set up SQLite database for results storage

### Phase 2: Scoring System (Week 2)

- [ ] Implement `ScoringAgent` with mixed evaluation tiers
- [ ] Develop comprehensive evaluation rubric with calibration
- [ ] Create detailed feedback generation with explainability
- [ ] Add confidence scoring and uncertainty handling
- [ ] Implement batch evaluation capabilities
- [ ] Set up dashboard and alert system

### Phase 3: Advanced Scenarios (Week 3)

- [ ] Create complex, multi-step scenarios
- [ ] Add comprehensive edge case and error handling tests
- [ ] Implement persona-specific evaluation criteria
- [ ] Add integration tests with narrative memory
- [ ] Create scenario difficulty progression
- [ ] Implement accessibility and language testing

### Phase 4: Meta-Analysis (Week 4)

- [ ] Implement `MetaTracker` with version tracking
- [ ] Create automated insight generation with actionables
- [ ] Add recommendation engine with issue tracker integration
- [ ] Implement performance tracking over time
- [ ] Create automated reporting system
- [ ] Set up regression detection and alerts

## Technical Architecture

### File Structure

```
llm_testing/
├── __init__.py
├── personas.py          # Persona definitions with diversity
├── scenarios.py         # Scenario definitions with ground truth
├── prompts.py          # Test prompt management with templates
├── evaluator.py        # Scoring agent with mixed tiers
├── evaluation_loop.py  # Main evaluation orchestration
├── meta_tracker.py     # Insights and recommendations
├── config.py          # Configuration management
├── utils.py           # Utility functions
├── database.py        # SQLite database for results
├── dashboard.py       # Dashboard and alert system
└── tests/             # Framework tests
    ├── __init__.py
    ├── test_personas.py
    ├── test_scenarios.py
    ├── test_evaluator.py
    └── test_integration.py
```

### Configuration

```python
# llm_testing/config.py
@dataclass
class TestingConfig:
    scoring_model: str = "gpt-4"
    fallback_model: str = "gpt-3.5-turbo"
    max_tokens: int = 1000
    temperature: float = 0.1
    batch_size: int = 10
    evaluation_timeout: int = 30
    results_storage: str = "llm_testing/results.db"  # SQLite for performance
    insights_storage: str = "llm_testing/insights.db"
    dashboard_url: str = "http://localhost:3000"
    alert_threshold: float = 3.5
    ci_integration: bool = True
    version_tracking: bool = True
```

### Data Models

```python
# Core data structures
@dataclass
class EvaluationResult:
    scenario_name: str
    persona_name: str
    prompt: str
    assistant_response: str
    scores: Dict[str, float]
    intermediate_scores: Dict[str, List[float]]  # For regression tracking
    feedback: str
    timestamp: str
    code_version: str
    model_version: str
    metadata: Dict[str, Any]

@dataclass
class BatchResult:
    batch_id: str
    scenarios: List[Scenario]
    results: List[EvaluationResult]
    summary: Dict[str, Any]
    insights: List[str]
    performance_alerts: List[str]

@dataclass
class Insight:
    insight_type: str
    description: str
    confidence: float
    evidence: List[str]
    recommendations: List[str]
    timestamp: str
    code_version: str
    model_version: str
    linked_issues: List[str]  # Links to issue tracker
```

## Success Metrics

### Quantitative Metrics

- **Average Score**: Overall performance across all scenarios
- **Score Distribution**: How scores are distributed across categories
- **Improvement Rate**: How scores change over time
- **Scenario Success Rate**: Percentage of scenarios that meet success criteria
- **Response Time**: How quickly the assistant responds
- **Error Rate**: Frequency of failed or incorrect responses
- **Accessibility Score**: Performance with accessibility needs
- **Language Fluency Score**: Performance with varying language levels

### Qualitative Metrics

- **User Satisfaction**: How well responses align with user expectations
- **Persona Alignment**: How well responses match persona characteristics
- **Goal Achievement**: How effectively responses advance user goals
- **Clarity and Helpfulness**: Subjective quality assessments
- **Innovation**: How well the assistant handles novel situations
- **Inclusivity**: How well the assistant serves diverse users
- **Error Handling**: Gracefulness in handling invalid inputs

## Integration Points

### With Existing Systems

- **Core Memory**: Test how well the assistant uses narrative and core memory
- **Narrative Memory**: Evaluate theme and pattern recognition capabilities
- **EventKit Integration**: Test real calendar operations
- **Conversation Manager**: Evaluate multi-turn conversation handling

### Continuous Integration

- **Automated Testing**: Run tests on every PR with smoke tests
- **Performance Tracking**: Monitor scores over time with alerts
- **Alert System**: Notify when scores drop below thresholds
- **Report Generation**: Automated weekly/monthly reports
- **Dashboard**: Real-time metrics and trend visualization

## Open Questions

### Technical Questions

1. **Model Selection**: Which LLM should we use for scoring? (GPT-4, Claude, etc.)
2. **Cost Management**: How do we manage API costs for extensive testing?
3. **Rate Limiting**: How do we handle API rate limits during batch testing?
4. **Database vs JSON**: Should we use SQLite for results or stick to JSON files?
5. **Scalability**: How do we scale testing as the system grows?

### Strategic Questions

1. **Test Frequency**: How often should we run tests? (Daily, weekly, on PRs?)
2. **Scenario Evolution**: How do we evolve scenarios as the assistant improves?
3. **Persona Refinement**: How do we refine personas based on real user data?
4. **Success Thresholds**: What score thresholds indicate acceptable performance?
5. **Improvement Tracking**: How do we measure and track improvements over time?

### Integration Questions

1. **Real vs Synthetic**: Should we test with real user data or stick to synthetic?
2. **Feedback Loop**: How do we incorporate real user feedback into testing?
3. **A/B Testing**: How do we test different assistant configurations?
4. **Performance Impact**: How do we ensure testing doesn't impact production performance?

## Deliverables for V1

### Core Implementation

- [ ] `llm_testing/` module with all core components
- [ ] 10 well-defined personas with diversity and accessibility considerations
- [ ] 15 comprehensive test scenarios with ground-truth anchors
- [ ] GPT-4/GPT-3.5 mixed scoring system with detailed rubric
- [ ] Basic evaluation loop with CI/CD integration
- [ ] Initial meta-tracking capabilities with version tracking
- [ ] SQLite database for efficient results storage

### Documentation

- [ ] Comprehensive API documentation
- [ ] User guide for running tests
- [ ] Configuration guide
- [ ] Troubleshooting guide
- [ ] Best practices document
- [ ] Accessibility testing guide

### Testing Infrastructure

- [ ] Unit tests for all components
- [ ] Integration tests for the full pipeline
- [ ] Performance benchmarks
- [ ] Error handling tests
- [ ] Configuration validation
- [ ] Accessibility testing framework

### Initial Results

- [ ] Baseline performance metrics
- [ ] Initial insights and recommendations
- [ ] Performance comparison with existing systems
- [ ] Identified areas for improvement
- [ ] Roadmap for V2 enhancements
- [ ] Dashboard with key metrics

## Continuous Testing Integration Strategy

### Feature-Driven Testing Expansion

As we build new features, we should continuously expand our LLM testing coverage to ensure comprehensive evaluation of the assistant's capabilities.

#### **Integration Points for New Features**

**Core Memory & Narrative Memory**

- Test how well the assistant leverages historical context
- Evaluate pattern recognition and theme identification
- Assess memory retrieval accuracy and relevance
- Test memory-based personalization capabilities

**Conversation Management**

- Multi-turn conversation handling
- Context preservation across turns
- Reference resolution ("move it", "that meeting")
- Conversation state management

**EventKit Integration**

- Real calendar operation testing
- Event creation, modification, deletion
- Recurring event handling
- Calendar conflict resolution
- Timezone handling

**Edge Case Handling**

- Input normalization and validation
- Error recovery and graceful degradation
- Ambiguous request clarification
- Invalid input handling

**Accessibility Features**

- Screen reader compatibility
- Keyboard navigation support
- Voice command processing
- Alternative input methods

#### **Testing Integration Workflow**

1. **Feature Development Phase**

   - Identify new capabilities being added
   - Design test scenarios that exercise new features
   - Create personas that would benefit from new features
   - Define success criteria for new functionality

2. **Test Scenario Creation**

   - Add new scenarios to `llm_testing/scenarios.py`
   - Create personas that test new feature boundaries
   - Define ground-truth responses for new capabilities
   - Update scoring rubrics to include new criteria

3. **Integration Testing**

   - Test new features with existing personas
   - Verify backward compatibility
   - Ensure no regressions in existing functionality
   - Validate performance impact

4. **Continuous Monitoring**
   - Track performance of new features over time
   - Identify areas for improvement
   - Generate insights for feature refinement
   - Create issues for problematic areas

#### **Example: Adding Calendar Sharing Feature**

**New Test Scenarios:**

- "Share calendar with team member"
- "Collaborative scheduling with external users"
- "Permission management and access control"
- "Cross-platform calendar synchronization"

**New Personas:**

- **Team Lead**: Manages team calendar access
- **External Collaborator**: Needs limited calendar access
- **Administrator**: Manages calendar permissions

**New Evaluation Criteria:**

- Permission handling accuracy
- Security awareness
- Collaboration facilitation
- Cross-platform compatibility

#### **Automated Integration**

- **PR Testing**: Run relevant test scenarios on every PR
- **Feature Flags**: Test new features before full deployment
- **A/B Testing**: Compare different feature implementations
- **Performance Monitoring**: Track impact on overall assistant performance

## Future Enhancements (V2+)

### Advanced Capabilities

- **Multi-Modal Testing**: Test with images, voice, and other media
- **Real-Time Testing**: Continuous testing during live usage
- **Adaptive Scenarios**: Scenarios that evolve based on assistant performance
- **Cross-Language Testing**: Test in multiple languages
- **Advanced Accessibility Testing**: Comprehensive accessibility evaluation

### Advanced Analytics

- **Predictive Analytics**: Predict performance issues before they occur
- **Anomaly Detection**: Identify unusual patterns in assistant behavior
- **Trend Analysis**: Long-term performance trend analysis
- **Comparative Analysis**: Compare against other AI assistants
- **User Journey Testing**: End-to-end user experience testing

### Integration Enhancements

- **Real User Data Integration**: Incorporate real user interactions
- **Feedback Loop**: Automated improvement suggestions
- **A/B Testing Framework**: Test different assistant configurations
- **Performance Optimization**: Optimize testing for speed and cost
- **Distributed Testing**: Scale testing across multiple environments

## Conclusion

The LLM-to-LLM Testing Framework will provide a robust foundation for continuously improving the calendar assistant's capabilities. By systematically testing against realistic scenarios with diverse personas, we can ensure the assistant meets user needs effectively and consistently.

The framework's modular design allows for incremental implementation and continuous enhancement, while the meta-tracking capabilities ensure that insights from testing directly inform product development decisions. The integration of accessibility considerations, dynamic prompt generation, and mixed evaluation tiers ensures comprehensive testing coverage while maintaining cost efficiency.
