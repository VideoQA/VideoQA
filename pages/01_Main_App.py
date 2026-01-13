import streamlit as st
import os
import json
from io import BytesIO
import tempfile 
from pathlib import Path 
from session_state import init_session_state
from frontend.ui_components import upload_section, summary_section, chat_section
# 引入后端推理逻辑
from backend.qa_chain import build_qa_chain, query_video, generate_summary
from backend.retriever import build_retriever

# 1. 页面配置 (必须在最顶部)
st.set_page_config(page_title="AI 视频助手 - 核心解析", layout="wide")
init_session_state()

# 在 init_session_state 中确保有存储摘要和对话的变量
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None

# 2. 权限拦截与跳转按钮
if not st.session_state.get("is_logged_in", False):
    col1, col2 = st.columns([3, 1])
    with col1:
        st.warning("⚠️ 会话已过期或未登录，请重新登录。")
    with col2:
        if st.button("👉 点击跳转登录"):
            st.switch_page("app.py")
    st.stop() # 停止后续代码运行

# 3. 侧边栏：用户信息与退出登录
with st.sidebar:
    st.markdown(f"### 👤 当前用户: **{st.session_state.username}**")
    if st.button("🚪 退出登录", use_container_width=True):
        st.session_state.is_logged_in = False
        st.session_state.username = None
        st.switch_page("app.py")
    st.divider()
    
    # 加载历史记录 (从 data/history.json)
    st.title("📜 历史解析记录")
    history_path = "data/history.json"
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            all_history = json.load(f)
            # 获取当前用户的特定历史
            user_history = all_history.get(st.session_state.username, [])
            
            if not user_history:
                st.write("暂无历史记录")
            for item in user_history:
                # 使用唯一 key 防止 ID 冲突
                st.button(f"📹 {item['title']}", key=f"hist_{item['title']}")
    else:
        st.write("未找到历史数据库")

st.title("🎬 视频解析助手")

# 定义阈值: 100MB
MAX_MEMORY_SIZE = 100 * 1024 * 1024 

if not st.session_state.file_uploaded:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        uploaded_file = upload_section()
        if uploaded_file:
            # 获取文件大小
            file_size = uploaded_file.size
            
            if file_size < MAX_MEMORY_SIZE:
                # 方式1：直接存入内存 (BytesIO)
                st.session_state.video_data = BytesIO(uploaded_file.read())
                st.session_state.processing_mode = "memory"
                st.success(f"小文件预览：已载入内存 ({file_size / 1024 / 1024:.2f} MB)")
            else:
                # 方式2：保存到临时磁盘路径 (tempfile)
                # suffix确保浏览器和后端能识别格式
                suffix = os.path.splitext(uploaded_file.name)[-1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.read())
                    st.session_state.video_data = tmp.name
                st.session_state.processing_mode = "disk"
                st.warning(f"大文件预览：已转存临时磁盘 ({file_size / 1024 / 1024:.2f} MB)")
            # --- ✨ 关键：在这里插入摘要生成代码 ---
            with st.spinner("🚀 正在分析视频并生成摘要，请稍候..."):
                try:
                   # 1. 确保 transcript 文件存在 (目前先用测试文件)
                    transcript_path = "data/processed_transcript_timestamped.txt"
                    
                    # 2. 调用你后端的函数（需确保 backend.qa_chain 已导入）
                    # 这一步包含了：提取音频 -> Whisper转文字 -> 构建Retriever
                    from backend.retriever import build_retriever
                    my_retriever = build_retriever(transcript_path)
                    
                    # 3. 调用后端 qa_chain.py
                    from backend.qa_chain import build_qa_chain, generate_summary
                    
                    # 4. 生成摘要并存入 Session
                    st.session_state.qa_chain = build_qa_chain(my_retriever)
                    st.session_state.summary = generate_summary(my_retriever)

                    st.success("解析完成！")
                    
                except Exception as e:
                    st.error(f"后端处理失败: {e}")
                    st.stop()

            st.session_state.file_uploaded = True
            st.rerun()
else:
    left_col, right_col = st.columns([1, 1])
    with left_col:
        st.subheader("📹 原始视频")
    
        if st.session_state.video_data:
            try:
                if st.session_state.processing_mode == "memory":
                    st.session_state.video_data.seek(0)
                    video_bytes = st.session_state.video_data.read()
                    st.video(video_bytes)
                else:
                    if os.path.exists(st.session_state.video_data):
                        st.video(st.session_state.video_data)
            except Exception as e:
                st.error(f"视频渲染失败: {e}")

        # --- 在这里添加"重新上传"按钮 ---
        st.write("") # 添加一点间距
        if st.button("🔄 重新上传", use_container_width=True):
            # 1. 如果是磁盘模式，删除临时文件防止占用空间
            if st.session_state.processing_mode == "disk" and os.path.exists(st.session_state.video_data):
                try:
                    os.remove(st.session_state.video_data)
                except Exception as e:
                    print(f"清理临时文件失败: {e}")
            
            # 2. 重置所有相关的 session_state
            st.session_state.file_uploaded = False
            st.session_state.video_data = None
            st.session_state.processing_mode = None
            
            # 3. 强制页面重绘，回到上传逻辑
            st.rerun()

    with right_col:
        # --- 视频摘要展示 ---
        st.subheader("📝 视频内容摘要")
        if st.session_state.summary:
            st.markdown(st.session_state.summary)
        else:
            st.info("未能获取到视频摘要。")
        
        st.divider()
        
        # --- 问答对话区 ---
        st.subheader("💬 智能问答")
        
        # 1. 渲染历史对话
        chat_container = st.container(height=400) # 固定高度的滚动容器
        with chat_container:
            for q, a in st.session_state.chat_history:
                st.chat_message("user").write(q)
                st.chat_message("assistant").write(a)
        
        # 2. 聊天输入框（固定在右侧列底部）
        if prompt := st.chat_input("针对视频内容提问..."):
            # 在界面上立即显示用户输入
            with chat_container:
                st.chat_message("user").write(prompt)

                if st.session_state.qa_chain is not None:
                    from backend.qa_chain import query_video
                    # 调用后端逻辑
                    with st.spinner("思考中..."):
                        ans, updated_history = query_video(
                            st.session_state.qa_chain, 
                            prompt, 
                            st.session_state.chat_history
                        )
                        st.chat_message("assistant").write(ans)
                        st.session_state.chat_history = updated_history
                else:
                    st.error("QA 链未成功初始化，请检查 backend 文件夹下的代码。")
# 模拟添加历史记录（在视频上传成功后调用）
if st.session_state.file_uploaded and not st.session_state.history:
    st.session_state.history.append({"title": "最新上传视频", "date": "2026-01-12"})