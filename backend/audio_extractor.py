# Extracts audio from a video file and saves it as a WAV file.
import moviepy as mp
import logging
import os

def extract_audio(video_path: str, audio_path: str = "data/temp_audio.wav") -> str:
    try:
        video = mp.VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
        logging.info(f"音频提取完成: {audio_path}")
        return audio_path
    except Exception as e:
        logging.error(f"音频提取失败: {e}")
        raise ValueError("视频文件无效或提取失败")