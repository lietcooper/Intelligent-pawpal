from datetime import date, time, datetime, timedelta


PRIORITY_WEIGHT = {"high": 3, "medium": 2, "low": 1}


class Pet:
    def __init__(self, pet_id, pet_name, owner, sex, age, species, breed):
        self.pet_id = pet_id
        self.pet_name = pet_name
        self.owner = owner
        self.sex = sex
        self.age = age
        self.species = species
        self.breed = breed
        self.tasks = []

    def __repr__(self):
        return f"Pet({self.pet_name}, {self.species}/{self.breed})"


RECURRENCE_DELTA = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


class Task:
    def __init__(self, name, description, due, pet, duration_minutes=30,
                 priority="medium", preferred_time=None, status="pending",
                 recurrence=None):
        self.name = name
        self.description = description
        self.due = due
        self.pet = pet
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.preferred_time = preferred_time  # e.g. time(8, 0) for 8 AM
        self.status = status
        self.recurrence = recurrence  # None | "daily" | "weekly"
        # Set after scheduling
        self.scheduled_start = None
        self.scheduled_end = None

    def execute(self):
        """Mark the task as done."""
        self.status = "done"

    def cancel(self):
        """Mark the task as cancelled."""
        self.status = "cancelled"

    def __repr__(self):
        return f"Task({self.name}, {self.priority}, {self.duration_minutes}min)"


