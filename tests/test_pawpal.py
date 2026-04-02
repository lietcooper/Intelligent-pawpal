from datetime import date, time, datetime, timedelta
from pawpal_system import User, Pet, Task, Planner


def test_task_completion():
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    task = Task("Walk", "Morning walk", date.today(), pet)

    assert task.status == "pending"
    task.execute()
    assert task.status == "done"


def test_task_cancellation():
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    task = Task("Walk", "Morning walk", date.today(), pet)

    assert task.status == "pending"
    task.cancel()
    assert task.status == "cancelled"


def test_task_addition_increases_pet_task_count():
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    user.add_pet(pet)

    assert len(pet.tasks) == 0

    task1 = Task("Walk", "Morning walk", date.today(), pet)
    user.schedule_task(task1)
    assert len(pet.tasks) == 1

    task2 = Task("Feed", "Breakfast", date.today(), pet)
    user.schedule_task(task2)
    assert len(pet.tasks) == 2


# ---------------------------------------------------------------------------
# Recurring tasks
# ---------------------------------------------------------------------------

def test_recurring_daily_spawns_next_task():
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    today = date.today()
    task = Task("Walk", "Morning walk", today, pet, recurrence="daily")
    user.schedule_task(task)

    next_task = user.execute_task(task)

    assert next_task is not None
    assert next_task.due == today + timedelta(days=1)
    assert next_task in user.planner.tasks


def test_recurring_weekly_spawns_next_task():
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    today = date.today()
    task = Task("Bath", "Weekly bath", today, pet, recurrence="weekly")
    user.schedule_task(task)

    next_task = user.execute_task(task)

    assert next_task is not None
    assert next_task.due == today + timedelta(weeks=1)


def test_recurring_task_inherits_fields():
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    today = date.today()
    task = Task("Walk", "Morning walk", today, pet,
                duration_minutes=45, priority="high",
                preferred_time=time(8, 0), recurrence="daily")
    user.schedule_task(task)

    next_task = user.execute_task(task)

    assert next_task.duration_minutes == 45
    assert next_task.priority == "high"
    assert next_task.preferred_time == time(8, 0)
    assert next_task.recurrence == "daily"


def test_non_recurring_complete_returns_none():
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    task = Task("Walk", "Morning walk", date.today(), pet, recurrence=None)
    user.schedule_task(task)

    result = user.execute_task(task)

    assert result is None


def test_recurring_month_rollover():
    """Completing a daily task on the last day of a month rolls due date correctly."""
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    last_day = date(2024, 1, 31)
    task = Task("Walk", "Morning walk", last_day, pet, recurrence="daily")
    user.schedule_task(task)

    next_task = user.execute_task(task)

    assert next_task.due == date(2024, 2, 1)


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_conflict_same_pet_same_time():
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    today = date.today()
    t1 = Task("Walk", "Walk", today, pet, duration_minutes=60, preferred_time=time(9, 0))
    t2 = Task("Bath", "Bath", today, pet, duration_minutes=60, preferred_time=time(9, 0))
    user.schedule_task(t1)

    warning = user.schedule_task(t2)

    assert warning is not None
    assert "same pet" in warning


def test_conflict_cross_pet_overlap():
    user = User("u1", "Jordan")
    pet1 = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    pet2 = Pet("p2", "Luna", user, "female", 2, "cat", "Ragdoll")
    today = date.today()
    t1 = Task("Walk", "Walk", today, pet1, duration_minutes=60, preferred_time=time(9, 0))
    t2 = Task("Feed", "Feed", today, pet2, duration_minutes=30, preferred_time=time(9, 15))
    user.schedule_task(t1)

    warning = user.schedule_task(t2)

    assert warning is not None
    assert "different pet" in warning


def test_no_conflict_different_dates():
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    today = date.today()
    tomorrow = today + timedelta(days=1)
    t1 = Task("Walk", "Walk", today, pet, duration_minutes=60, preferred_time=time(9, 0))
    t2 = Task("Walk", "Walk", tomorrow, pet, duration_minutes=60, preferred_time=time(9, 0))
    user.schedule_task(t1)

    warning = user.schedule_task(t2)

    assert warning is None


def test_no_conflict_adjacent_tasks():
    """Tasks that share a boundary (end == start) should NOT conflict."""
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    today = date.today()
    t1 = Task("Walk", "Walk", today, pet, duration_minutes=60, preferred_time=time(9, 0))
    t2 = Task("Feed", "Feed", today, pet, duration_minutes=30, preferred_time=time(10, 0))
    user.schedule_task(t1)

    warning = user.schedule_task(t2)

    assert warning is None


