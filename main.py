from datetime import date, time
from pawpal_system import User, Pet, Task


def main():
    user = User("u1", "Jordan")

    mochi    = Pet("p1", "Mochi",    user, "female", 3, "dog", "Shiba Inu")
    whiskers = Pet("p2", "Whiskers", user, "male",   5, "cat", "Maine Coon")
    user.add_pet(mochi)
    user.add_pet(whiskers)

    today = date.today()

    warnings = []

    def add(task):
        w = user.schedule_task(task)
        if w:
            warnings.append(w)

    # --- Normal tasks (no conflicts expected) ---
    add(Task("Litter box cleanup", "Clean Whiskers' litter box", today, whiskers,
             duration_minutes=10, priority="high", preferred_time=time(7, 0), recurrence="daily"))
    add(Task("Morning walk", "Walk Mochi around the park", today, mochi,
             duration_minutes=30, priority="high", preferred_time=time(7, 30), recurrence="daily"))
    add(Task("Breakfast", "Feed Mochi kibble and wet food", today, mochi,
             duration_minutes=15, priority="high", preferred_time=time(8, 0), recurrence="daily"))
    add(Task("Vet checkup", "Annual vaccination for Whiskers", today, whiskers,
             duration_minutes=60, priority="high", preferred_time=time(10, 0)))
    add(Task("Play fetch", "Fetch session in the yard", today, mochi,
             duration_minutes=25, priority="medium"))
    add(Task("Grooming", "Brush Whiskers' coat", today, whiskers,
             duration_minutes=20, priority="low", recurrence="weekly"))

    # --- Two tasks at the same time (same pet and cross-pet) ---
    add(Task("Second walk",  "Extra Mochi walk",      today, mochi,    # same-pet: overlaps Morning walk
             duration_minutes=20, priority="low",    preferred_time=time(7, 30)))
    add(Task("Vet recheck",  "Whiskers follow-up",    today, whiskers, # cross-pet: overlaps Vet checkup
             duration_minutes=30, priority="medium", preferred_time=time(10, 15)))

    # --- Print warnings ---
    print("=" * 50)
    print("  Scheduling warnings")
    print("=" * 50)
    if warnings:
        for w in warnings:
            print(f"  {w}")
    else:
        print("  No warnings.")

    # --- Build and print the day's schedule ---
    scheduled, explanations = user.planner.make_plan(today)

    print()
    print("=" * 50)
    print(f"  Today's Schedule — {today.strftime('%A, %B %d, %Y')}")
    print("=" * 50)
    for line in explanations:
        print(f"  {line}")
    print(f"\n  Total tasks scheduled: {len(scheduled)}")
    print("=" * 50)


if __name__ == "__main__":
    main()
