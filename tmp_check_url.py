import urllib.request, urllib.error, sys
url = 'https://github.com/Ben-bit-code208/game-data/raw/refs/heads/main/temp.bin'
print('Testing URL:', url)
try:
    req = urllib.request.Request(url, headers={'User-Agent':'python-urllib/3'})
    with urllib.request.urlopen(req, timeout=15) as r:
        status = getattr(r, 'status', 'unknown')
        print('Status:', status)
        hdrs = r.getheaders()
        print('Headers:')
        for k,v in hdrs[:10]:
            print(' ', k, ':', v)
        data = r.read(200)
        print('First bytes (len {}):'.format(len(data)))
        print(data[:200])
except urllib.error.HTTPError as he:
    print('HTTPError', he.code, he.reason)
    sys.exit(2)
except urllib.error.URLError as ue:
    print('URLError', ue.reason)
    sys.exit(3)
except Exception as e:
    print('ERR', e)
    sys.exit(4)
