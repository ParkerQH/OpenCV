import cv2
import numpy as np
import os
import tempfile
import time
import firebase_config
from firebase_admin import storage, firestore

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
        annotated_image = results[0].plot()

        # 가장 높은 confidence 값 추출
        boxes = results[0].boxes
        if len(boxes) == 0:
            top_confidence = 0.0
            top_class = "No detection"
        else:
            confidences = boxes.conf.cpu().numpy()
            class_ids = boxes.cls.cpu().numpy().astype(int)
            max_idx = np.argmax(confidences)
            top_confidence = float(confidences[max_idx])
            top_class = model.names[class_ids[max_idx]]

        # 분석 이미지 저장 (Storage)
        conclusion_blob = bucket.blob(f'conclusion/{file_url}')
        _, temp_annotated = tempfile.mkstemp(suffix='.jpg')
        cv2.imwrite(temp_annotated, annotated_image)
        conclusion_blob.upload_from_filename(temp_annotated)
        conclusion_url = conclusion_blob.public_url

        # Firestore에 결과 저장
        db_fs = firestore.client()
        doc_id = os.path.splitext(file_url)[0]
        conclusion_data = {
            'violation': "헬멧미착용",
            'confidence': top_confidence,   # confidence score
            'detectedBrand': top_class,
            'imageUrl': conclusion_url
        }
        db_fs.collection('Conclusion').document(doc_id).set(conclusion_data)

        print(f"✅ Processed image: {file_url}\n")

    finally:
        # 파일 삭제 재시도 로직
        for _ in range(3):
            try:
                os.unlink(temp_file.name)
                break
            except PermissionError:
                time.sleep(0.3)
        if 'temp_annotated' in locals():
            try:
                os.unlink(temp_annotated)
            except:
                pass

# 실시간 리스너 설정 (Realtime Database는 그대로 사용)
def callback(event):
    report_id = event.path.split('/')[-1]
    report_data = event.data
    
    if report_data and 'file' in report_data:
        print(f"New report detected! ID: {report_id}")
        process_image(report_data['file'])

if __name__ == "__main__":
    from firebase_admin import db  # 실시간 리스너만 사용
    ref = db.reference('Report')
    ref.listen(callback)
    print("🔥 실시간 감지를 시작합니다. 종료 : Ctrl+C 🔥")
    
    try:
        while True:
            time.sleep(1)  # CPU 사용량 최적화
    except KeyboardInterrupt:
        print("\n 실시간 감지를 중지합니다!")
