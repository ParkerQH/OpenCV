import cv2
import numpy as np
import os
import tempfile
import time
import firebase_config
from firebase_admin import storage, firestore
from google.cloud.firestore import Client as FirestoreClient
from ultralytics import YOLO

# YOLOv11s 모델 로드
model = YOLO("runs/detect/train_yolov11s/weights/best.pt")

def process_image(file_url):
    # 임시 파일 생성
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    try:
        # 이미지 다운로드
        bucket = storage.bucket()
        blob = bucket.blob(file_url)
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

# Firestore 실시간 리스너 설정
def on_snapshot(col_snapshot, changes, read_time):
    # 초기 스냅샷은 무시 (최초 1회 실행 시 건너뜀)
    # if not hasattr(on_snapshot, "initialized"):
    #     on_snapshot.initialized = True
    #     return
    
    for change in changes:
        if change.type.name == 'ADDED':  # 새 문서가 추가될 때만 반응
            doc_id = change.document.id
            doc_data = change.document.to_dict()
            
            if 'file' in doc_data:
                print(f"🔥 New Firestore report: {doc_id}")
                process_image(doc_data['file_url'])

if __name__ == "__main__":
    # Firestore 클라이언트 초기화
    db_fs: FirestoreClient = firestore.client()
    
    # Report 컬렉션 감시 시작
    report_col = db_fs.collection('Report')
    listener = report_col.on_snapshot(on_snapshot)
    
    print("🔥 Firestore 실시간 감시 시작 (종료: Ctrl+C) 🔥")
    
    try:
        # 무한 대기 (Firestore 리스너는 백그라운드 스레드에서 실행)
        while True:
            time.sleep(3600)  # CPU 사용량 최소화
    except KeyboardInterrupt:
        listener.unsubscribe()  # 리스너 종료
        print("\n🛑 Firestore 감시를 안전하게 종료합니다.")
