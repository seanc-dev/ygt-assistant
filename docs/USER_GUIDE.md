# Calendar Assistant User Guide

## 🚀 Getting Started

### **Installation**

1. **Clone the repository**:

```bash
git clone https://github.com/seanc-dev/coach-flow-app.git
cd coach-flow-app
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

3. **Set up environment**:

```bash
cp env.production.sample .env
# Fill in provider API keys and settings
```

4. **Run the API (dev)**:

```bash
uvicorn presentation.api.app:app --reload
```

## 🎯 Basic Usage

### **Starting a Session**

```bash
python main.py
```

You'll see:

```
Welcome to the Terminal Calendar Assistant! Type 'exit' to quit.

>
```

### **Basic Commands**

#### **View Your Calendar**

```
> show my events
> what's on today?
> list my schedule
```

#### **Schedule Events**

```
> schedule team meeting tomorrow at 2pm
> create lunch meeting with John on Friday
> book 30-minute call with client next Tuesday
```

#### **Manage Events**

```
> delete team meeting
> move lunch to 1pm
> reschedule call to next week
```

#### **View Reminders**

```
> show my reminders
> list my tasks
> what do I need to do today?
```

## 🧠 Advanced Features

### **Natural Language Understanding**

The assistant understands natural language and handles:

#### **Misspellings**

```
> shedule meeting tomorrow    # → schedules meeting
> delet team meeting         # → deletes team meeting
> calender events           # → calendar events
```

#### **Poor Grammar**

```
> meeting tomorrow at 2pm I need    # → extracts "meeting tomorrow at 2pm"
> schedule meeting for tomorrow please  # → schedules meeting
> I want to have a meeting          # → schedules meeting
```

#### **Ambiguous References**

```
> schedule team meeting tomorrow
> move it to 3pm                    # → knows "it" refers to the team meeting
```

### **Conversation Context**

The assistant remembers your conversation:

```
> schedule team meeting tomorrow at 10am
✅ Event created successfully

> move it to 2pm
✅ Event moved successfully

> delete that meeting
✅ Event deleted successfully
```

### **Smart Suggestions**

The assistant learns your patterns:

```
> schedule my usual Tuesday check-in
✅ Found similar past event: "Weekly Check-in with Boss" (Tuesdays at 10am)
✅ Event created successfully
```

## 📅 Calendar Operations

### **Creating Events**

#### **Basic Event Creation**

```
> schedule team meeting tomorrow at 2pm
```

#### **With Duration**

```
> schedule 30-minute standup tomorrow at 9am
> create 2-hour project review on Friday
```

#### **With Location**

```
> schedule meeting in conference room A tomorrow
> create lunch at the office cafeteria
```

#### **With Attendees**

```
> schedule meeting with John and Sarah tomorrow
> create team sync with engineering team
```

#### **Recurring Events**

```
> schedule daily standup every weekday at 9am
> create weekly team meeting every Monday
> schedule monthly review on the first Friday
```

### **Managing Events**

#### **Moving Events**

```
> move team meeting to 3pm
> reschedule lunch to tomorrow
> shift call to next week
```

#### **Deleting Events**

```
> delete team meeting
> cancel lunch
> remove that meeting
```

#### **Finding Events**

```
> show my meetings today
> list events for tomorrow
> what's on my calendar this week?
```

### **Reminders and Tasks**

#### **Viewing Reminders**

```
> show my reminders
> list my tasks
> what do I need to do?
```

#### **Creating Reminders**

```
> remind me to call John tomorrow
> add task to review budget
> create reminder to follow up with client
```

## 🎯 Pro Tips

### **Time References**

The assistant understands various time formats:

#### **Relative Times**

```
> tomorrow
> next week
> in 3 days
> this weekend
```

#### **Specific Times**

```
> 2pm
> 14:00
> noon
> midnight
```

#### **Date Formats**

```
> January 15th
> 2024-01-15
> next Monday
> this Friday
```

### **Natural Language Patterns**

#### **Intent Recognition**

```

```
