"""Refresh the On file column (pull-list/) and the recorded-document / index lists (catalog/) from the
hourly scan's status export, without rebuilding anything else.

Usage: python3 build/refresh_onfile.py "<On file status (auto).csv>" <repo dir> [<label for 'checked' time>]

The status CSV is written every hour by scan-nm-uploads.ps1 on JONDESK into
Shared Documents/Pending Parcels - Pull List & Catalogue (2026-11-17)/Hourly scan/ and lists every file in each
pending parcel's Documents and Indexes & Abstracts folders (county, apn, file, kind, name, book, page, path, modified).
"""
import csv, json, re, sys, urllib.parse

status_csv, repo = sys.argv[1], sys.argv[2]
label = sys.argv[3] if len(sys.argv) > 3 else None
BASE = 'https://vresolutions.sharepoint.com/sites/VanguardCorporate/Documents/Projects/FAT%20-%20First%20American%20Title/FAT-NM-Title1%20-%20New%20Mexico/'
RX = re.compile(r'(<script id="data" type="application/json">)(.*?)(</script>)', re.S)


def url(path):
    return BASE + urllib.parse.quote(path.replace('\\', '/'), safe="/&()',-._~!$*+;=:@")


def load(fn):
    t = open(fn, encoding='utf-8').read()
    m = RX.search(t)
    return t, m, json.loads(m.group(2).replace('<\\/', '</'))


def save(fn, t, m, d):
    blob = json.dumps(d, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    open(fn, 'w', encoding='utf-8').write(t[:m.start(2)] + blob + t[m.end(2):])


rows = list(csv.DictReader(open(status_csv, encoding='utf-8-sig')))
if len(rows) < 500:
    sys.exit(f'status file has only {len(rows)} rows; refusing to refresh from it')
docs_bp, rec, ia = {}, {}, {}
for r in rows:
    if r['kind'] == 'Documents':
        if r['book'] and r['page']:
            docs_bp.setdefault((r['apn'], int(r['book']), int(r['page'])), url(r['path']))
        n = r['name']
        if not (n.startswith('SER-') or 'patent' in n.lower()):
            rec.setdefault(r['apn'], []).append(['Recorded doc', n, url(r['path'])])
    elif r['kind'] == 'Indexes & Abstracts':
        ia.setdefault(r['apn'], []).append(['Index/abstract', r['name'], url(r['path'])])


def num(x):
    try:
        return int(str(x).strip())
    except ValueError:
        return None


# pull list: On file = the parcel's Documents folder has a file for that book-page
fn = f'{repo}/pull-list/index.html'
t, m, d = load(fn)
before = sum(1 for r in d['R'] if r[13])
for r in d['R']:
    apn = d['P'][r[0]][2]
    b, p = num(r[4]), num(r[5])
    r[13] = docs_bp.get((apn, b, p), '') if b is not None and p is not None else ''
after = sum(1 for r in d['R'] if r[13])
save(fn, t, m, d)
if label:
    t = open(fn, encoding='utf-8').read()
    t = re.sub(r"\(checked [^)]*\)", f'(checked {label})', t)
    open(fn, 'w', encoding='utf-8').write(t)

# catalog: replace recorded-doc and index/abstract entries; keep plat, cards, runsheets, patents
fn = f'{repo}/catalog/index.html'
t, m, d = load(fn)
nrec = 0
for apn, lst in d['docs'].items():
    keep = [x for x in lst if x[0] not in ('Recorded doc', 'Index/abstract')]
    new_ia = sorted(ia.get(apn, []), key=lambda x: x[1].lower())
    new_rec = sorted(rec.get(apn, []), key=lambda x: x[1].lower())
    if not new_ia:   # never blank out index files because of a partial export
        new_ia = [x for x in lst if x[0] == 'Index/abstract']
    d['docs'][apn] = keep + new_ia + new_rec
    nrec += len(new_rec)
save(fn, t, m, d)
if label:
    t = open(fn, encoding='utf-8').read()
    t = re.sub(r"\(updated [^)]*\)", f'(updated {label})', t)
    open(fn, 'w', encoding='utf-8').write(t)
print(f'pull list on file: {before} -> {after}; catalog recorded docs: {nrec}')
