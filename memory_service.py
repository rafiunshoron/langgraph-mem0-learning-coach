from typing import Any

from mem0 import MemoryClient

from config import MEM0_API_KEY, MEM0_USER_ID, MEMORY_TOP_K


memory_client = MemoryClient(api_key=MEM0_API_KEY)


def _extract_results(response: Any) -> list[dict[str, Any]]:
    """Normalize Mem0 responses into a list of memory records."""
    if isinstance(response, dict):
        results = response.get("results", [])
        return results if isinstance(results, list) else []

    if isinstance(response, list):
        return response

    return []


def search_memories(
    query: str,
    user_id: str = MEM0_USER_ID,
) -> tuple[list[str], str]:
    """Retrieve relevant long-term memories for the current query."""
    try:
        response = memory_client.search(
            query,
            filters={"user_id": user_id},
            top_k=MEMORY_TOP_K,
        )

        records = _extract_results(response)
        memories = [
            record["memory"]
            for record in records
            if isinstance(record, dict) and record.get("memory")
        ]

        return memories, "available"

    except Exception as error:
        print(
            f"[MEMORY WARNING] Search failed: "
            f"{type(error).__name__}: {error}"
        )
        return [], "unavailable"


def store_interaction(
    user_message: str,
    assistant_message: str,
    thread_id: str,
    user_id: str = MEM0_USER_ID,
) -> tuple[bool, str]:
    """Submit the latest user-assistant interaction to Mem0."""
    messages = [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": assistant_message},
    ]

    try:
        response = memory_client.add(
            messages,
            user_id=user_id,
            run_id=thread_id,
            metadata={
                "source": "langgraph-learning-coach",
                "thread_id": thread_id,
            },
        )

        if isinstance(response, dict):
            status = str(response.get("status", "accepted"))
            event_id = response.get("event_id")

            if event_id:
                return True, f"{status} | event_id={event_id}"

            return True, status

        return True, "accepted"

    except Exception as error:
        message = f"{type(error).__name__}: {error}"
        print(f"[MEMORY WARNING] Storage failed: {message}")
        return False, message


def get_all_memories(
    user_id: str = MEM0_USER_ID,
) -> tuple[list[dict[str, Any]], str]:
    """Retrieve memories for inspection and management."""
    try:
        response = memory_client.get_all(
            filters={"user_id": user_id},
            page=1,
            page_size=100,
        )
        return _extract_results(response), "available"

    except Exception as error:
        message = f"{type(error).__name__}: {error}"
        print(f"[MEMORY WARNING] Listing failed: {message}")
        return [], "unavailable"


def delete_memory(memory_id: str) -> tuple[bool, str]:
    """Delete one exact memory."""
    try:
        memory_client.delete(memory_id=memory_id)
        return True, "Memory deleted."

    except Exception as error:
        message = f"{type(error).__name__}: {error}"
        return False, message


def clear_all_memories(
    user_id: str = MEM0_USER_ID,
) -> tuple[bool, str]:
    """Delete every long-term memory belonging to one user."""
    try:
        memory_client.delete_all(user_id=user_id)
        return True, f"All memories deleted for {user_id}."

    except Exception as error:
        message = f"{type(error).__name__}: {error}"
        return False, message