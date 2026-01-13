import whisper
import logging
from googletrans import Translator

#音频转文字
# 辅助函数：将秒转换为 [mm:ss.mmm] 格式
def format_timestamp(seconds: float):
    tdelta = seconds
    hours = int(tdelta // 3600)
    minutes = int((tdelta % 3600) // 60)
    secs = tdelta % 60
    return f"[{hours:02d}:{minutes:02d}:{secs:06.3f}]"

async def transcribe_audio(audio_path: str, model_size: str = "base", translate_to: str = None) -> str:
    try:
        logging.info("加载模型中...")
        model = whisper.load_model(model_size)
        
        # 1. 执行转录
        # verbose=False 避免控制台刷屏
        result = model.transcribe(audio_path)
        segments = result["segments"]
        logging.info("转录完成")

        translator = Translator() if translate_to else None
        processed_lines = []

        # 2. 处理每一个带时间戳的片段
        for segment in segments:
            start = format_timestamp(segment['start'])
            end = format_timestamp(segment['end'])
            text = segment['text'].strip()

            # 如果需要翻译
            if translate_to and text:
                try:
                    translated = await translator.translate(text, dest=translate_to)
                    text = translated.text
                except Exception as e:
                    logging.warning(f"翻译片段失败: {e}")

            # 组合成：[00:00:01.200 -> 00:00:04.500] 文本内容
            processed_lines.append(f"{start} --> {end} {text}")

        # 3. 写入文件
        processed_path = "processed_transcript_timestamped.txt"
        with open(processed_path, "w", encoding="utf-8") as f:
            f.write("\n".join(processed_lines))
            
        logging.info(f"带时间戳的文本已保存至: {processed_path}")
        return processed_path

    except Exception as e:
        logging.error(f"出错详情: {e}")
        raise e