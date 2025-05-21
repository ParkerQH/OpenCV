import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from dotenv import load_dotenv

def get_exif_data(image_path):
    image = Image.open(image_path)
    exif_data = image._getexif()
    if not exif_data:
        return None
    exif = {}
    for tag, value in exif_data.items():
        decoded = TAGS.get(tag, tag)
        if decoded == "GPSInfo":
            gps_data = {}
            for t in value:
                sub_decoded = GPSTAGS.get(t, t)
                gps_data[sub_decoded] = value[t]
            exif[decoded] = gps_data
        else:
            exif[decoded] = value
    return exif

def get_lat_lon(exif_data):
    def _convert_to_degrees(value):
        # IFDRational 객체를 float로 변환
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + m/60 + s/3600

    gps_info = exif_data.get("GPSInfo")
    if not gps_info:
        return None, None
    
    lat = _convert_to_degrees(gps_info["GPSLatitude"])
    if gps_info["GPSLatitudeRef"] != "N":
        lat = -lat
        
    lon = _convert_to_degrees(gps_info["GPSLongitude"])
    if gps_info["GPSLongitudeRef"] != "E":
        lon = -lon
        
    return lat, lon


# 사용 예시
exif = get_exif_data("image/ex/KakaoTalk_20250519_084001477_03.jpg")
lat, lon = get_lat_lon(exif)
print("위도:", lat, "경도:", lon)


import requests

def reverse_geocode(lat, lon, api_key):
    url = "https://api.vworld.kr/req/address"
    params = {
        "service": "address",
        "request": "getAddress",
        "crs": "epsg:4326",
        "point": f"{lon},{lat}",  # 경도,위도 순서
        "format": "json",
        "type": "both",  # 도로명주소와 지번주소 모두 반환
        "key": api_key
    }
    response = requests.get(url, params=params)

    road_addr, parcel_addr = None, None
    
    if response.status_code == 200:
        data = response.json()
        if data['response']['status'] == 'OK':
            # 결과 배열 순회
            for result in data['response']['result']:
                addr_type = result.get('type')
                text = result.get('text')
                
                if addr_type == 'road':
                    road_addr = text
                elif addr_type == 'parcel':
                    parcel_addr = text
                    
    return road_addr, parcel_addr

# 사용 예시
load_dotenv()

api_key = os.getenv('VWorld_API') 
road_addr, parcel_addr = reverse_geocode(lat, lon, api_key)
print("도로명주소:", road_addr)
print("지번주소:", parcel_addr)