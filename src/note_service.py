import os
import json


def create_note_file(title: str) -> dict:
    """Create a new note with the given title.

    Args:
        title (str): Note title (used as filename)

    Returns:
        dict: Success message or error
    """
    os.makedirs("./notes", exist_ok=True)
    if os.path.exists(os.path.join("./notes", title)):
        return {"error": "Note with this title already exists."}
    with open(os.path.join("./notes", title), "w") as f:
        json.dump({}, f)
    return {"message": "Note created successfully."}


def delete_note_file(title: str) -> dict:
    """Delete a note.

    Args:
        title (str): Note title to delete

    Returns:
        dict: Deletion result with message or error
    """
    note_path = os.path.join("./notes", title)
    if not os.path.exists(note_path):
        return {"error": "Note not found."}
    os.remove(note_path)
    return {"message": "Note deleted successfully."}


def list_all_notes() -> dict:
    """List all notes.

    Returns:
        dict: Dictionary with notes list or error
    """
    notes_dir = "./notes"
    if not os.path.exists(notes_dir):
        return {"notes": []}
    notes = [f for f in os.listdir(notes_dir) if os.path.isfile(os.path.join(notes_dir, f))]
    return {"notes": notes}


def read_note_content(title: str) -> dict:
    """Read a note.

    Args:
        title (str): Note title to read

    Returns:
        dict: Note content or error
    """
    note_path = os.path.join("./notes", title)
    if not os.path.exists(note_path):
        return {"error": "Note not found."}
    with open(note_path, "r") as f:
        content = json.load(f)
    return content


def edit_note_value(title: str, key: list[str], value: str) -> dict:
    """Edit a value in a note by key path.

    Args:
        title (str): Note title to edit
        key (list[str]): List of keys representing the path to the value
        value (str): New value to set

    Returns:
        dict: Success message or error
    """
    note_path = os.path.join("./notes", title)
    if not os.path.exists(note_path):
        return {"error": "Note not found."}

    with open(note_path, "r") as f:
        content = json.load(f)

    # Navigate to the target location and set the value
    current = content
    for k in key[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]

    current[key[-1]] = value

    with open(note_path, "w") as f:
        json.dump(content, f, indent=2)

    return {"message": "Note updated successfully."}


def insert_key_path(title: str, key: list[str]) -> dict:
    """Insert a key path structure in a note.

    Args:
        title (str): Note title to edit
        key (list[str]): List of keys representing the path to create

    Returns:
        dict: Success message or error
    """
    note_path = os.path.join("./notes", title)
    if not os.path.exists(note_path):
        return {"error": "Note not found."}

    with open(note_path, "r") as f:
        content = json.load(f)

    # Navigate to the target location, creating nested structure as needed
    current = content
    for i in range(len(key)):
        if key[i] not in current:
            current[key[i]] = {}
        elif not isinstance(current[key[i]], dict) and i + 1 < len(key):
            # Convert existing non-dict value to dict, preserving value under next key
            value = current[key[i]]
            current[key[i]] = {key[i + 1]: value}

    with open(note_path, "w") as f:
        json.dump(content, f, indent=2)

    return {"message": "Key inserted successfully."}


def delete_key_path(title: str, key: list[str]) -> dict:
    """Delete a key from a note.

    Args:
        title (str): Note title to edit
        key (list[str]): List of keys representing the path to delete

    Returns:
        dict: Success message or error
    """
    note_path = os.path.join("./notes", title)
    if not os.path.exists(note_path):
        return {"error": "Note not found."}

    with open(note_path, "r") as f:
        content = json.load(f)

    # Navigate to the parent of the target key
    current = content
    for k in key[:-1]:
        if k not in current:
            return {"error": f"Path not found: {k}"}
        current = current[k]

    # Delete the key
    if key[-1] not in current:
        return {"error": f"Key '{key[-1]}' not found."}

    del current[key[-1]]

    with open(note_path, "w") as f:
        json.dump(content, f, indent=2)

    return {"message": "Key deleted successfully."}