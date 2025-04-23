from roboflow import Roboflow
from dotenv import load_dotenv
import cv2
import os

load_dotenv()  # .env 파일에서 API 키 로드
rf = Roboflow(api_key=os.getenv("MY_API_KEY"))

# Roboflow 프로젝트/모델 정보 입력
project = rf.workspace("kickbord").project("electric-kick-board-vjfvv")
model = project.version(3).model  # 버전 번호 확인

# 이미지 경로 설정
image_folder_path = "image"
image_paths = [os.path.join(image_folder_path, f) 
              for f in os.listdir(image_folder_path) 
              if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

# 추론 및 결과 시각화
for img_path in image_paths:
    prediction = model.predict(img_path, confidence=40, overlap=30)
    
    # Roboflow 내장 함수로 결과 표시 (바운딩 박스 자동 생성)
    prediction.plot()  # 이미지 팝업
    # prediction.save("result.jpg")  # 파일 저장
