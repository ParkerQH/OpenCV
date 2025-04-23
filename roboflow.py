from roboflow import Roboflow
from dotenv import load_dotenv
import os

load_dotenv()  # .env 파일에서 API 키 로드
rf = Roboflow(api_key=os.getenv("MY_API_KEY"))

