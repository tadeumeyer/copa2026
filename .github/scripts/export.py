import requests, os, base64

FILE_KEY      = 'eVEXECqP4Zmmz88uxhn836'
GITHUB_USER   = 'rthomazi'
GITHUB_REPO   = 'copa2026'
GITHUB_BRANCH = 'main'
FIGMA_TOKEN  = os.environ['FIGMA_TOKEN']
GITHUB_TOKEN = os.environ['GH_TOKEN']
FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true

CANAL_FRAMES = {
    'A':'787:3979','B':'787:4150','C':'787:4321','D':'787:4492',
    'E':'787:4834','F':'787:5176','G':'787:5518','H':'787:5860',
    'I':'787:6202','J':'787:6544','K':'787:6886','L':'787:7228',
}
REDES_FRAMES = {
    'A':'906:1392','B':'915:4961','C':'915:5181','D':'915:5401',
    'E':'915:5621','F':'915:5841','G':'915:6061','H':'915:6281',
    'I':'915:6501','J':'915:6721','K':'915:6941','L':'915:7161',
}

TARGETS = {}
for l, n in CANAL_FRAMES.items(): TARGETS[f'frames/canal/canal-grupo-{l.lower()}.png'] = n
for l, n in REDES_FRAMES.items(): TARGETS[f'frames/redes/redes-grupo-{l.lower()}.png'] = n

GH = {
    'Authorization': 'Bearer ' + GITHUB_TOKEN,
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
}
API = 'https://api.github.com'

def export_batch(node_ids):
    ids = ','.join(n.replace(':', '-') for n in node_ids)
    r = requests.get(
        f'https://api.figma.com/v1/images/{FILE_KEY}',
        headers={'X-Figma-Token': FIGMA_TOKEN},
        params={'ids': ids, 'format': 'png', 'scale': 1},
        timeout=120
    )
    r.raise_for_status()
    data = r.json()
    result = {}
    for k, url in data['images'].items():
        if url:
            img = requests.get(url, timeout=120)
            img.raise_for_status()
            result[k.replace('-', ':')] = img.content
    return result

def get_sha(path):
    r = requests.get(f'{API}/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{path}',
                     headers=GH, params={'ref': GITHUB_BRANCH}, timeout=15)
    return r.json()['sha'] if r.status_code == 200 else None

def push(path, data, sha=None):
    body = {'message': f'Update {path}', 'content': base64.b64encode(data).decode(), 'branch': GITHUB_BRANCH}
    if sha: body['sha'] = sha
    r = requests.put(f'{API}/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{path}',
                     headers=GH, json=body, timeout=30)
    r.raise_for_status()

images = {}
images.update(export_batch(list(CANAL_FRAMES.values())))
images.update(export_batch(list(REDES_FRAMES.values())))

for path, nid in TARGETS.items():
    data = images.get(nid)
    if not data: print(f'No image: {path}'); continue
    try:
        push(path, data, get_sha(path))
        print(f'✓ {path}')
    except Exception as e:
        print(f'✗ {path}: {e}')
