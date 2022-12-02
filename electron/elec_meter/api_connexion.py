import requests
headers = requests.utils.default_headers()
url = "http://3.19.22.2:7070/openapi/device/downlink/create"
token = "0h2PPw2AlcKM0R1xXymkFA=="
headers.update({
    "Accept-Encoding": "gzip", "Content-Length": "286", "Content-Type": "application/json",
    'X-Access-Token': '{0}'.format(token),
    "User-Agent": "python-requests/2.26.0"
})
fPORT = 8






