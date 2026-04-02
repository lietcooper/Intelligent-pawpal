import streamlit as st
from datetime import date, time
from pawpal_system import User, Pet, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# --- Session state: persist objects across reruns ---
if "user" not in st.session_state:
    st.session_state.user = User("u1", "Jordan")

if "pets" not in st.session_state:
    st.session_state.pets = {}  # pet_name -> Pet

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "schedule" not in st.session_state:
    st.session_state.schedule = None

user = st.session_state.user

# --- Header ---
st.title("🐾 PawPal+")
st.caption("A pet care planning assistant that schedules your pet's day.")

st.divider()

# --- Owner setup ---
st.subheader("Owner")
owner_name = st.text_input("Owner name", value=user.username)
if owner_name != user.username:
    user.username = owner_name

# --- Pet management ---
st.subheader("Pets")

col1, col2, col3, col4 = st.columns(4)
with col1:
    new_pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    breed = st.text_input("Breed", value="Shiba Inu")
with col4:
    age = st.number_input("Age", min_value=0, max_value=30, value=3)

if st.button("Add pet"):
    if new_pet_name and new_pet_name not in st.session_state.pets:
        pet_id = f"p{len(st.session_state.pets) + 1}"
        pet = Pet(pet_id, new_pet_name, user, "unknown", age, species, breed)
        user.add_pet(pet)
        st.session_state.pets[new_pet_name] = pet
        st.success(f"Added {new_pet_name}!")
    elif new_pet_name in st.session_state.pets:
        st.warning(f"{new_pet_name} already exists.")

if st.session_state.pets:
    st.write("Your pets:")
    pet_data = [
        {"Name": p.pet_name, "Species": p.species, "Breed": p.breed, "Age": p.age}
        for p in st.session_state.pets.values()
    ]
    st.table(pet_data)

st.divider()

# --- Task management ---
st.subheader("Tasks")

if not st.session_state.pets:
    st.info("Add a pet first before scheduling tasks.")
else:
    col1, col2 = st.columns(2)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
        selected_pet = st.selectbox("For which pet?", list(st.session_state.pets.keys()))
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=5, max_value=240, value=30)
        priority = st.selectbox("Priority", ["high", "medium", "low"])

    use_preferred = st.checkbox("Set a preferred time?")
    preferred_time = None
    if use_preferred:
        preferred_time = st.time_input("Preferred time", value=time(8, 0))

    if st.button("Add task"):
        pet = st.session_state.pets[selected_pet]
        task = Task(
            task_title, task_title, date.today(), pet,
            duration_minutes=int(duration),
            priority=priority,
            preferred_time=preferred_time,
        )
        user.schedule_task(task)
        st.session_state.tasks.append(task)
        st.success(f"Scheduled '{task_title}' for {selected_pet}!")

    if st.session_state.tasks:
        st.write("Current tasks:")
        task_data = [
            {
                "Task": t.name,
                "Pet": t.pet.pet_name,
                "Duration": f"{t.duration_minutes} min",
                "Priority": t.priority,
                "Preferred": t.preferred_time.strftime("%I:%M %p") if t.preferred_time else "—",
            }
            for t in st.session_state.tasks
        ]
        st.table(task_data)

st.divider()

# --- Schedule generation ---
st.subheader("Today's Schedule")

if st.button("Generate schedule"):
    if not st.session_state.tasks:
        st.warning("Add some tasks first.")
    else:
        scheduled, explanations = user.planner.make_plan(date.today())
        st.session_state.schedule = explanations

if st.session_state.schedule:
    for line in st.session_state.schedule:
        st.write(f"• {line}")
    st.success(f"Total tasks scheduled: {len(st.session_state.schedule)}")
