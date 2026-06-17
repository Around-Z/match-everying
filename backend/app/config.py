import os
from dotenv import load_dotenv

load_dotenv()

# DeepSeek — 聊天（UI生成 + 匹配解释）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_CHAT_MODEL = "deepseek-chat"

# 智谱（ZhipuAI）— 嵌入向量
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY", "")
ZHIPUAI_EMBEDDING_MODEL = "embedding-2"
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1024"))

# Milvus — 向量数据库
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
MILVUS_COLLECTION = os.getenv("MILVUS_COLLECTION", "matching_vectors")

# Privacy
MATCH_VISIBILITY_THRESHOLD = float(os.getenv("MATCH_VISIBILITY_THRESHOLD", "0.5"))

# MySQL (Docker)
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3307"))
MYSQL_USER = os.getenv("MYSQL_USER", "matching_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "matching_pass_2026")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "matching_platform")
