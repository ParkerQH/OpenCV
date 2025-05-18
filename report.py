# 임시 신고 내역 입력기
import os
import firebase_config
from firebase_admin import credentials, db, storage
from datetime import datetime

now = datetime.now()
report_id = now.strftime('%Y%m%d%H%M%S%f')
user_id = 'admin'

# 업로드할 파일 경로
local_file_path = 'image/pic1.jpg'

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

ref = db.reference('Report')
report = ref.get()

data = {
    'date': '2025-05-18',
    'file': f'{report_id}_{user_id}{file_extension}',
    'violation': '헬멧 미착용',
    'about': '헬멧 미착용으로 신고',
    'place':'화성시 동탄순환대로',
    'file_url':file_url
}

ref.child(report_id).set(data)