import cv2
from datetime import datetime
import os
from ultralytics import YOLO
from picamera2 import Picamera2
import time
import firebase_config
import uuid
from firebase_admin import credentials, storage, firestore
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from dotenv import load_dotenv
import pytz

# 모델 경로 설정
MODEL_PATH = '/home/admin/Desktop/YOLO11/best2.pt'  # 라즈베리파이 경로에 맞게 수정
model = YOLO(MODEL_PATH)

user_id = "admin"

kst = pytz.timezone('Asia/Seoul')

# 이미지 저장 폴더 생성
SAVE_DIR = 'captures'
os.makedirs(SAVE_DIR, exist_ok=True)

def detect_kickboard_local(image, conf_threshold=0.7):
    results = model(image)[0]
    filtered = []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        if conf >= conf_threshold:
            label = model.names[cls_id]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            filtered.append({
                'class': label,
                'confidence': conf,
                'box': (x1, y1, x2, y2)
            })

    return filtered

def draw_detections(image, detections):
    for d in detections:
        x1, y1, x2, y2 = d['box']
        label = d['class']
        conf = d['confidence']
        text = f"{label} {conf:.2f}"

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 255), 2)
        cv2.putText(image, text, (x1 + 5, y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    return image

# ?? 카메라 초기화
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()

print("킥보드 감지를 시작합니다. Ctrl+C 또는 ESC 키로 종료하세요.")

last_saved = None  # 최근 저장 시간

try:
    while True:
        frame = picam2.capture_array()
        detections = detect_kickboard_local(frame)
        frame = draw_detections(frame, detections)

        # 킥보드 감지되면 3초 간격으로 저장
        for d in detections:
            if d['class'] == 'kickboard':
                now = datetime.now(kst)
                if last_saved is None or (now - last_saved).total_seconds() > 10:
                    timestamp = now.strftime("%Y%m%d_%H%M%S")
                    save_path = os.path.join(SAVE_DIR, f"kickboard_{timestamp}.jpg")
                    cv2.imwrite(save_path, frame)
                    print(f"?? 킥보드 감지! 이미지 저장됨: {save_path}")
                    last_saved = now
                    
                    report_id = uuid.uuid4().hex

                    # 파일 확장자 추출
                    _, file_extension = os.path.splitext(save_path)

                    # Storage에 저장할 경로 생성
                    storage_path = f"report_raspberry/{report_id}{file_extension}"

                    # Storage에 파일 업로드
                    bucket = storage.bucket()
                    blob = bucket.blob(storage_path)
                    blob.upload_from_filename(save_path)
                    blob.make_public()
                    file_url = blob.public_url

                    #위, 경도 설정
                    lat, lon = "37.2222", "127.2222"

                    # Firestore 클라이언트 가져오기
                    db_fs = firestore.client()

                    data = {
                        "date": datetime.now(kst),
                        "gpsInfo": f"{lat} {lon}",
                        "imageUrl": file_url,
                        "userId": "Raspberry Pi",
                        "violation" : "Raspberry Pi 감지"
                    }

                    # Firestore에 저장 (컬렉션: Report, 문서: report_id)
                    db_fs.collection("Report_Raspberry").document(report_id).set(data)
                break

        cv2.imshow("Kickboard Detection", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC 키
            break

except KeyboardInterrupt:
    print("프로그램 종료 중...")

cv2.destroyAllWindows()
picam2.stop()
