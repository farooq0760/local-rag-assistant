"""
app.py — Enhanced Local RAG Chat UI with Streamlit.
Main Entry Point.
"""

import re
import uuid
import datetime
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

# Local modules
from config import CHROMA_DB_FOLDER, DOCS_FOLDER, TOP_K, TOOLTIP_CSS
from history import load_history, save_history, get_linear_messages
from utils import (
    list_documents, 
    ingest_uploaded_file, 
    load_vectorstore_and_llm, 
    build_source_map, 
    inject_tooltips, 
    build_prompt
)
from dialogs import view_document_dialog, render_timeline, rename_chat_dialog

def main():
    st.set_page_config(page_title="🔒 Private Doc Assistant", page_icon="🔒", layout="wide")
    st.markdown(TOOLTIP_CSS, unsafe_allow_html=True)

    db_exists = Path(CHROMA_DB_FOLDER).exists() and any(Path(CHROMA_DB_FOLDER).iterdir())
    if not db_exists:
        st.error("⚠️ No document database found! Run **`python ingest.py`** first.")
        st.stop()

    with st.spinner("Loading knowledge base…"):
        vectorstore, llm = load_vectorstore_and_llm()
    retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": TOP_K})

    if "quote_key_counter" not in st.session_state:
        st.session_state.quote_key_counter = 0
    if "all_chats" not in st.session_state:
        st.session_state.all_chats = load_history()
    if "current_chat_id" not in st.session_state:
        nav_name = datetime.datetime.now().strftime("%b %d, %H:%M:%S")
        new_id = f"Session: {nav_name}"
        st.session_state.current_chat_id = new_id
        st.session_state.all_chats[new_id] = {
            "nodes": {"root": {"id": "root", "parent_id": None, "role": "system", "content": "Start"}},
            "current_leaf": "root"
        }
        save_history(st.session_state.all_chats)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 🔒 Private Doc Assistant")
        st.success("✅ 100% Local — No data leaves your machine")
        st.divider()

        st.markdown("### 📤 Upload New Documents")
        uploaded_files = st.file_uploader(
            "Drop files here", type=["pdf", "docx", "xlsx", "xls", "txt", "md"],
            accept_multiple_files=True, label_visibility="collapsed"
        )
        if uploaded_files:
            for uf in uploaded_files:
                with st.spinner(f"Ingesting {uf.name}…"):
                    ok, msg = ingest_uploaded_file(uf, vectorstore)
                st.markdown(msg)

        st.divider()
        st.markdown("### 📚 Your Documents")
        docs = list_documents()
        if docs:
            for d in docs:
                col_name, col_btn = st.columns([5, 1])
                col_name.markdown(f"📄 `{d}`")
                if col_btn.button("👁️", key=f"view_{d}", help="Preview Document"):
                    view_document_dialog(Path(DOCS_FOLDER) / d)
        else:
            st.caption("No documents found in docs folder.")

        st.divider()
        st.markdown("### ⚙️ Settings")
        show_reasoning = st.toggle("🧠 Show model reasoning", value=True)

        st.divider()
        st.markdown("### 💬 Chat History")
        
        if st.button("🌳 View Branching Timeline", use_container_width=True, type="primary"):
            render_timeline()
            
        st.markdown("<br>", unsafe_allow_html=True)
            
        if st.button("➕ New Chat Session", use_container_width=True):
            nav_name = datetime.datetime.now().strftime("%b %d, %H:%M:%S")
            new_id = f"Session: {nav_name}"
            st.session_state.current_chat_id = new_id
            st.session_state.all_chats[new_id] = {
                "nodes": {"root": {"id": "root", "parent_id": None, "role": "system", "content": "Start"}},
                "current_leaf": "root"
            }
            save_history(st.session_state.all_chats)
            st.rerun()

        chat_ids = list(st.session_state.all_chats.keys())
        chat_ids.reverse()
        selected_chat = st.selectbox(
            "Select previous conversation", options=chat_ids,
            key="current_chat_id",
            label_visibility="collapsed"
        )
            
        col_ren, col_del = st.columns(2)
        with col_ren:
            if st.button("✏️ Rename", use_container_width=True):
                rename_chat_dialog()
        with col_del:
            if st.button("🗑️ Clear", use_container_width=True, help="Erase all messages in this chat"):
                st.session_state.all_chats[st.session_state.current_chat_id] = {
                    "nodes": {"root": {"id": "root", "parent_id": None, "role": "system", "content": "Start"}},
                    "current_leaf": "root"
                }
                save_history(st.session_state.all_chats)
                st.rerun()

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        "<h1 style='text-align:center'>🔒 Private Document Assistant</h1>"
        "<p style='text-align:center;color:gray'>"
        "Ask questions about your documents — 100% local &amp; private</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Chat History Rendering ────────────────────────────────────────────────
    current_chat = st.session_state.all_chats[st.session_state.current_chat_id]
    linear_messages = get_linear_messages(current_chat)
    
    for msg in linear_messages:
        st.markdown(f"<div id='msg_{msg['id']}'></div>", unsafe_allow_html=True)
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                st.markdown(msg.get("html_content") or msg.get("content", ""), unsafe_allow_html=True)
                if msg.get("thinking") and show_reasoning:
                    with st.expander("🧠 Reasoning", expanded=False):
                        styled = "\n".join(f"> {line}" for line in msg['thinking'].split("\n"))
                        st.markdown(styled)
                if msg.get("sources_info"):
                    with st.expander("📄 Sources", expanded=False):
                        for name, info in msg["sources_info"].items():
                            st.markdown(f"**[{info['num']}]** `{name}`")
            else:
                st.markdown(msg["content"])

    if "scroll_to" in st.session_state and st.session_state.scroll_to:
        js = f"""
        <script>
            setTimeout(() => {{
                var elem = window.parent.document.getElementById('msg_{st.session_state.scroll_to}');
                if (elem) {{
                    elem.scrollIntoView({{behavior: 'smooth', block: 'start'}});
                }}
            }}, 250);
        </script>
        """
        components.html(js, height=0)
        st.session_state.scroll_to = None

    # ── Inputs ────────────────────────────────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_quote, col_space = st.columns([1, 0.01])
    with col_quote:
        quote_text = st.text_area("📌 Follow-up Context Quote (Optional):", 
                                  placeholder="Copy-paste any text from the AI's response here to explicitly follow-up on it...", 
                                  height=68, 
                                  key=f"quote_input_{st.session_state.quote_key_counter}")

    question = st.chat_input("Ask me anything about your documents…")
        
    if question:
        combined_question = question
        if quote_text.strip():
            combined_question = f'> "{quote_text.strip()}"\n\n**Follow-up Question:** {question}'

        user_id = str(uuid.uuid4())
        user_node = {
            "id": user_id,
            "parent_id": current_chat["current_leaf"],
            "role": "user",
            "content": combined_question
        }
        current_chat["nodes"][user_id] = user_node
        current_chat["current_leaf"] = user_id
        
        with st.chat_message("user"):
            st.markdown(combined_question)

        with st.chat_message("assistant"):
            thinking_text = ""
            answer_text   = ""
            sources_info  = {}

            with st.status("🔍 Searching your documents…", expanded=True) as status:
                try:
                    source_docs  = retriever.invoke(combined_question)
                    sources_info = build_source_map(source_docs)
                    found_names = list(sources_info.keys())
                    status.write(f"📚 Found relevant content in: " + ", ".join(f"`{n}`" for n in found_names))

                    prompt = build_prompt(combined_question, source_docs, sources_info)
                    status.update(label="🧠 Reasoning…", expanded=True)
                    think_holder = st.empty()
                except Exception as e:
                    status.update(label="❌ Error connecting to Ollama", state="error")
                    st.error(f"Cannot reach Ollama! Please make sure the Ollama app is running in the background. If it crashed, restart it.\n\n`{e}`")
                    st.stop()

            answer_holder = st.empty()
            full_response = ""
            answer_buffer = ""
            thinking_closed = False
            in_think = False

            try:
                for chunk in llm.stream(prompt):
                    chunk_str = chunk.content if hasattr(chunk, "content") else chunk
                    full_response += chunk_str

                    if not thinking_closed:
                        if "<think>" in full_response and not in_think:
                            in_think = True
                        if in_think and "</think>" in full_response:
                            thinking_closed = True
                            in_think = False
                            m = re.search(r"<think>(.*?)</think>", full_response, re.DOTALL)
                            if m:
                                thinking_text = m.group(1).strip()
                            answer_buffer = re.sub(r"<think>.*?</think>", "", full_response, flags=re.DOTALL).strip()
                            answer_holder.markdown(answer_buffer + " ▌")
                            status.update(label="✅ Done!", state="complete", expanded=False)
                            think_holder.empty()
                        elif in_think:
                            parts = full_response.split("<think>")
                            if len(parts) > 1 and show_reasoning:
                                raw_think = parts[-1]
                                styled_think = "\n".join(f"> {line}" for line in raw_think.split("\n"))
                                think_holder.markdown(styled_think + " ▌")
                    else:
                        answer_buffer = re.sub(r"<think>.*?</think>", "", full_response, flags=re.DOTALL).strip()
                        answer_holder.markdown(answer_buffer + " ▌")
            except Exception as e:
                st.error(f"Ollama crashed or disconnected during generation: {e}")
                st.stop()

            if not thinking_closed:
                answer_buffer = full_response.strip()
                status.update(label="✅ Done!", state="complete", expanded=False)

            answer_text = answer_buffer
            html_answer = inject_tooltips(answer_text, sources_info)
            answer_holder.markdown(html_answer, unsafe_allow_html=True)

            if thinking_text and show_reasoning:
                with st.expander("🧠 Reasoning", expanded=False):
                    styled_think = "\n".join(f"> {line}" for line in thinking_text.split("\n"))
                    st.markdown(styled_think)
            if sources_info:
                with st.expander("📄 Sources", expanded=False):
                    for name, info in sources_info.items():
                        st.markdown(f"**[{info['num']}]** `{name}`")

            ai_id = str(uuid.uuid4())
            ai_node = {
                "id": ai_id,
                "parent_id": user_id,
                "role": "assistant",
                "content": answer_text,
                "html_content": html_answer,
                "thinking": thinking_text,
                "sources_info": sources_info
            }
            current_chat["nodes"][ai_id] = ai_node
            current_chat["current_leaf"] = ai_id
            
            save_history(st.session_state.all_chats)
            
            st.session_state.quote_key_counter += 1
            st.rerun()

if __name__ == "__main__":
    main()
