from datetime import date, time
from pawpal_system import User, Pet, Task


def main():
    # Create user
    user = User("u1", "Jordan")

    # Create two pets
    mochi = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    whiskers = Pet("p2", "Whiskers", user, "male", 5, "cat", "Maine Coon")
    user.add_pet(mochi)
    user.add_pet(whiskers)

    today = date.today()

    # Mochi's tasks
    user.schedule_task(Task("Morning walk", "Walk Mochi around the park", today, mochi,
                            duration_minutes=30, priority="high", preferred_time=time(7, 30)))
    user.schedule_task(Task("Breakfast", "Feed Mochi kibble and wet food", today, mochi,
                            duration_minutes=15, priority="high", preferred_time=time(8, 0)))
    user.schedule_task(Task("Play fetch", "Fetch session in the yard", today, mochi,
                            duration_minutes=25, priority="medium"))

    # Whiskers' tasks
    user.schedule_task(Task("Litter box cleanup", "Clean Whiskers' litter box", today, whiskers,
                            duration_minutes=10, priority="high", preferred_time=time(7, 0)))
    user.schedule_task(Task("Vet checkup", "Annual vaccination for Whiskers", today, whiskers,
                            duration_minutes=60, priority="high", preferred_time=time(10, 0)))
    user.schedule_task(Task("Grooming", "Brush Whiskers' coat", today, whiskers,
                            duration_minutes=20, priority="low"))

    # Generate and print the plan
    scheduled, explanations = user.planner.make_plan(today)

    print("=" * 50)
    print(f"  Today's Schedule for {user.username}")
    print(f"  Date: {today.strftime('%A, %B %d, %Y')}")
    print(f"  Pets: {', '.join(p.pet_name for p in user.pets)}")
    print("=" * 50)
    for line in explanations:
        print(f"  {line}")
    print("=" * 50)
    print(f"  Total tasks: {len(scheduled)}")
    print("=" * 50)


if __name__ == "__main__":
    main()
