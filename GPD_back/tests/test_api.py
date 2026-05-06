import requests

#url = "https://farah040-gpd-service.hf.space/analyze"
url = "http://127.0.0.1:8001/analyze"
# جرب إرسال ملف فارغ أو بيانات بسيطة لتختبر هل يستقبل الطلب
files = {'file': ('test.txt', b'hello world', 'text/plain')}

try:
    response = requests.post(url, files=files, timeout=20)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"حدث خطأ في الاتصال: {e}")