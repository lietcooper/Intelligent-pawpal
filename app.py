import streamlit as st
from datetime import date, time
from ai_assistant import CareAssistant, KnowledgeBase, ScheduleContext
from pawpal_system import User, Pet, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# --- Session state ---
if "user" not in st.session_state:
    st.session_state.user = User("u1", "Jordan")
if "pets" not in st.session_state:
    st.session_state.pets = {}
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "schedule" not in st.session_state:
    st.session_state.schedule = None  # (scheduled_tasks, explanations)
if "ai_response" not in st.session_state:
    st.session_state.ai_response = None

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
st.subheader("Add a Task")

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

    col3, col4 = st.columns(2)
    with col3:
        use_preferred = st.checkbox("Set a preferred time?")
        preferred_time = None
        if use_preferred:
            preferred_time = st.time_input("Preferred time", value=time(8, 0))
    with col4:
        recurrence = st.selectbox("Recurrence", ["none", "daily", "weekly"])
        recurrence_val = None if recurrence == "none" else recurrence

    if st.button("Add task"):
        pet = st.session_state.pets[selected_pet]
        task = Task(
            task_title, task_title, date.today(), pet,
            duration_minutes=int(duration),
            priority=priority,
            preferred_time=preferred_time,
            recurrence=recurrence_val,
        )
        warning = user.schedule_task(task)
        st.session_state.tasks.append(task)
        # Reset cached schedule so stale results aren't shown
        st.session_state.schedule = None
        st.session_state.ai_response = None

        if warning:
            st.warning(
                f"Task added, but a time conflict was detected:\n\n"
                f"**{warning}**\n\n"
                "You can still generate a schedule — PawPal+ will find the next available slot."
            )
        else:
            st.success(f"Scheduled '{task_title}' for {selected_pet}!")

# --- Task list (sorted by time) ---
pending_tasks = [t for t in st.session_state.tasks if t.status == "pending"]
if pending_tasks:
    st.divider()
    st.subheader("Pending Tasks")
    sorted_tasks = user.planner.sort_by_time(pending_tasks)
    task_data = []
    for t in sorted_tasks:
        if t.scheduled_start:
            time_str = t.scheduled_start.strftime("%I:%M %p")
        elif t.preferred_time:
            time_str = f"{t.preferred_time.strftime('%I:%M %p')} (preferred)"
        else:
            time_str = "—"
        task_data.append({
            "Time": time_str,
            "Task": t.name,
            "Pet": t.pet.pet_name,
            "Duration": f"{t.duration_minutes} min",
            "Priority": t.priority,
            "Repeats": t.recurrence or "—",
        })
    st.table(task_data)

st.divider()

# --- Schedule generation ---
st.subheader("Today's Schedule")

if st.button("Generate schedule"):
    if not st.session_state.tasks:
        st.warning("Add some tasks first.")
    else:
        scheduled, explanations = user.planner.make_plan(date.today())
        st.session_state.schedule = (scheduled, explanations)
        st.session_state.ai_response = None

if st.session_state.schedule:
    scheduled, explanations = st.session_state.schedule

    if not scheduled:
        st.info("No tasks could be scheduled for today.")
    else:
        st.caption(f"{len(scheduled)} task(s) scheduled")

        for explanation in explanations:
            if "preferred time conflict" in explanation:
                st.warning(explanation)
            else:
                st.success(explanation)

        # --- Conflict report ---
        conflicts = user.planner.find_conflicts(scheduled)
        if conflicts:
            st.divider()
            st.error(
                f"**{len(conflicts)} scheduling conflict(s) detected.**  \n"
                "Review the overlapping tasks below and consider adjusting times or durations."
            )
            for c in conflicts:
                a, b = c["task_a"], c["task_b"]
                kind_label = "Same pet" if c["overlap"] == "same_pet" else "Different pets"
                st.warning(
                    f"**{kind_label}** conflict:  \n"
                    f"• **{a.name}** ({a.pet.pet_name}) "
                    f"{a.scheduled_start.strftime('%I:%M %p')} – {a.scheduled_end.strftime('%I:%M %p')}  \n"
                    f"• **{b.name}** ({b.pet.pet_name}) "
                    f"{b.scheduled_start.strftime('%I:%M %p')} – {b.scheduled_end.strftime('%I:%M %p')}"
                )
        else:
            st.info("No conflicts — your schedule looks clean!")

# --- RAG Care Assistant ---
st.divider()
st.subheader("AI Care Assistant")
st.caption("Uses local pet-care guidance plus today's generated schedule.")

provider_label = st.selectbox(
    "LLM provider",
    ["Local fallback", "OpenAI", "Gemini"],
    help="Local fallback runs without API keys. OpenAI and Gemini use their matching environment variables.",
)
provider = {
    "Local fallback": "local",
    "OpenAI": "openai",
    "Gemini": "gemini",
}[provider_label]

default_model = {
    "local": "",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.5-flash",
}[provider]
model_name = st.text_input(
    "Model name",
    value=default_model,
    disabled=(provider == "local"),
    help="OpenAI uses OPENAI_API_KEY. Gemini uses GEMINI_API_KEY or GOOGLE_API_KEY.",
)

if st.button("Explain and improve schedule"):
    if not st.session_state.pets:
        st.warning("Add at least one pet before using the assistant.")
    elif not st.session_state.tasks:
        st.warning("Add at least one task before using the assistant.")
    elif not st.session_state.schedule:
        st.warning("Generate a schedule before using the assistant.")
    else:
        scheduled, explanations = st.session_state.schedule
        if not scheduled:
            st.warning("Generate a schedule with at least one scheduled task first.")
        else:
            conflicts = user.planner.find_conflicts(scheduled)
            context = ScheduleContext.from_user(user, scheduled, explanations, conflicts)
            assistant = CareAssistant(
                KnowledgeBase(),
                provider=provider,
                model=model_name or None,
            )
            with st.spinner("Reviewing schedule with retrieved care guidance..."):
                st.session_state.ai_response = assistant.explain_schedule(context)

if st.session_state.ai_response:
    response = st.session_state.ai_response
    st.write(response.answer)
    if response.sources:
        st.caption(f"Sources: {', '.join(response.sources)}")
    if response.used_model:
        st.success(
            f"Generated with {response.provider.title()} "
            f"({response.model}) using retrieved local guidance."
        )
    elif response.error:
        st.warning(f"Using local fallback because the model call failed: {response.error}")
    else:
        st.info(
            "Using local fallback. Set OPENAI_API_KEY for OpenAI or "
            "GEMINI_API_KEY for Gemini model-generated output."
        )
