import os
import firebase_config
from firebase_admin import credentials, storage, firestore
from datetime import datetime

now = datetime.now()
report_id = now.strftime('%Y%m%d%H%M%S%f')
user_id = 'admin'

# 업로드할 파일 경로
local_file_path = 'image/ex/KakaoTalk_20250518_171537204_03.jpg'

# 파일 확장자 추출
_, file_extension = os.path.splitext(local_file_path)

# Storage에 저장할 경로 생성
storage_path = f'report/{report_id}_{user_id}{file_extension}'

# Storage에 파일 업로드
bucket = storage.bucket()
blob = bucket.blob(storage_path)
blob.upload_from_filename(local_file_path)
blob.make_public()
file_url = blob.public_url

# Firestore 클라이언트 가져오기
db_fs = firestore.client()

data = {
    'date': '2025-05-18',
    'file': f'{report_id}_{user_id}{file_extension}',
    'violation': '헬멧 미착용',
    'about': '헬멧 미착용으로 신고',
    'gpsInfo' : '위도: 37.2792405 경도: 127.0296529',
    'place': '화성시 동탄순환대로',
    'file_url': file_url
}

# Firestore에 저장 (컬렉션: Report, 문서: report_id)
db_fs.collection('Report').document(report_id).set(data)
