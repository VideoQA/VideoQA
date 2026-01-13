import streamlit as st

def init_session_state():
    if "is_logged_in" not in st.session_state:
        st.session_state.is_logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    # --- 模拟数据库 (存放预设账号) ---
    if "user_db" not in st.session_state:
        # 后端思维：键为用户名，值为密码（实际应存哈希值）
        st.session_state.user_db = {
            "1": "1",           # 你的需求：用户名1, 密码1
            "admin": "admin123" # 备用管理员账号
        }
    if "file_uploaded" not in st.session_state:
        st.session_state.file_uploaded = False
    if "video_data" not in st.session_state:
        st.session_state.video_data = None  # 存储 BytesIO 或 文件路径
    if "processing_mode" not in st.session_state:
        st.session_state.processing_mode = None # "memory" 或 "disk"
    if "qa_chain" not in st.session_state:
        st.session_state.qa_chain = None
    if "summary" not in st.session_state:
        st.session_state.summary = ""
    if "history" not in st.session_state:
        # 模拟历史记录：[{'title': '视频1', 'date': '2026-01-12'}, ...]
        st.session_state.history = []