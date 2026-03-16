import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # DeepSeek API配置
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_API_BASE = "https://api.deepseek.com"
    
    # 模型路径（当使用本地模型时）
    # MODEL_PATH = os.getenv("MODEL_PATH", "./models/frailty_model.pth")
    
    # 文件上传设置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}