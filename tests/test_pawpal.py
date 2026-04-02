from datetime import date
from pawpal_system import User, Pet, Task


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
