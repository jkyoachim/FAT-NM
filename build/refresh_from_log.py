"""Apply new rows from the hourly scan's "Scan log (auto).csv" to the site (incremental).

Usage: python3 build/refresh_from_log.py <log rows csv> <repo dir> "<label>"
  <log rows csv>: CSV with the scan log header (run,county,apn,result,src,dest,note); only result == copied is used.
Adds each copied file to the catalog (Recorded doc for Documents\\, Index/abstract for Indexes & Abstracts\\)
and marks matching pull-list rows (same APN and book-page) On file. Updates build/last_log_run.txt to the
newest run applied. Never removes anything from the pages.
"""
import csv, json, re, sys, urllib.parse

log_csv, repo, label = sys.argv[1], sys.argv[2], sys.argv[3]
BASE = 'https://vresolutions.sharepoint.com/sites/VanguardCorporate/Documents/Projects/FAT%20-%20First%20American%20Title/FAT-NM-Title1%20-%20New%20Mexico/'
RX = re.compile(r'(<script id="data" type="application/json">)(.*?)(</script>)', re.S)
BP = re.compile(r'^\s*0*(\d{1,4})[\s\-_]+0*(\d{1,4})(?!\d)')
state = f'{repo}/build/last_log_run.txt'
try:
    last = open(state).read().strip()
except FileNotFoundError:
    last = ''


def url(path):
    return BASE + urllib.parse.quote(path.replace('\\', '/'), safe="/&()',-._~!$*+;=:@")


def load(fn):
    t = open(fn, encoding='utf-8').read()
    m = RX.search(t)
    return t, m, json.loads(m.group(2).replace('<\\/', '</'))


def save(fn, t, m, d, sub=None):
    blob = json.dumps(d, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    t = t[:m.start(2)] + blob + t[m.end(2):]
    if sub:
        t = re.sub(sub[0], sub[1], t)
    open(fn, 'w', encoding='utf-8').write(t)


rows = [r for r in csv.DictReader(open(log_csv, encoding='utf-8-sig')) if r['result'] == 'copied' and r['run'] > last]
if not rows:
    sys.exit('nothing new to apply')
newest = max(r['run'] for r in rows)

onfile = {}
cat_add = {}
for r in rows:
    name = r['dest'].replace('/', '\\').split('\\')[-1]
    u = url(r['dest'])
    if '\\Documents\\' in r['dest']:
        cat_add.setdefault(r['apn'], []).append(['Recorded doc', name, u])
        m = BP.match(name)
        if m:
            onfile.setdefault((r['apn'], int(m.group(1)), int(m.group(2))), u)
    elif '\\Indexes & Abstracts\\' in r['dest']:
        cat_add.setdefault(r['apn'], []).append(['Index/abstract', name, u])

fn = f'{repo}/pull-list/index.html'
t, m, d = load(fn)
marked = 0
for r in d['R']:
    if r[13]:
        continue
    try:
        k = (d['P'][r[0]][2], int(str(r[4]).strip()), int(str(r[5]).strip()))
    except ValueError:
        continue
    if k in onfile:
        r[13] = onfile[k]
        marked += 1
save(fn, t, m, d, (r'\(checked [^)]*\)', f'(checked {label})'))

fn = f'{repo}/catalog/index.html'
t, m, d = load(fn)
added = 0
for apn, items in cat_add.items():
    lst = d['docs'].setdefault(apn, [])
    have = {(x[0], x[1]) for x in lst}
    for it in items:
        if (it[0], it[1]) not in have:
            lst.append(it)
            have.add((it[0], it[1]))
            added += 1
save(fn, t, m, d, (r'\(updated [^)]*\)', f'(updated {label})'))
open(state, 'w').write(newest + '\n')
print(f'applied {len(rows)} copied rows (runs after {last or "start"} through {newest}); pull list rows marked on file: {marked}; catalog entries added: {added}')
