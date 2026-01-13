# QA推理链

import os
import torch
import logging
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import HumanMessage
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"
# REPO_ID = "Qwen/Qwen2.5-1.5B-Instruct"  # 或 7B 如果内存够
# llm = HuggingFaceEndpoint(
#     repo_id=REPO_ID,
#     huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
#     task="conversational",  # ← 关键！改成 conversational
#     temperature=0.1,
#     max_new_tokens=1024,
# )


model_id = "Qwen/Qwen2.5-1.5B-Instruct"  # 或 7B 如果内存够
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto",
    low_cpu_mem_usage=True,
    )
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=1024,
    temperature=0.1,
    do_sample=True,
    return_full_text=False
)
llm = HuggingFacePipeline(pipeline=pipe)

def build_qa_chain(retriever):
    # 1. 历史感知 retriever（把历史转成 standalone question）
    contextualize_q_system_prompt = """根据聊天历史和最新问题，生成一个独立的问题（standalone question），以便在没有历史的情况下也能理解。
    只输出问题本身，不要加额外解释。"""
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # 2. 回答提示（你的中文增强版）
    system_prompt = """你是一个专业的视频助手。请根据以下带时间戳的视频文案，回答用户的问题。

    要求：
    1. 尽量在回答中引用[时间戳]信息，帮助用户定位。
    2. 如果文案中没有相关信息，请直接回答“视频中没有提到这一点”。
    3. 请始终使用中文回答。

    已知视频内容（上下文）：
    {context}

    用户问题：{input}
    助手回答："""
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    # 3. 组合文档链
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    # 4. 最终 retrieval chain（带历史）
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    logging.info("现代 RAG + 多轮对话 QA 链构建完成")
    return rag_chain

def query_video(chain, question: str, chat_history: list = None):
    if chat_history is None:
        chat_history = []

    # 格式化历史为 LangChain Message
    history_msgs = []
    for q, a in chat_history:
        history_msgs.extend([HumanMessage(content=q), AIMessage(content=a)])

    try:
        result = chain.invoke({
            "input": question,
            "chat_history": history_msgs,
        })
        answer = result["answer"]
        sources = [doc.page_content for doc in result.get("context", [])][:2]  # context 就是 source docs

        print(f"\n{answer}")
        # print(f"参考来源: {sources}")

        # 更新历史（供下次用）
        chat_history.append((question, answer))
        return answer, chat_history
    except Exception as e:
        logging.error(f"查询出错: {e}")
        return "抱歉，处理您的请求时出错了。", chat_history
    
def generate_summary(retriever):
    all_docs = retriever.invoke("视频主要内容")
    context_text = "\n".join([doc.page_content for doc in all_docs])

    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的视频内容分析助手。"),
        ("human",
         """以下是视频转录文本：
        {context}

        请完成：
        1. 一句话概括核心主题
        2. 列出 3–5 个关键点（带大致时间戳）
        3. 使用中文总结"""
        )
    ])

    chain = summary_prompt | llm | StrOutputParser()

    summary = chain.invoke({"context": context_text})
    return summary
    