class Planner:
    def __init__(self, name, user, day_start=time(7, 0), day_end=time(21, 0)):
        self.name = name
        self.user = user
        self.tasks = []
        self.day_start = day_start
        self.day_end = day_end

    def _conflict_warning(self, task):
        """Return a warning string if task overlaps an existing task, else None.

        Uses preferred_time + duration as the interval when scheduled_start is
        not yet set. O(n) scan — intentionally lightweight, never raises.
        """
        if task.scheduled_start is not None:
            new_start, new_end = task.scheduled_start, task.scheduled_end
        elif task.preferred_time is not None:
            new_start = datetime.combine(task.due, task.preferred_time)
            new_end = new_start + timedelta(minutes=task.duration_minutes)
        else:
            return None  # no time info to compare

        for existing in self.tasks:
            if existing.due != task.due or existing.status in ("done", "cancelled"):
                continue
            if existing.scheduled_start is not None:
                ex_start, ex_end = existing.scheduled_start, existing.scheduled_end
            elif existing.preferred_time is not None:
                ex_start = datetime.combine(existing.due, existing.preferred_time)
                ex_end = ex_start + timedelta(minutes=existing.duration_minutes)
            else:
                continue

            if new_start < ex_end and new_end > ex_start:
                kind = "same pet" if task.pet is existing.pet else "different pet"
                return (
                    f"Warning: '{task.name}' "
                    f"({new_start.strftime('%I:%M %p')}-{new_end.strftime('%I:%M %p')}) "
                    f"conflicts with '{existing.name}' "
                    f"({ex_start.strftime('%I:%M %p')}-{ex_end.strftime('%I:%M %p')}) "
                    f"[{kind}]"
                )
        return None

    def schedule_task(self, task):
        """Add a task to the planner and its associated pet.

        Returns a warning string if a time conflict is detected, else None.
        The task is always added regardless — callers decide what to do with
        the warning.
        """
        warning = self._conflict_warning(task)
        self.tasks.append(task)
        task.pet.tasks.append(task)
        return warning

    def cancel_task(self, task):
        """Cancel a scheduled task."""
        task.cancel()

    def complete_task(self, task):
        """Mark a task done and auto-schedule the next occurrence for recurring tasks.

        Returns the newly created Task if recurrence fired, otherwise None.
        """
        task.execute()
        delta = RECURRENCE_DELTA.get(task.recurrence)
        if delta is None:
            return None
        next_task = Task(
            name=task.name,
            description=task.description,
            due=task.due + delta,
            pet=task.pet,
            duration_minutes=task.duration_minutes,
            priority=task.priority,
            preferred_time=task.preferred_time,
            recurrence=task.recurrence,
        )
        self.schedule_task(next_task)
        return next_task

    def find_conflicts(self, tasks=None):
        """Return all overlapping task pairs among scheduled tasks.

        Checks both same-pet and cross-pet overlaps. Only tasks with a
        scheduled_start are considered (unscheduled tasks are skipped).

        Args:
            tasks: list of Task objects to check. Defaults to all planner tasks.

        Returns:
            list of dicts, each with keys:
                "task_a", "task_b"  — the two conflicting tasks
                "overlap"           — "same_pet" | "cross_pet"
        """
        source = [t for t in (self.tasks if tasks is None else tasks)
                  if t.scheduled_start is not None]
        conflicts = []
        for i in range(len(source)):
            for j in range(i + 1, len(source)):
                a, b = source[i], source[j]
                if a.scheduled_start < b.scheduled_end and a.scheduled_end > b.scheduled_start:
                    conflicts.append({
                        "task_a": a,
                        "task_b": b,
                        "overlap": "same_pet" if a.pet is b.pet else "cross_pet",
                    })
        return conflicts

    def get_tasks_for_today(self):
        """Return all pending tasks due today."""
        today = date.today()
        return [t for t in self.tasks if t.due == today and t.status == "pending"]

    def get_tasks_for_date(self, target_date):
        """Return all pending tasks for a specific date."""
        return [t for t in self.tasks if t.due == target_date and t.status == "pending"]

    def sort_by_time(self, tasks=None):
        """Return tasks sorted by scheduled_start, falling back to preferred_time.

        Args:
            tasks: list of Task objects to sort. Defaults to all planner tasks.

        Tasks with no time set are placed at the end, ordered by priority.
        """
        source = self.tasks if tasks is None else tasks

        def _sort_key(task):
            if task.scheduled_start is not None:
                return (0, task.scheduled_start)
            if task.preferred_time is not None:
                return (1, datetime.combine(task.due, task.preferred_time))
            return (2, datetime.max)

        return sorted(source, key=_sort_key)

    def make_plan(self, target_date=None):
        """Build a time-ordered schedule for the given date.

        Strategy:
        1. Collect all pending tasks for the date.
        2. Sort by priority (high first), then by preferred_time if set.
        3. Assign time slots greedily, respecting preferred times when possible.
        4. Return the ordered list of scheduled tasks and a plan summary.
        """
        if target_date is None:
            target_date = date.today()

        pending = self.get_tasks_for_date(target_date)
        if not pending:
            return [], []

        # Separate tasks with and without preferred times
        preferred = [t for t in pending if t.preferred_time is not None]
        flexible = [t for t in pending if t.preferred_time is None]

        # Sort preferred tasks by their preferred time
        preferred.sort(key=lambda t: t.preferred_time)
        # Sort flexible tasks by priority (high first)
        flexible.sort(key=lambda t: PRIORITY_WEIGHT.get(t.priority, 0), reverse=True)

        scheduled = []
        explanations = []
        occupied = []  # list of (start_dt, end_dt) tuples

        def _dt(t):
            return datetime.combine(target_date, t)

        def _conflicts(start, end):
            for occ_start, occ_end in occupied:
                if start < occ_end and end > occ_start:
                    return True
            return False

        def _find_slot(duration_minutes, earliest):
            """Find the earliest available slot starting at or after `earliest`.

            Single linear scan over sorted occupied intervals — O(n) per call
            instead of re-sorting on every conflict.
            """
            cursor = earliest
            duration = timedelta(minutes=duration_minutes)
            end_boundary = _dt(self.day_end)

            for occ_start, occ_end in sorted(occupied):
                if occ_end <= cursor:
                    continue  # entirely before cursor, skip
                if cursor + duration <= occ_start:
                    break     # gap before this block is wide enough
                cursor = occ_end  # overlap: push past this block

            if cursor + duration <= end_boundary:
                return cursor
            return None

        # Phase 1: schedule preferred-time tasks
        for task in preferred:
            desired_start = _dt(task.preferred_time)
            desired_end = desired_start + timedelta(minutes=task.duration_minutes)

            if not _conflicts(desired_start, desired_end) and desired_end <= _dt(self.day_end):
                task.scheduled_start = desired_start
                task.scheduled_end = desired_end
                occupied.append((desired_start, desired_end))
                scheduled.append(task)
                explanations.append(
                    f"{task.scheduled_start.strftime('%I:%M %p')} - "
                    f"{task.scheduled_end.strftime('%I:%M %p')}: "
                    f"{task.name} for {task.pet.pet_name} "
                    f"[{task.priority} priority] — scheduled at preferred time"
                )
            else:
                # Preferred time unavailable, fall back to next available slot
                slot = _find_slot(task.duration_minutes, _dt(self.day_start))
                if slot:
                    task.scheduled_start = slot
                    task.scheduled_end = slot + timedelta(minutes=task.duration_minutes)
                    occupied.append((task.scheduled_start, task.scheduled_end))
                    scheduled.append(task)
                    explanations.append(
                        f"{task.scheduled_start.strftime('%I:%M %p')} - "
                        f"{task.scheduled_end.strftime('%I:%M %p')}: "
                        f"{task.name} for {task.pet.pet_name} "
                        f"[{task.priority} priority] — preferred time conflict, moved to next slot"
                    )

        # Phase 2: schedule flexible tasks by priority
        for task in flexible:
            slot = _find_slot(task.duration_minutes, _dt(self.day_start))
            if slot:
                task.scheduled_start = slot
                task.scheduled_end = slot + timedelta(minutes=task.duration_minutes)
                occupied.append((task.scheduled_start, task.scheduled_end))
                scheduled.append(task)
                explanations.append(
                    f"{task.scheduled_start.strftime('%I:%M %p')} - "
                    f"{task.scheduled_end.strftime('%I:%M %p')}: "
                    f"{task.name} for {task.pet.pet_name} "
                    f"[{task.priority} priority] — scheduled by priority"
                )

        # Sort final schedule by start time
        order = sorted(range(len(scheduled)), key=lambda i: scheduled[i].scheduled_start)
        scheduled = [scheduled[i] for i in order]
        explanations = [explanations[i] for i in order]

        return scheduled, explanations


class User:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.pets = []
        self.planner = Planner(f"{username}_planner", self)

    def add_pet(self, pet):
        """Register a pet under this user."""
        pet.owner = self
        self.pets.append(pet)

    def schedule_task(self, task):
        """Delegate task scheduling to the planner.

        Returns a warning string if a time conflict is detected, else None.
        """
        return self.planner.schedule_task(task)

    def execute_task(self, task):
        """Mark a task as completed, spawning the next occurrence if recurring."""
        return self.planner.complete_task(task)
