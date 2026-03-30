import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None
if "setup_done" not in st.session_state:
    st.session_state.setup_done = False
if "schedule" not in st.session_state:
    st.session_state.schedule = None

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🐾 PawPal+")
st.caption("Your daily pet care planner")
st.divider()

# ---------------------------------------------------------------------------
# STEP 1 — Owner setup
# ---------------------------------------------------------------------------
if not st.session_state.setup_done:
    st.subheader("👤 Let's get started — tell us about yourself")
    with st.form("owner_form"):
        col1, col2 = st.columns(2)
        with col1:
            owner_name = st.text_input("Your name", placeholder="e.g. Jordan")
        with col2:
            available_time = st.slider("How many minutes do you have today?", 30, 480, 120, step=15)
        submitted = st.form_submit_button("Continue →", use_container_width=True)
        if submitted and owner_name.strip():
            st.session_state.owner = Owner(name=owner_name.strip(), available_time=available_time)
            st.session_state.setup_done = True
            st.rerun()
        elif submitted:
            st.warning("Please enter your name.")
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Sidebar — owner summary + reset
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 👤 {owner.name}")
    st.metric("Time available today", f"{owner.available_time} min")
    st.divider()

    pets = owner.get_pets()
    if pets:
        st.markdown("**Your pets**")
        for pet in pets:
            st.markdown(f"- {pet.name} ({pet.species}, {pet.age}y)")
    else:
        st.info("No pets added yet.")

    st.divider()
    if st.button("🔄 Start over", use_container_width=True):
        for key in ["owner", "setup_done", "schedule"]:
            del st.session_state[key]
        st.rerun()

# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🐶 My Pets", "📋 Tasks", "📅 Daily Schedule"])

