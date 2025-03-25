from roboflow import Roboflow
from dotenv import load_dotenv
import cv2
import numpy as  np

# YOLOv8 모델 로드
from ultralytics import YOLO
model = YOLO("runs/detect/train/weights/best.pt")  # .pt 모델 파일 경로로 변경

# 이미지 로드
image_path = "image/pic12.jpg"  # 분석할 이미지 경로
image = cv2.imread(image_path)

# 모델을 통해 이미지 분석
results = model(image)

# 분석 결과 출력
results[0].show()  # 결과를 화면에 표시