import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from config import MEM0_USER_ID
from graph import coach_graph
from memory_service import (
    clear_all_memories,
    delete_memory,
    get_all_memories,
)


st.set_page_config(
    page_title="RecallCoach AI",
    page_icon="🧠",
    layout="wide",
)


def thread_config(thread_id: str) -> dict:
    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


def get_thread_messages(thread_id: str) -> list:
    """Load the conversation directly from LangGraph SQLite."""
    try:
        snapshot = coach_graph.get_state(thread_config(thread_id))
        return list(snapshot.values.get("messages", []))
    except Exception as error:
        st.error(
            f"Could not load conversation: "
            f"{type(error).__name__}: {error}"
        )
        return []


def memory_id_from(record: dict) -> str:
    return str(
        record.get("id")
        or record.get("memory_id")
        or ""
    )


# UI-only state
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "python-basics"

if "thread_input" not in st.session_state:
    st.session_state.thread_input = st.session_state.thread_id

if "memory_records" not in st.session_state:
    st.session_state.memory_records = None

if "sidebar_notice" not in st.session_state:
    st.session_state.sidebar_notice = None


# Sidebar
with st.sidebar:
    st.title("🧠 RecallCoach")
    st.caption("Memory control center")

    if st.session_state.sidebar_notice:
        st.success(st.session_state.sidebar_notice)
        st.session_state.sidebar_notice = None

    st.subheader("Conversation")

    st.text_input(
        "Thread ID",
        key="thread_input",
        help="Different thread IDs have separate SQLite histories.",
    )

    if st.button(
        "Switch or create thread",
        use_container_width=True,
    ):
        new_thread = st.session_state.thread_input.strip()

        if new_thread:
            st.session_state.thread_id = new_thread
            st.session_state.memory_records = None
            st.rerun()
        else:
            st.warning("Enter a valid thread ID.")

    st.info(
        f"Current thread: **{st.session_state.thread_id}**\n\n"
        f"Mem0 user: **{MEM0_USER_ID}**"
    )

    st.divider()
    st.subheader("Long-term memory")

    if st.button(
        "Load / refresh memories",
        use_container_width=True,
    ):
        records, status = get_all_memories()

        if status == "available":
            st.session_state.memory_records = records
        else:
            st.error("Mem0 is currently unavailable.")

    records = st.session_state.memory_records

    if records is not None:
        if not records:
            st.caption("No long-term memories found.")

        for index, record in enumerate(records, start=1):
            memory_id = memory_id_from(record)
            memory_text = record.get("memory", "No memory text")

            with st.expander(
                f"Memory {index}",
                expanded=False,
            ):
                st.write(memory_text)
                st.caption(f"ID: {memory_id or 'unknown'}")

                if memory_id and st.button(
                    "Forget this memory",
                    key=f"forget-{memory_id}",
                    use_container_width=True,
                ):
                    success, message = delete_memory(memory_id)

                    if success:
                        st.session_state.memory_records = [
                            item
                            for item in records
                            if memory_id_from(item) != memory_id
                        ]
                        st.session_state.sidebar_notice = message
                        st.rerun()
                    else:
                        st.error(message)

    st.divider()

    confirm_clear = st.checkbox(
        f"Confirm deletion for {MEM0_USER_ID}"
    )

    if st.button(
        "Clear all long-term memories",
        disabled=not confirm_clear,
        use_container_width=True,
        type="secondary",
    ):
        success, message = clear_all_memories()

        if success:
            st.session_state.memory_records = []
            st.session_state.sidebar_notice = message
            st.rerun()
        else:
            st.error(message)


# Main interface
st.title("RecallCoach AI")
st.write(
    "A personalized learning coach with "
    "**LangGraph**, **SQLite short-term memory**, "
    "and **Mem0 long-term memory**."
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("User", MEM0_USER_ID)

with col2:
    st.metric("Active thread", st.session_state.thread_id)

with col3:
    st.metric("Long-term memory", "Mem0 Platform")

st.caption(
    "Switching threads changes the SQLite conversation history "
    "while preserving user-level Mem0 memories."
)

st.divider()


# Load messages from SQLite—not from Streamlit session state
messages = get_thread_messages(st.session_state.thread_id)

if not messages:
    st.info(
        "This conversation is empty. Introduce yourself, describe "
        "what you are learning, or share a learning preference."
    )

for message in messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(str(message.content))

    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(str(message.content))


user_input = st.chat_input(
    "What would you like to learn?",
    max_chars=4000,
)


if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        with st.spinner("RecallCoach is thinking..."):
            result = coach_graph.invoke(
                {
                    "messages": [
                        HumanMessage(content=user_input)
                    ]
                },
                config=thread_config(
                    st.session_state.thread_id
                ),
            )

        assistant_message = result["messages"][-1]

        with st.chat_message("assistant"):
            st.markdown(str(assistant_message.content))

        retrieval_status = result.get(
            "memory_retrieval_status",
            "unknown",
        )
        write_status = result.get(
            "memory_write_status",
            "unknown",
        )

        if retrieval_status == "unavailable":
            st.warning(
                "The response was generated without "
                "long-term personalization."
            )

        st.caption(
            f"Memory retrieval: {retrieval_status} · "
            f"Memory write: {write_status}"
        )

    except Exception as error:
        st.error(
            f"Application error: "
            f"{type(error).__name__}: {error}"
        )