def test_done_task_not_flagged_as_conflict():
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    today = date.today()
    t1 = Task("Walk", "Walk", today, pet, duration_minutes=60, preferred_time=time(9, 0))
    user.schedule_task(t1)
    t1.execute()  # mark done

    t2 = Task("Bath", "Bath", today, pet, duration_minutes=60, preferred_time=time(9, 0))
    warning = user.schedule_task(t2)

    assert warning is None


def test_find_conflicts_mixed_preferred_and_scheduled():
    """find_conflicts only checks scheduled_start; preferred_time-only tasks are skipped."""
    planner = Planner("p", None)
    pet = Pet("p1", "Mochi", None, "female", 3, "dog", "Shiba Inu")
    today = date.today()

    t1 = Task("Walk", "Walk", today, pet, duration_minutes=60)
    t1.scheduled_start = datetime.combine(today, time(9, 0))
    t1.scheduled_end = t1.scheduled_start + timedelta(minutes=60)

    t2 = Task("Bath", "Bath", today, pet, duration_minutes=60)
    t2.scheduled_start = datetime.combine(today, time(9, 30))
    t2.scheduled_end = t2.scheduled_start + timedelta(minutes=60)

    t3 = Task("Feed", "Feed", today, pet, duration_minutes=30, preferred_time=time(9, 0))
    # t3 has no scheduled_start — should be ignored by find_conflicts

    planner.tasks = [t1, t2, t3]
    conflicts = planner.find_conflicts()

    assert len(conflicts) == 1
    assert {conflicts[0]["task_a"], conflicts[0]["task_b"]} == {t1, t2}


# ---------------------------------------------------------------------------
# sort_by_time
# ---------------------------------------------------------------------------

def test_sort_by_time_three_tiers():
    """scheduled_start < preferred_time-only < no time."""
    planner = Planner("p", None)
    pet = Pet("p1", "Mochi", None, "female", 3, "dog", "Shiba Inu")
    today = date.today()

    t_scheduled = Task("Walk", "", today, pet)
    t_scheduled.scheduled_start = datetime.combine(today, time(8, 0))
    t_scheduled.scheduled_end = t_scheduled.scheduled_start + timedelta(minutes=30)

    t_preferred = Task("Feed", "", today, pet, preferred_time=time(10, 0))

    t_none = Task("Groom", "", today, pet)

    planner.tasks = [t_none, t_preferred, t_scheduled]
    result = planner.sort_by_time()

    assert result[0] is t_scheduled
    assert result[1] is t_preferred
    assert result[2] is t_none


# ---------------------------------------------------------------------------
# make_plan
# ---------------------------------------------------------------------------

def test_make_plan_empty_returns_empty():
    user = User("u1", "Jordan")
    scheduled, explanations = user.planner.make_plan(date.today())
    assert scheduled == []
    assert explanations == []


def test_make_plan_preferred_time_honored():
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    today = date.today()
    task = Task("Walk", "Walk", today, pet, duration_minutes=30,
                priority="medium", preferred_time=time(9, 0))
    user.schedule_task(task)

    scheduled, _ = user.planner.make_plan(today)

    assert len(scheduled) == 1
    assert scheduled[0].scheduled_start == datetime.combine(today, time(9, 0))


def test_make_plan_conflict_falls_back_to_next_slot():
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    today = date.today()
    t1 = Task("Walk", "Walk", today, pet, duration_minutes=60, preferred_time=time(9, 0))
    t2 = Task("Bath", "Bath", today, pet, duration_minutes=30, preferred_time=time(9, 0))
    user.schedule_task(t1)
    user.schedule_task(t2)

    scheduled, explanations = user.planner.make_plan(today)

    assert len(scheduled) == 2
    # t2 must not overlap t1
    assert scheduled[0].scheduled_end <= scheduled[1].scheduled_start
    assert any("moved to next slot" in e for e in explanations)


def test_make_plan_task_beyond_day_end_not_scheduled():
    planner = Planner("p", None, day_start=time(7, 0), day_end=time(8, 0))
    pet = Pet("p1", "Mochi", None, "female", 3, "dog", "Shiba Inu")
    today = date.today()
    # 90-minute task in a 60-minute window — no slot fits
    task = Task("LongWalk", "Walk", today, pet, duration_minutes=90)
    task.status = "pending"
    planner.tasks = [task]

    scheduled, _ = planner.make_plan(today)

    assert task not in scheduled


def test_make_plan_flexible_tasks_sorted_by_priority():
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    today = date.today()
    low = Task("Groom", "Groom", today, pet, duration_minutes=30, priority="low")
    high = Task("Vet", "Vet", today, pet, duration_minutes=30, priority="high")
    user.schedule_task(low)
    user.schedule_task(high)

    scheduled, _ = user.planner.make_plan(today)

    assert scheduled[0] is high
    assert scheduled[1] is low
