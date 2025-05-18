# 임시 신고 내역 입력기

import config
from firebase_admin import credentials, db
from datetime import datetime

now = datetime.now()
report_id = now.strftime('%Y%m%d%H%M%S%f')

ref = db.reference('Report')
report = ref.get()

data = {
    'date': '2025-05-18',
    'file': '20250518120523_userid.jpg',
    'violation': '헬멧 미착용',
    'about': '헬멧 미착용으로 신고'
}

ref.child(report_id).set(data)