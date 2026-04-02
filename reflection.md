# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**
- Briefly describe your initial UML design.
  - Potential actions:
    - add a pet
    - schedule a task
    - cancel a task
    - view today's tasks
  - Objects:
    - User
      - user_id
      - username
      - pets
      - add_pet()
      - schedule_task()
      - execute_task()
    - Pet
      - pet_id
      - pet_name
      - owner
      - sex
      - age
      - species
      - breed
    - Task
      - name
      - description
      - due
      - status
    - Planner
      - name
      - make_plan()

- What classes did you include, and what responsibilities did you assign to each?
  - The initial design contains four classes. `User` is the user of the application and the owner of the pets, with the accessibility to manage pets and pets' tasks. `Pet` is the pets. `Task` is the differente tasks to be scheduled and executed. `Planner` is the object that makes everyday's plan for pets.

**b. Design changes**

- Did your design change during implementation?
  - Yes
- If yes, describe at least one change and why you made it.
  1. Pet now tracks its own tasks — added a self.tasks list so you can see all tasks associated with a specific pet.                         
  2. Task now references a pet — added a pet parameter so every task knows which pet it belongs to, and gained execute() and cancel() methods to manage its own status instead of relying on User. 
  3. Planner is now the single source of truth for scheduling — it holds the master self.tasks list, owns schedule_task() and cancel_task(), and provides get_tasks_for_today() to query pending tasks by date. It also takes a user reference so it knows who it's planning for.
  4. User delegates to Planner — User automatically creates a Planner on init and schedule_task() now forwards to self.planner.schedule_task(). execute_task() calls task.execute() directly since execution is just a status change on the task itself.      

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.$$
- Why is that tradeoff reasonable for this scenario?

 _conflict_warning (lightweight, at add-time)
```
┌──────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐  │         Tradeoff         │                                                                     Detail                                                                     │  ├──────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Preferred time as a      │ Uses preferred_time + duration as the interval — but make_plan may place the task somewhere else entirely, so a warning can be a false         │
│ proxy                    │ positive                                                                                                                                       │  ├──────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ First conflict only      │ Returns on the first overlap found, so a task clashing with two others only reports one warning                                                │  ├──────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ No cross-date awareness  │ Skips tasks on different due dates, so a task ending at 11:59 PM won't warn against one starting at midnight the next day                      │  ├──────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Advisory, not blocking   │ The task is always added; callers that ignore the return value silently lose the warning                                                       │  └──────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```
  find_conflicts (exhaustive, post-schedule)

  ```
┌──────────────────────┬───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │       Tradeoff       │                                                      Detail                                                       │
  ├──────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ O(n²) pairwise scan  │ Every task is compared against every other — fine for a handful of pets/tasks, but grows quadratically with scale │
  ├──────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ scheduled_start only │ Skips any task without a confirmed slot, so unscheduled tasks are invisible to it                                 │
  ├──────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ No severity ranking  │ All conflicts are equal; a 5-minute overlap and a full-day double-book look the same in the output                │
  └──────────────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
  ```
  _find_slot (greedy scheduler)

  ```
┌────────────────────────────────┬──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │            Tradeoff            │                                                                  Detail                                                                  │
  ├────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Greedy, not optimal            │ Takes the first open slot after earliest — doesn't look ahead to find a placement that creates less fragmentation                        │
  ├────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Preferred times are            │ A preferred-time task that can't fit is silently rescheduled; there's no way to distinguish "I really need 8 AM" from "8 AM is nice to   │
  │ best-effort                    │ have"                                                                                                                                    │
  ├────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ No buffer between tasks        │ Slots are packed end-to-end with zero travel or transition time between them                                                             │
  └────────────────────────────────┴──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
  ```

  The core tension is speed vs. accuracy: _conflict_warning is cheap and early but works on hints, while find_conflicts is accurate but only useful after the full plan is built.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
