import cv2
import numpy as np
import os
import firbase_config
from ultralytics import YOLO
# YOLOv11s 모델 로드
model = YOLO("runs/detect/train_yolov11s/weights/best.pt")

# 이미지 폴더 경로
image_folder_path = "image"

# 폴더 내의 모든 이미지 파일 경로
image_paths = [os.path.join(image_folder_path, file) 
               for file in os.listdir(image_folder_path) 
               if file.endswith(".jpg") or file.endswith(".png") or file.endswith(".jpeg")]

# 폴더 내의 모든 이미지 파일 분석
for image_path in image_paths:
    # 이미지 로드
    image = cv2.imread(image_path)
    
    # 모델을 통해 이미지 분석, confidence score >= 0.8
    results = model(image, conf=0.8)
    
    # 분석 결과 출력
    results[0].show()  # 결과를 화면에 표시
    print(f"Image: {image_path} processed.")
