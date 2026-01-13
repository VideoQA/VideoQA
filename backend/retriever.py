from langchain_community.document_loaders import TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging


def build_retriever(transcript_path: str):
    # 1. 加载带时间戳的文档
    loader = TextLoader(transcript_path, encoding='utf-8')
    raw_documents = loader.load()

    # 2. 切分文档
    # 对于带时间戳的文本，我们希望每个 chunk 包含完整的时间戳和内容
    # 如果你的视频很长，chunk_size 可以设大一点（比如 300-500 字），包含相邻的几个时间戳片段
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=50,
        separators=["\n\n", "\n", " "] # 优先按行切分，保证时间戳不被截断
    )
    documents = text_splitter.split_documents(raw_documents)
    logging.info(f"文档切分完成，共有 {len(documents)} 个片段")

    # 3. 初始化 Embeddings
    # 注意：初次运行会下载模型，建议国内环境配置镜像
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'} # 如果有 GPU 可以改为 'cuda' 或 'mps'
    )

    # 4. 构建向量检索器 (FAISS)
    vectorstore = FAISS.from_documents(documents, embeddings)
    # search_kwargs={"k": 3} 表示检索最相关的 3 个片段
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # 5. 构建关键词检索器 (BM25)
    bm25_retriever = BM25Retriever.from_documents(documents)
    bm25_retriever.k = 3

    # 6. 融合检索器 (Ensemble)
    # 结合了语义理解 (Vector) 和 关键词匹配 (BM25)
    ensemble_retriever = EnsembleRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        weights=[0.4, 0.6] # 视频问答中关键词往往更重要，略微调高 BM25 权重
    )

    logging.info("带时间戳的检索器构建完成")
    return ensemble_retriever