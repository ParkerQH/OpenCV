import os
import firebase_config
import uuid
from firebase_admin import credentials, storage, firestore
from datetime import datetime
import pytz

# 한국 시간대 객체 생성
kst = pytz.timezone('Asia/Seoul')

notice_id = uuid.uuid4().hex

title = input('제목을 입력하세요 >>> ')
content = input('내용을 입력하세요 >>> ')

# Firestore 클라이언트 가져오기
db_fs = firestore.client()

data = {
    "title": title,
    "content": content,
    "create_date": datetime.now(kst)
}

# Firestore에 저장 (컬렉션: Report, 문서: report_id)
db_fs.collection("Notices").document(notice_id).set(data)
