#!/usr/bin/env python3
"""自动从福彩官网抓取最新10期双色球数据，校验后写入 index.html"""
import json, ssl, urllib.request, http.cookiejar, re, sys, os

OUT = os.path.join(os.path.dirname(__file__), '..', 'index.html')
API = ('https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/'
       'findDrawNotice?name=ssq&issueCount=10&issueStart=&issueEnd='
       '&dayStart=&dayEnd=&isVerify=1')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ctx),
    urllib.request.HTTPCookieProcessor(jar),
    urllib.request.HTTPRedirectHandler()
)
req = urllib.request.Request(API)
req.add_header('Referer', 'https://www.cwl.gov.cn/')
req.add_header('User-Agent',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 Chrome/124.0 Safari/537.36')
req.add_header('Accept', 'application/json, text/plain, */*')

try:
    with opener.open(req, timeout=20) as r:
        data = json.loads(r.read())
except Exception as e:
    print(f'[FAIL] 抓取失败: {e}', file=sys.stderr)
    sys.exit(1)

draws = []
for row in data['result']:
    code = row['code']
    date = row['date'].split('(')[0]
    reds = row['red'].split(',')
    blue = row['blue']
    assert len(reds) == 6, f"红球数量异常: {reds}"
    assert blue.isdigit() and 1 <= int(blue) <= 16, f"蓝球异常: {blue}"
    draws.append({'p': code, 'date': date, 'rs': reds, 'b': blue})

def js_draw(d):
    rs = ','.join(f"'{x}'" for x in d['rs'])
    return f"  {{p:'{d['p']}',date:'{d['date']}',rs:[{rs}],b:'{d['b']}'}}"

draws_js = 'var REAL_DRAWS = [\n' + ',\n'.join(js_draw(d) for d in draws) + '\n];'

with open(OUT, 'r', encoding='utf-8') as f:
    html = f.read()

html = re.sub(r'var REAL_DRAWS = \[[\s\S]*?\];', draws_js, html)
prev = draws[0]
html = re.sub(
    r'(<div class="bb blue" id="pr7">)\d+(</div>)',
    rf'\g<1>{prev["b"]}\2', html)
for i in range(6):
    html = re.sub(
        rf'(<div class="bb red" id="pr{i+1}">)\d+(</div>)',
        rf'\g<1>{prev["rs"][i]}\2', html)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'[OK] 最新期: {prev["p"]}  红:{",".join(prev["rs"])}  蓝:{prev["b"]}')
