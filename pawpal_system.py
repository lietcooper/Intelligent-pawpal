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


class Task:
    def __init__(self, name, description, due, pet, duration_minutes=30,
                 priority="medium", preferred_time=None, status="pending"):
        self.name = name
        self.description = description
        self.due = due
        self.pet = pet
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.preferred_time = preferred_time  # e.g. time(8, 0) for 8 AM
        self.status = status
        # Set after scheduling
        self.scheduled_start = None
        self.scheduled_end = None

    def execute(self):
        self.status = "done"

    def cancel(self):
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

    def schedule_task(self, task):
        self.tasks.append(task)
        task.pet.tasks.append(task)

    def cancel_task(self, task):
        task.cancel()

    def get_tasks_for_today(self):
        today = date.today()
        return [t for t in self.tasks if t.due == today and t.status == "pending"]

    def get_tasks_for_date(self, target_date):
        return [t for t in self.tasks if t.due == target_date and t.status == "pending"]

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
            """Find the earliest available slot starting at or after `earliest`."""
            cursor = earliest
            end_boundary = _dt(self.day_end)
            while cursor + timedelta(minutes=duration_minutes) <= end_boundary:
                candidate_end = cursor + timedelta(minutes=duration_minutes)
                if not _conflicts(cursor, candidate_end):
                    return cursor
                # Jump past the conflicting block
                for occ_start, occ_end in sorted(occupied):
                    if cursor < occ_end and candidate_end > occ_start:
                        cursor = occ_end
                        break
                else:
                    cursor += timedelta(minutes=5)
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
        pet.owner = self
        self.pets.append(pet)

    def schedule_task(self, task):
        self.planner.schedule_task(task)

    def execute_task(self, task):
        task.execute()
