import urllib.request
req=urllib.request.Request('https://github.com/Ben-bit-code208/game-data/blob/main/temp.bin', headers={'User-Agent':'Mozilla/5.0','Accept':'text/html'})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        html=r.read(2000).decode('utf-8',errors='ignore')
        print('len',len(html))
        print(html[:400])
except Exception as e:
    print('ERR',e)
