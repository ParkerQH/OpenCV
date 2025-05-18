import cv2
import numpy as np
import os
import tempfile
import time
import firebase_config
from firebase_admin import db, storage
from ultralytics import YOLO

# YOLOv11s 모델 로드
model = YOLO("runs/detect/train_yolov11s/weights/best.pt")

def process_image(file_url):
    # 임시 파일 생성
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    try:
        # 이미지 다운로드
        bucket = storage.bucket()
        blob = bucket.blob(f'report/{file_url}')
        blob.download_to_filename(temp_file.name)

        # 파일 잠금 방지 읽기
        with open(temp_file.name, 'rb') as f:
            image_data = f.read()
        image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)

        # YOLO 분석 및 결과 표시
        results = model(image, conf=0.8)
        results[0].show()  # GUI 표시
        time.sleep(0.5)  # GUI 초기화 대기

        print(f"Processed image: {file_url}\n")

        ref
    finally:
        # 파일 삭제 재시도 로직
        for _ in range(3):
            try:
                os.unlink(temp_file.name)
                break
            except PermissionError:
                time.sleep(0.3)


# 실시간 리스너 설정
def callback(event):
    report_id = event.path.split('/')[-1]
    report_data = event.data
    
    if report_data and 'file' in report_data:
        print(f"New report detected! ID: {report_id}")
        process_image(report_data['file'])

if __name__ == "__main__":
    ref = db.reference('Report')
    ref.listen(callback)
    print("🔥 실시간 감지를 시작합니다. 종료 : Ctrl+C 🔥")
    
    try:
        while True:
            time.sleep(1)  # CPU 사용량 최적화
    except KeyboardInterrupt:
        print("\n 실시간 감지를 중지합니다!")
