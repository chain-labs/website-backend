# config.py
from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env into os.environ

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is not set")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 31536000 # 1 year