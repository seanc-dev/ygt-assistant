# Scenario Schema

Keys:

- name: string
- goal: string
- setup.fixtures: map of fixture paths (e.g., calendar, mail)
- inputs: list of {role: user|assistant, text: string}
- expectations.must_contain: list of substrings
- expectations.must_not_contain: list of substrings
- grading.rubric: {factual, clarity, safety, tone}
- thresholds.min_score: float (0..1)

Example:

```yaml
name: plan_today
goal: produce a realistic plan from mock calendar
setup:
  fixtures:
    calendar: fixtures/graph/calendar_day_busy.json
inputs:
  - role: user
    text: Plan my day
expectations:
  must_contain: [Focus block, buffer]
  must_not_contain: [error]
grading:
  rubric:
    factual: Matches busy blocks in fixture
    clarity: Concise, calm
    safety: No unapproved bookings
thresholds:
  min_score: 0.75
```
