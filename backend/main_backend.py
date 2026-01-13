from audio_extractor import extract_audio
from transcriber import transcribe_audio
from retriever import build_retriever
from qa_chain import build_qa_chain, query_video, generate_summary

import asyncio

async def main():
    video_path = "backend/input_video.mp4"
    audio_path = extract_audio(video_path)
    transcript_path = await transcribe_audio(audio_path, model_size="base", translate_to="zh-cn")
    retriever = build_retriever(transcript_path)
    summary = generate_summary(retriever)
    
    # All lines below must match the indentation level of video_path above
    print("视频摘要:", summary)
    history = []
    while True:
        q = input("\n请输入问题 (输入 quit 退出): ")
        if q.lower() in ['quit', 'exit']:
            break
        # Note: Ensure video_rag_chain is defined; you might need:
        # video_rag_chain = build_qa_chain(retriever) 
        ans, history = query_video(video_rag_chain, q, history)
        print("回答:", ans)

if __name__ == "__main__":
    asyncio.run(main())