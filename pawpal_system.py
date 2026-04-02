class Pet:
    def __init__(self, pet_id, pet_name, owner, sex, age, species, breed):
        self.pet_id = pet_id
        self.pet_name = pet_name
        self.owner = owner
        self.sex = sex
        self.age = age
        self.species = species
        self.breed = breed


class Task:
    def __init__(self, name, description, due, status="pending"):
        self.name = name
        self.description = description
        self.due = due
        self.status = status


class Planner:
    def __init__(self, name):
        self.name = name

    def make_plan(self):
        pass


class User:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.pets = []

    def add_pet(self, pet):
        pass

    def schedule_task(self, task):
        pass

    def execute_task(self, task):
        pass
