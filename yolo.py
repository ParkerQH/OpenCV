from roboflow import Roboflow
from dotenv import load_dotenv
import cv2
import numpy as np
import os

# YOLOv8 모델 로드
from ultralytics import YOLO
model = YOLO("runs/detect/train/weights/best.pt")  # .pt 모델 파일 경로로 변경

# 이미지 폴더 경로
image_folder_path = "image"  # 분석할 이미지 폴더 경로

# 폴더 내의 모든 이미지 파일 경로
image_paths = [os.path.join(image_folder_path, file) 
               for file in os.listdir(image_folder_path) 
               if file.endswith(".jpg") or file.endswith(".png") or file.endswith(".jpeg")]

# 폴더 내의 모든 이미지 파일 분석
for image_path in image_paths:
    # 이미지 로드
    image = cv2.imread(image_path)
    
    # 모델을 통해 이미지 분석
    results = model(image)
    
    # 분석 결과 출력
    results[0].show()  # 결과를 화면에 표시
    print(f"Image: {image_path} processed.")
