from roboflow import Roboflow
from dotenv import load_dotenv
import os

# .env 파일의 환경 변수를 로드
load_dotenv()

# Roboflow API 키로 데이터셋 다운로드
api_key = os.getenv('MY_API_KEY') 
rf = Roboflow(api_key=api_key)
project = rf.workspace("kickbord").project("helmet-dxttm")
version = project.version(1)
dataset = version.download("yolov8")