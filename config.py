import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
SDP_URL: str = os.getenv("SDP_URL", "https://helpme.gkfs.com.ua").rstrip("/")
SDP_API_KEY: str = os.getenv("SDP_API_KEY", "")
SDP_SSL_VERIFY: bool = os.getenv("SDP_SSL_VERIFY", "true").lower() != "false"

ACCESS_MODE: str = os.getenv("ACCESS_MODE", "general")  # 'general' або 'restricted'
ACCESS_PASSWORD: str = os.getenv("ACCESS_PASSWORD", "")

MAX_PHOTOS: int = int(os.getenv("MAX_PHOTOS", "5"))
