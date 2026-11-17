"""Build the FAT NM GitHub Pages site: pull-list/ (starter parcels) and catalog/ (all pending parcels).
Inputs (paths passed in env-free constants below are from the Claude project workspace):
  artifact_data.json  P (parcels), S (index/abstract files), R (pull rows), cats, notes
  starter APNs        from the starter pull list workbook
  docs.json           per-APN list of [kind, name, url] for plat/property/tax/runsheet/patent files
  shell.html          the page template (styles + markup + script) with a __DATA__ placeholder
"""
import json, sys, re
shell, data, starters, docs, outdir = sys.argv[1:6]
T = open(shell, encoding='utf-8').read()
D = json.load(open(data)); ST = set(json.load(open(starters))); DOCS = json.load(open(docs))
HEAD = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<meta name="robots" content="noindex,nofollow,noarchive">\n<meta name="referrer" content="no-referrer">\n')
def page(title, sub, nd, mode):
    t = T.replace('__TITLE__', title).replace('__SUB__', sub).replace('__MODE__', mode)
    blob = json.dumps(nd, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    i = t.index('</style>') + len('</style>')
    body = t[i:].replace('__DATA__', blob)
    return HEAD + t[:i] + '\n</head>\n<body>\n' + body + '\n</body>\n</html>\n'
# pull list: starters only
pm = {}; P = []
for i, p in enumerate(D['P']):
    if p[2] in ST: pm[i] = len(P); P.append(p)
R = [r for r in D['R'] if r[0] in pm]
used = sorted({s for r in R for s in r[11]}); sm = {o: n for n, o in enumerate(used)}
pull = dict(P=P, S=[D['S'][o] for o in used], R=[[pm[r[0]]] + r[1:11] + [[sm[x] for x in r[11]]] + r[12:] for r in R], cats=D['cats'], notes=D['notes'], docs={})
open(f'{outdir}/pull-list/index.html', 'w', encoding='utf-8').write(page('NM Starter Parcels Pull List',
    f"Instruments to pull for the {len(P)} starter parcels, read from Charlie's Curry abstracts and indexes and the Quay ground-team account indexes. Same rows as \"FAT NM - Starter parcels pull list\" on SharePoint. Machine-read: confirm every row against the recorded instrument.",
    pull, 'pull'))
cat = dict(P=D['P'], S=D['S'], R=[], cats=D['cats'], notes=[], docs=DOCS)
open(f'{outdir}/catalog/index.html', 'w', encoding='utf-8').write(page('NM Pending Parcels Document Catalog',
    f"Every document filed so far for the {len(D['P'])} pending parcels First American numbered on 11/3: plat maps, property and tax cards, draft runsheets, GLO patents, and the index and abstract files. Links open SharePoint (Vanguard sign-in).",
    cat, 'cat'))
print('pull', len(P), len(pull['R']), 'catalog', len(D['P']), sum(len(v) for v in DOCS.values()))
