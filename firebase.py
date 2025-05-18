import firebase_admin
from firebase_admin import credentials, db

# 서비스 계정 키로 초기화
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://kts-dataset-default-rtdb.firebaseio.com'
})

# 경로
ref = db.reference('Conclusion')

# 데이터 준비
data = {
    'value': '원하는 데이터 값',
    # 'id': 나중에 push로 생성된 id를 넣을 수 있음
}

# push로 데이터 추가 (랜덤 id 생성)
new_ref = ref.push(data)

# 생성된 id를 데이터 내부에도 저장하고 싶다면 update로 추가
new_ref.update({'id': new_ref.key})

# print(ref.get())
