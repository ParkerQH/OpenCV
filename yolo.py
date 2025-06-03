import cv2
import numpy as np
import os
import tempfile
import time
import requests
import firebase_config
from firebase_admin import storage, firestore
from google.cloud.firestore import Client as FirestoreClient
from ultralytics import YOLO
from datetime import datetime
from dotenv import load_dotenv
from inference_sdk import InferenceHTTPClient

# YOLOv11s 모델 로드
model = YOLO("runs/detect/train_yolov11s/weights/best.pt")

#Roboflow Inference API 설정
load_dotenv()
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key= os.environ.get('ROBOFLOW_API_KEY')
)


def process_image(imageUrl, date, userId, violation, doc_id):
    temp_annotated = None  # 초기화
    try:
        # 이미지 다운로드
        response = requests.get(imageUrl)
        response.raise_for_status()

        # 메모리에서 이미지 디코딩
        image = cv2.imdecode(
            np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR
        )

        #temp에 넣은 이미지 전처리
        h, w = image.shape[:2]
        if h > w :
            resized = cv2.resize(image, (500,700), interpolation=cv2.INTER_AREA)
        else :
            resized = cv2.resize(image, (500,500), interpolation=cv2.INTER_AREA)
        img = resized.copy()

        #헬멧 착용여부 판단
        result_kickboard = CLIENT.infer(resized, model_id="kickboard-22-jt3v1/1")
        print('result: ', result_kickboard)

        helmet_status = None
        traffic_violation_detection = '위반사항 없음'
        result_helmet = None
        top_helmet_confidence = 0.0

        if any(item['confidence'] > 0.1 for item in result_kickboard['predictions']) :

            result_person = CLIENT.infer(resized, model_id="person-469rx-3u095/1")
            print('result: ', result_person)


            if any(item['confidence'] > 0.1 for item in result_person['predictions']) :

                result_helmet = CLIENT.infer(resized, model_id="helmet-nw6lg-i02zn/1")
                print('result: ', result_helmet)

                if any(item['confidence'] > 0.1 for item in result_helmet['predictions'])  :
                    helmet_status = '착용'
                    img = object_detection(result_helmet['predictions'], img)
                else:
                    helmet_status = '미착용'
                    traffic_violation_detection = '헬멧 미착용'
                
                helmet_preds = result_helmet.get("predictions", [])

                if helmet_preds:
                    confidences = [p["confidence"] for p in helmet_preds]
                    top_helmet_confidence = max(confidences)
                else:
                    top_helmet_confidence = 0.0
            else:
                traffic_violation_detection = '사람 감지 실패'
                #return jsonify({'위반 감지': traffic_violation_detection})
        else:
            traffic_violation_detection = '킥보드 감지 실패'
            #return jsonify({'위반 감지': traffic_violation_detection})
        
        

        # YOLO 분석 및 결과 표시
        results = model(image, conf=0.3)
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
        bucket = storage.bucket()
        conclusion_blob = bucket.blob(f"Conclusion/{doc_id}.jpg")

        # 임시 파일 생성 (분석 이미지용)
        _, temp_annotated = tempfile.mkstemp(suffix=".jpg")
        cv2.imwrite(temp_annotated, img)
        conclusion_blob.upload_from_filename(temp_annotated)
        conclusion_url = conclusion_blob.public_url

        # 사진 지번 주소 출력
        api_key = os.getenv("VWorld_API")
        db_fs = firestore.client()
        doc_ref = db_fs.collection("Report").document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            doc_data = doc.to_dict()
            gps_info = doc_data.get("gpsInfo")
        if gps_info:
            lat_str, lon_str = gps_info.strip().split()
            lat = float(lat_str)
            lon = float(lon_str)
            parcel_addr = reverse_geocode(lat, lon, api_key)

        if traffic_violation_detection in ("사람 감지 실패", "킥보드 감지 실패"):
            # Firestore에 결과 저장
            doc_id = f"conclusion_{doc_id}"  # 문서 ID 생성
            conclusion_data = {
                "date" : date,
                "userId" : userId,
                "aiConclusion" : traffic_violation_detection,
                "violation": violation,
                "confidence": top_helmet_confidence,
                "detectedBrand": top_class,
                "imageUrl": conclusion_url,
                "region": parcel_addr,
                "gpsInfo": f"{lat} {lon}",
                "result": "반려",
                "reason": traffic_violation_detection
            }
            db_fs.collection("Conclusion").document(doc_id).set(conclusion_data)

            print(f"✅ 분석된 사진 url : {imageUrl}\n")

        # Firestore에 결과 저장
        doc_id = f"conclusion_{doc_id}"  # 문서 ID 생성
        conclusion_data = {
            "date" : date,
            "userId" : userId,
            "aiConclusion" : traffic_violation_detection,
            "violation": violation,
            "confidence": top_helmet_confidence,
            "detectedBrand": top_class,
            "imageUrl": conclusion_url,
            "region": parcel_addr,
            "gpsInfo": f"{lat} {lon}",
            "result": "미확인"
        }
        db_fs.collection("Conclusion").document(doc_id).set(conclusion_data)

        print(f"✅ 분석된 사진 url : {imageUrl}\n")

    except Exception as e:
        print(f"❌ 분석 중 에러 발생 {imageUrl}: {str(e)}")
    finally:
        if temp_annotated and os.path.exists(temp_annotated):
            try:
                os.unlink(temp_annotated)
            except:
                pass


