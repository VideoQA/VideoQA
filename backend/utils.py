import os
import logging

def cleanup_temp_files(files: list):
    for file in files:
        if os.path.exists(file):
            os.remove(file)
            logging.info(f"清理文件: {file}")