import requests
from requests.adapters import HTTPAdapter

filename = "http.txt"
result = "HTTP_URL.txt"

requests.packages.urllib3.disable_warnings()
requests.adapters.DEFAULT_RETRIES = 5
f2 = open(result, 'w')
with open(filename, 'r') as f1:
    for url in f1:
        url = url.strip()
        # headers = {'Connection': 'close'}
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
                'Connection': 'close'
            }
            sess = requests.Session()
            sess.mount('http://', HTTPAdapter(max_retries=3))
            sess.mount('https://', HTTPAdapter(max_retries=3))
            sess.keep_alive = False  # 关闭多余连接
            response = requests.get(url, headers=headers, stream=True, verify=False, timeout=(2, 2))
            if response.status_code == 200:
                f2.write(url)
                f2.write('\n')
                print(url)
                response.close()
        except Exception as e:
            print(e)
f2.close()
