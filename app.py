import streamlit as st
import json
import os
from session_state import init_session_state

# 1. 基础配置
st.set_page_config(page_title="AI 视频助手 - 登录", layout="centered")
init_session_state()

# 2. 增强型后端函数：确保在云服务器路径下也能读到 JSON
def load_users():
    # 使用绝对路径防止 Jupyter 工作目录切换导致的读取失败
    base_path = os.path.dirname(__file__)
    json_path = os.path.join(base_path, "data", "users.json")
    
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    # 彻底移除 session_state 备选逻辑，统一数据源
    return {"1": "1", "admin": "test123"}

# 3. 自动跳转：防止重复登录
if st.session_state.is_logged_in:
    st.switch_page("pages/01_Main_App.py")

# 4. UI 渲染
st.title("📽️ AI 视频助手系统")
tab1, tab2 = st.tabs(["用户登录", "新用户注册"])

with tab1:
    # 修复：输入框添加 label_visibility 提升 UI 体验
    input_user = st.text_input("用户名", key="login_user_id").strip()
    input_pwd = st.text_input("密码", type="password", key="login_pwd_id").strip()
    
    if st.button("立即登录", use_container_width=True):
        users = load_users()
        
        # 强制字符串比对，防止 JSON 将 "1" 识别为 int
        u = str(input_user)
        p = str(input_pwd)
        
        if u in users and str(users[u]) == p:
            st.session_state.is_logged_in = True
            st.session_state.username = u
            st.success("登录成功！")
            st.rerun() # 先刷新状态，触发顶部的自动跳转逻辑
        else:
            st.error("用户名或密码错误")

with tab2:
    st.info("注册功能开发中...")