# ── TAB 1: Pets ─────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Add a pet")
    with st.form("pet_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            pet_name = st.text_input("Pet name", placeholder="e.g. Mochi")
        with c2:
            species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
        with c3:
            age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
        add_pet = st.form_submit_button("➕ Add pet", use_container_width=True)
        if add_pet:
            if pet_name.strip():
                owner.add_pet(Pet(name=pet_name.strip(), species=species, age=age))
                st.success(f"{pet_name.strip()} added!")
                st.session_state.schedule = None
                st.rerun()
            else:
                st.warning("Please enter a pet name.")

    pets = owner.get_pets()
    if pets:
        st.divider()
        st.subheader("Your pets")
        cols = st.columns(min(len(pets), 3))
        for i, pet in enumerate(pets):
            with cols[i % 3]:
                st.markdown(f"### {pet.name}")
                st.write(f"**Species:** {pet.species.capitalize()}")
                st.write(f"**Age:** {pet.age} year(s)")
                st.write(f"**Tasks:** {len(pet.get_tasks())}")
                if st.button(f"Remove {pet.name}", key=f"remove_pet_{i}"):
                    owner.remove_pet(pet)
                    st.session_state.schedule = None
                    st.rerun()
    else:
        st.info("No pets yet — add one above to get started.")

# ── TAB 2: Tasks ────────────────────────────────────────────────────────────
with tab2:
    pets = owner.get_pets()
    if not pets:
        st.info("Add a pet first before adding tasks.")
    else:
        st.subheader("Add a task")
        with st.form("task_form"):
            c1, c2 = st.columns(2)
            with c1:
                selected_pet_name = st.selectbox("For which pet?", [p.name for p in pets])
                task_name = st.text_input("Task name", placeholder="e.g. Morning walk")
                category = st.selectbox("Category", ["walk", "feeding", "meds", "grooming", "enrichment", "other"])
            with c2:
                duration = st.slider("Duration (minutes)", 5, 120, 20, step=5)
                priority = st.radio("Priority", ["high", "medium", "low"], horizontal=True)
                frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
            notes = st.text_area("Notes (optional)", placeholder="Any extra details...")
            add_task = st.form_submit_button("➕ Add task", use_container_width=True)

            if add_task:
                if task_name.strip():
                    selected_pet = next(p for p in pets if p.name == selected_pet_name)
                    warning = selected_pet.add_task(Task(
                        name=task_name.strip(),
                        category=category,
                        duration=duration,
                        priority=priority,
                        frequency=frequency,
                        notes=notes.strip(),
                    ))
                    if warning:
                        st.warning(warning)
                    else:
                        st.success(f"Task '{task_name.strip()}' added for {selected_pet_name}!")
                    st.session_state.schedule = None
                    st.rerun()
                else:
                    st.warning("Please enter a task name.")

        # Show existing tasks grouped by pet
        all_pairs = owner.get_all_tasks()
        if all_pairs:
            st.divider()
            st.subheader("All tasks")
            for pet in pets:
                tasks = pet.get_tasks()
                if not tasks:
                    continue
                with st.expander(f"🐾 {pet.name} — {len(tasks)} task(s)", expanded=True):
                    for idx, task in enumerate(tasks):
                        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
                        c1.write(f"**{task.name}**")
                        c2.write(f"⏱ {task.duration} min")
                        priority_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                        c3.write(f"{priority_colors.get(task.priority, '')} {task.priority}")
                        c4.write(f"🔁 {task.frequency}")
                        if c5.button("✕", key=f"del_{pet.name}_{idx}"):
                            pet.remove_task(task)
                            st.session_state.schedule = None
                            st.rerun()
        else:
            st.info("No tasks yet — add one above.")

# ── TAB 3: Schedule ─────────────────────────────────────────────────────────
with tab3:
    pets = owner.get_pets()
    all_tasks = owner.get_all_tasks()

    if not pets:
        st.info("Add a pet and some tasks first.")
    elif not all_tasks:
        st.info("Add some tasks before generating a schedule.")
    else:
        total_tasks_time = sum(t.duration for _, t in all_tasks)
        c1, c2, c3 = st.columns(3)
        c1.metric("Pets", len(pets))
        c2.metric("Total tasks", len(all_tasks))
        c3.metric("Total tasks time", f"{total_tasks_time} min")

        st.divider()

        if st.button("✨ Generate my daily schedule", use_container_width=True, type="primary"):
            # Reset completion state before generating
            for _, task in all_tasks:
                task.mark_undone()
                task.is_urgent = False
            scheduler = Scheduler(owner)
            st.session_state.schedule = scheduler.generate()

        schedule = st.session_state.schedule
        if schedule:
            st.divider()
            scheduled = schedule.get_checklist()
            skipped = schedule.get_skipped()

            # Urgent reminders banner
            urgent = [(pet, task) for pet, task in scheduled if task.is_urgent]
            if urgent:
                st.error("⚠️ Reminders — these high-priority tasks go over your time budget but must not be skipped:")
                for pet, task in urgent:
                    st.markdown(f"- **{task.name}** for {pet.name} ({task.duration} min)")
                st.divider()

            # Time summary
            st.markdown(f"**Scheduled:** {schedule.total_time_used} min &nbsp;|&nbsp; **Available:** {owner.available_time} min")
            over = schedule.total_time_used > owner.available_time
            if over:
                st.warning(f"You're {schedule.total_time_used - owner.available_time} min over budget due to urgent tasks.")
            else:
                st.success(f"{owner.available_time - schedule.total_time_used} min to spare today!")

            st.divider()

            # Checklist
            st.subheader("✅ Today's checklist")
            for pet, task in scheduled:
                col1, col2 = st.columns([6, 1])
                label = f"**[{pet.name}]** {task.name} — {task.duration} min · {task.priority} priority"
                if task.is_urgent:
                    label += " ⚠️"
                checked = col1.checkbox(label, value=task.is_completed, key=f"chk_{pet.name}_{task.name}")
                if checked:
                    task.mark_done()
                else:
                    task.mark_undone()
                if task.notes:
                    col1.caption(f"📝 {task.notes}")

            # Skipped tasks
            if skipped:
                st.divider()
                with st.expander(f"⏭ Skipped tasks ({len(skipped)})"):
                    for pet, task, reason in skipped:
                        st.markdown(f"- **[{pet.name}]** {task.name} — {task.duration} min · {task.priority} priority · *{reason}*")

            # Full summary
            st.divider()
            with st.expander("📋 Full schedule summary"):
                st.text(schedule.get_summary())
