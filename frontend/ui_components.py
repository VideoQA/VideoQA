import streamlit as st

def upload_section():
    """上传区域"""
    st.markdown("### 📽️ 上传视频开始解析")
    uploaded_file = st.file_uploader("选择一个视频文件", type=["mp4", "mov", "avi"])
    if uploaded_file is not None:
        st.session_state.file_uploaded = True
        return uploaded_file
    return None

def summary_section(summary_text):
    """右侧上方：自动总结区域"""
    st.subheader("📝 视频内容摘要")
    with st.container(border=True):
        if summary_text:
            st.write(summary_text)
        else:
            st.info("正在解析视频并生成摘要，请稍候...")

def chat_section():
    """右侧下方：智能对话区域"""
    st.subheader("💬 智能检索问答")
    
    # 显示历史消息
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 用户输入
    if prompt := st.chat_input("针对视频内容提问..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 此处待对接 backend/rag_chain.py
        with st.chat_message("assistant"):
            response = f"这是针对 '{prompt}' 的模拟回答（待对接 RAG 链）"
            st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})