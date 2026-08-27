import urllib.request
import urllib.error

url = 'https://api.agromonitoring.com/agro/1.0/stats/ndvi?polyid=6a8542d10ece801e53e03a99&dt=1787011200&appid=35c3682795c14edee7dd512a190128e5'
try:
    urllib.request.urlopen(url)
except urllib.error.HTTPError as e:
    print(e.code, e.fp.read().decode('utf-8'))
except Exception as e:
    print(e)
