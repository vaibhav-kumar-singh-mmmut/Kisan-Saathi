import urllib.request
import urllib.parse
import json

url = 'http://127.0.0.1:8000/api/v1/predict'
file_path = r'C:\Users\mrala\.gemini\antigravity-ide\brain\d1733f3a-75c6-40c2-b806-c4bbaf8e3c81\.user_uploaded\media_1788007555682.png'
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'

with open(file_path, 'rb') as f:
    img_data = f.read()

body = (
    b'--' + boundary.encode() + b'\r\n'
    b'Content-Disposition: form-data; name="image"; filename="image.png"\r\n'
    b'Content-Type: image/png\r\n\r\n' +
    img_data + b'\r\n'
    b'--' + boundary.encode() + b'--\r\n'
)

req = urllib.request.Request(url, data=body)
req.add_header('Content-Type', 'multipart/form-data; boundary=' + boundary)

try:
    response = urllib.request.urlopen(req)
    print(response.read().decode())
except Exception as e:
    print('Error:', e)
