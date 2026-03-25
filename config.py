import os
from dotenv import load_dotenv

load_dotenv()

CHROMA_DB_FOLDER = os.getenv("CHROMA_DB_FOLDER", "./chroma_db")
DOCS_FOLDER      = os.getenv("DOCS_FOLDER",      "./docs")
CHAT_MODEL       = os.getenv("CHAT_MODEL",       "deepseek-r1:7b")
EMBED_MODEL      = os.getenv("EMBED_MODEL",      "nomic-embed-text")
TOP_K            = int(os.getenv("TOP_K",        "5"))
HISTORY_FILE     = "./chat_history.json"

TOOLTIP_CSS = """
<style>
.ref-num {
    display: inline-block;
    color: #4fc3f7;
    font-size: 0.72em;
    vertical-align: super;
    cursor: help;
    font-weight: 700;
    background: rgba(79,195,247,0.12);
    border: 1px solid #4fc3f7;
    border-radius: 50%;
    padding: 0 5px;
    margin: 0 2px;
    position: relative;
}
.ref-num .ref-tip {
    visibility: hidden;
    opacity: 0;
    transition: opacity 0.15s ease;
    background: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #4fc3f7;
    border-radius: 10px;
    padding: 10px 14px;
    position: absolute;
    z-index: 9999;
    bottom: 150%;
    left: 50%;
    transform: translateX(-50%);
    width: 310px;
    font-size: 1.3em;
    line-height: 1.5;
    box-shadow: 0 6px 24px rgba(0,0,0,0.7);
    white-space: normal;
    font-weight: normal;
    pointer-events: none;
}
.ref-num .ref-tip::after {
    content: "";
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 6px solid transparent;
    border-top-color: #4fc3f7;
}
.ref-num:hover .ref-tip { visibility: visible; opacity: 1; }
</style>
"""
