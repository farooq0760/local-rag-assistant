import json
from pathlib import Path
from config import HISTORY_FILE

def migrate_to_tree(flat_list):
    """Convert an old flat list of messages into a tree structure."""
    nodes = {"root": {"id": "root", "parent_id": None, "role": "system", "content": "Start"}}
    prev_id = "root"
    for i, msg in enumerate(flat_list):
        msg_id = f"msg_{i}"
        new_msg = dict(msg)
        new_msg["id"] = msg_id
        new_msg["parent_id"] = prev_id
        nodes[msg_id] = new_msg
        prev_id = msg_id
    return {"nodes": nodes, "current_leaf": prev_id}

def load_history():
    if Path(HISTORY_FILE).exists():
        try:
            with open(HISTORY_FILE, encoding="utf-8") as f:
                data = json.load(f)
                result = {}
                for cid, val in data.items():
                    if isinstance(val, list):
                        result[cid] = migrate_to_tree(val)
                    elif isinstance(val, dict) and "nodes" in val:
                        result[cid] = val
                return result
        except Exception:
            return {}
    return {}

def save_history(all_chats):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chats, f, ensure_ascii=False, indent=2)

def get_linear_messages(chat_tree):
    """Traverse from current_leaf up to the root to get the linear chat sequence."""
    if not chat_tree or "nodes" not in chat_tree:
        return []
    nodes = chat_tree["nodes"]
    current_id = chat_tree.get("current_leaf")
    sequence = []
    while current_id and current_id != "root":
        node = nodes.get(current_id)
        if not node:
            break
        sequence.append(node)
        current_id = node.get("parent_id")
    sequence.reverse()
    return sequence
