import urllib.request, urllib.error
urls=[
    'https://ben-bit-code208.github.io/DATA/Spiele/temp.bin',
    'https://raw.githubusercontent.com/Ben-bit-code208/Ben-bit-code-208.github.io/main/DATA/Spiele/temp.bin'
]
for u in urls:
    try:
        req=urllib.request.Request(u, headers={'User-Agent':'python-urllib/3'})
        with urllib.request.urlopen(req, timeout=10) as r:
            print(u, 'OK', getattr(r,'status', 'unknown'))
    except urllib.error.HTTPError as he:
        print(u, 'HTTPError', he.code)
    except urllib.error.URLError as ue:
        print(u, 'URLError', ue.reason)
    except Exception as e:
        print(u, 'ERR', e)
