import base64
from pathlib import Path
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
from history import save_history

@st.dialog("Document Preview", width="large")
def view_document_dialog(file_path: Path):
    st.markdown(f"### {file_path.name}")
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        try:
            with open(file_path, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Cannot render PDF: {e}")
    elif ext in [".txt", ".md"]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                st.text_area("Content", f.read(), height=600)
        except Exception as e:
            st.error(f"Cannot read file: {e}")
    else:
        st.info(f"Inline preview not supported for {ext} files.")
        try:
            with open(file_path, "rb") as f:
                st.download_button("Download to open locally", file_name=file_path.name, data=f)
        except Exception as e:
            st.error(f"File error: {e}")

@st.dialog("🌳 Conversation Branching Timeline", width="large")
def render_timeline():
    st.markdown("Click on any old node to immediately revert back to that point in the conversation and branch out!")
    chat = st.session_state.all_chats[st.session_state.current_chat_id]
    nodes_data = chat["nodes"]
    current_leaf = chat.get("current_leaf")
    
    ag_nodes = []
    ag_edges = []
    
    for nid, ndata in nodes_data.items():
        if nid == "root":
            ag_nodes.append(Node(id=nid, label="Start", shape="dot", color="#4fc3f7", size=15))
            continue
            
        role = ndata.get("role")
        content = ndata.get("content", "")
        # Shorten label
        label_text = content[:40] + "..." if len(content) > 40 else content
        label_text = label_text.replace("\n", " ").replace(">", "")
            
        if role == "user":
            ag_nodes.append(Node(id=nid, label=label_text, shape="box", color="#1c5253" if nid == current_leaf else "#2a3f5f", font={"color": "white"}))
        else:
            ag_nodes.append(Node(id=nid, label="AI Reply", shape="ellipse", color="#4CAF50" if nid == current_leaf else "#81c784", font={"color": "white"}))
            
        pid = ndata.get("parent_id")
        if pid and pid in nodes_data:
            ag_edges.append(Edge(source=pid, target=nid, color="#7B8CA5"))
            
    config = Config(width=800, height=500, directed=True, nodeHighlightBehavior=True, highlightColor="#F7A7A6", collapsible=False,
                    layout={"hierarchical": {"enabled": True, "direction": "UD", "sortMethod": "directed", "levelSeparation": 120}})
    
    if len(ag_nodes) <= 1:
        st.info("Ask your first question to start the timeline!")
        return

    selected_id = agraph(nodes=ag_nodes, edges=ag_edges, config=config)
    if selected_id and selected_id != "root":
        st.session_state.scroll_to = selected_id
        st.rerun()

@st.dialog("✏️ Rename Chat Session", width="small")
def rename_chat_dialog():
    old_id = st.session_state.current_chat_id
    new_name = st.text_input("New Name:", value=old_id)
    if st.button("Save", type="primary"):
        new_name = new_name.strip()
        if new_name == old_id:
            st.rerun()
        elif not new_name:
            st.error("Name cannot be empty.")
        elif new_name in st.session_state.all_chats:
            st.error("A chat with this name already exists!")
        else:
            new_all_chats = {}
            for k, v in st.session_state.all_chats.items():
                if k == old_id:
                    new_all_chats[new_name] = v
                else:
                    new_all_chats[k] = v
            st.session_state.all_chats = new_all_chats
            st.session_state.current_chat_id = new_name
            save_history(st.session_state.all_chats)
            st.rerun()
