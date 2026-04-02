from datetime import date


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


class Task:
    def __init__(self, name, description, due, pet, status="pending"):
        self.name = name
        self.description = description
        self.due = due
        self.pet = pet
        self.status = status

    def execute(self):
        self.status = "done"

    def cancel(self):
        self.status = "cancelled"


class Planner:
    def __init__(self, name, user):
        self.name = name
        self.user = user
        self.tasks = []

    def schedule_task(self, task):
        self.tasks.append(task)
        task.pet.tasks.append(task)

    def cancel_task(self, task):
        task.cancel()

    def get_tasks_for_today(self):
        today = date.today()
        return [t for t in self.tasks if t.due == today and t.status == "pending"]

    def make_plan(self):
        return self.get_tasks_for_today()


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
