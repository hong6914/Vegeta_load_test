
import sys
import requests


###############################################################################


fullURL = 'http://localhost:5555/'
res = requests.get('{}test/version'.format(fullURL))
if res.ok:
    print(res.json())
else:
    print('bad...')

res = requests.post('{}test/update'.format(fullURL))
res = requests.get('{}test/count'.format(fullURL))
if res.ok:
    print(res.content)
res = requests.post('{}test/update'.format(fullURL))
res = requests.get('{}test/count'.format(fullURL))
if res.ok:
    print(res.content)
res = requests.post('{}test/update'.format(fullURL))
res = requests.get('{}test/count'.format(fullURL))
if res.ok:
    print(res.content)
res = requests.post('{}test/update'.format(fullURL))
res = requests.get('{}test/count'.format(fullURL))
if res.ok:
    print(res.content)
res = requests.post('{}test/update'.format(fullURL))
res = requests.get('{}test/count'.format(fullURL))
if res.ok:
    print(res.content)
    print("done 1")