def reverse_geocode(lat, lon, api_key):
    url = "https://api.vworld.kr/req/address"
    params = {
        "service": "address",
        "request": "getAddress",
        "crs": "epsg:4326",
        "point": f"{lon},{lat}",
        "format": "json",
        "type": "parcel",
        "key": api_key,
    }
    response = requests.get(url, params=params)

    # 반환값 단순화
    if response.status_code == 200:
        data = response.json()
        if data["response"]["status"] == "OK":
            # 첫 번째 결과에서 지번주소 추출
            result = data["response"]["result"][0]
            if "text" in result:
                return result["text"]  # 지번주소만 반환
    return None


# Firestore 실시간 리스너 설정
def on_snapshot(col_snapshot, changes, read_time):
    # 초기 스냅샷은 무시 (최초 1회 실행 시 건너뜀)
    # if not hasattr(on_snapshot, "initialized"):
    #     on_snapshot.initialized = True
    #     return

    for change in changes:
        if change.type.name == "ADDED":  # 새 문서가 추가될 때만 반응
            doc_id = change.document.id
            doc_data = change.document.to_dict()

            if "imageUrl" in doc_data:
                print(f"🔥 새로운 신고 감지  : {doc_id}")
                process_image(doc_data["imageUrl"], doc_data["date"], doc_data["userId"], doc_data["violation"], doc_id)


def object_detection(predictions, img):
    for prediction in predictions:
        centerx = int(prediction['x'])
        centery = int(prediction['y'])
        symmetric = int(prediction['width'])/2
        horizontal = int(prediction['height'])/2
        
        x1 = int(centerx - symmetric)
        y1 = int(centery - horizontal)
        x2 =  int(centerx + symmetric)
        y2 =  int(centery + horizontal)
        
        label = prediction['class']
        #label = str('Helmet')
        conf = prediction['confidence']
        #conf = 0.84
        text = str(label) + ' ' + str(conf)

        cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 2)
        cv2.putText(img, text, (x1+5, y1+20 ), cv2.FONT_HERSHEY_PLAIN, 1.2, (255, 0, 255), 1)
    return img


if __name__ == "__main__":
    # Firestore 클라이언트 초기화
    db_fs: FirestoreClient = firestore.client()

    # Report 컬렉션 감시 시작
    report_col = db_fs.collection("Report")
    listener = report_col.on_snapshot(on_snapshot)

    print("🔥 Firestore 실시간 감지 시작 (종료: Ctrl+C) 🔥")

    try:
        # 무한 대기 (Firestore 리스너는 백그라운드 스레드에서 실행)
        while True:
            time.sleep(3600)  # CPU 사용량 최소화
    except KeyboardInterrupt:
        listener.unsubscribe()  # 리스너 종료
        print("\n🛑 Firestore 실시간 감지를 종료합니다.")
