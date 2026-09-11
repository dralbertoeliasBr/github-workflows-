#!/usr/bin/env bash
#
# drive-socorro.sh — recupera arquivos da lixeira do Google Drive e fecha
# compartilhamentos públicos, em lote, sem precisar tocar item por item.
#
# Feito para rodar no Cloud Shell (https://shell.cloud.google.com), que abre
# no navegador do celular e já autentica com a sua conta Google.
#
#   1) Autorize o acesso ao Drive, uma vez:
#        gcloud auth login --enable-gdrive-access
#
#   2) Use:
#        ./scripts/drive-socorro.sh listar-lixeira            # só mostra
#        ./scripts/drive-socorro.sh listar-lixeira --midia    # só fotos e vídeos
#        ./scripts/drive-socorro.sh restaurar                 # traz tudo de volta
#        ./scripts/drive-socorro.sh restaurar --midia         # só fotos e vídeos
#        ./scripts/drive-socorro.sh listar-publicos           # o que está público
#        ./scripts/drive-socorro.sh fechar-publicos --confirmar
#
# Nada é alterado sem um subcomando explícito. Os comandos "listar-*" só leem.
#
# A lixeira do Drive retém 30 dias. Passado isso o item some em definitivo e
# nenhuma ferramenta recupera — inclusive esta.

set -uo pipefail

API="https://www.googleapis.com/drive/v3"
ACAO="${1:-ajuda}"
shift || true

SOMENTE_MIDIA=0
CONFIRMAR=0
for arg in "$@"; do
  case "${arg}" in
    --midia)     SOMENTE_MIDIA=1 ;;
    --confirmar) CONFIRMAR=1 ;;
    *) echo "Opcao desconhecida: ${arg}" >&2; exit 2 ;;
  esac
done

# ---------------------------------------------------------------- utilidades

exigir() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "ERRO: '$1' nao encontrado. Rode isto no Cloud Shell." >&2
    exit 127
  }
}
obter_token() {
  local t
  t="$(gcloud auth print-access-token \
        --scopes=https://www.googleapis.com/auth/drive 2>/dev/null)"
  [[ -z "${t}" ]] && t="$(gcloud auth print-access-token 2>/dev/null)"
  if [[ -z "${t}" ]]; then
    echo "ERRO: nao foi possivel obter um token de acesso." >&2
    echo "Rode primeiro:  gcloud auth login --enable-gdrive-access" >&2
    exit 1
  fi
  printf '%s' "${t}"
}

# Só exige ferramentas e token quando a acao de fato vai falar com a API,
# para que "ajuda" funcione em qualquer lugar.
preparar() {
  exigir gcloud
  exigir curl
  exigir python3
  TOKEN="$(obter_token)"
  AUTH=(-H "Authorization: Bearer ${TOKEN}")
}

# Trata 401/403 de escopo com uma mensagem que diz o que fazer.
checar_escopo() {
  if grep -q 'insufficientPermissions\|insufficientScopes\|ACCESS_TOKEN_SCOPE' <<<"$1"; then
    echo >&2
    echo "ERRO: o token nao tem permissao de Drive." >&2
    echo "Autorize uma vez e repita o comando:" >&2
    echo "  gcloud auth login --enable-gdrive-access" >&2
    exit 1
  fi
}

# Percorre todas as páginas de files.list e imprime TSV: id, nome, tipo, tamanho.
# As linhas vão para a saída padrão; o token da próxima página vai para um
# arquivo temporário, para não se misturar com os dados.
listar() {
  local consulta="$1" token_pagina="" pagina=0 tmp_token
  tmp_token="$(mktemp)"

  while :; do
    local url resp
    url="${API}/files?q=$(python3 -c "
import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" "${consulta}")"
    url+="&pageSize=1000&fields=nextPageToken,files(id,name,mimeType,size)"
    url+="&supportsAllDrives=true&includeItemsFromAllDrives=true"
    [[ -n "${token_pagina}" ]] && url+="&pageToken=${token_pagina}"

    resp="$(curl -sS "${AUTH[@]}" "${url}")"
    checar_escopo "${resp}"

    python3 -c '
import sys, json
d = json.load(sys.stdin)
if "error" in d:
    print("ERRO_API: " + d["error"].get("message", "?"), file=sys.stderr)
    sys.exit(3)
for f in d.get("files", []):
    print("\t".join([f["id"],
                     f.get("name", "(sem nome)").replace("\t", " "),
                     f.get("mimeType", ""),
                     str(f.get("size", "") or "")]))
open(sys.argv[1], "w").write(d.get("nextPageToken", ""))
' "${tmp_token}" <<<"${resp}" || { rm -f "${tmp_token}"; return 3; }

    token_pagina="$(cat "${tmp_token}")"
    pagina=$((pagina + 1))
    [[ -z "${token_pagina}" ]] && break
    [[ ${pagina} -gt 50 ]] && break   # trava de segurança
  done

  rm -f "${tmp_token}"
}

humano() {  # bytes -> legível
  python3 -c "
import sys
b = sys.argv[1]
if not b.isdigit(): print('-'); raise SystemExit
n = int(b)
for u in ['B','KB','MB','GB','TB']:
    if n < 1024: print(f'{n:.0f}{u}'); break
    n /= 1024
else: print(f'{n:.1f}PB')" "$1"
}

consulta_lixeira() {
  if [[ ${SOMENTE_MIDIA} -eq 1 ]]; then
    echo "trashed = true and (mimeType contains 'image/' or mimeType contains 'video/')"
  else
    echo "trashed = true"
  fi
}

# ------------------------------------------------------------------- acoes

acao_listar_lixeira() {
  echo "Lendo a lixeira..."
  [[ ${SOMENTE_MIDIA} -eq 1 ]] && echo "(filtrando apenas fotos e videos)"
  echo

  local n=0 bytes=0
  while IFS=$'\t' read -r id nome tipo tamanho; do
    [[ -z "${id}" ]] && continue
    n=$((n + 1))
    [[ "${tamanho}" =~ ^[0-9]+$ ]] && bytes=$((bytes + tamanho))
    printf '  %-9s  %s\n' "$(humano "${tamanho}")" "${nome}"
  done < <(listar "$(consulta_lixeira)")

  echo
  echo "============================================"
  if [[ ${n} -eq 0 ]]; then
    echo "A lixeira esta vazia para esse filtro."
    echo
    echo "Se os arquivos sumiram ha mais de 30 dias, a exclusao ja e definitiva"
    echo "e nao ha o que restaurar."
  else
    echo "${n} item(ns) na lixeira · $(humano "${bytes}") recuperaveis"
    echo
    echo "Para trazer de volta:"
    local sufixo=""; [[ ${SOMENTE_MIDIA} -eq 1 ]] && sufixo=" --midia"
    echo "  $0 restaurar${sufixo}"
  fi
}

acao_restaurar() {
  echo "Restaurando da lixeira..."
  [[ ${SOMENTE_MIDIA} -eq 1 ]] && echo "(apenas fotos e videos)"
  echo

  local ok=0 falha=0
  while IFS=$'\t' read -r id nome tipo tamanho; do
    [[ -z "${id}" ]] && continue
    local resp
    resp="$(curl -sS -X PATCH "${AUTH[@]}" \
      -H "Content-Type: application/json" \
      -d '{"trashed": false}' \
      "${API}/files/${id}?supportsAllDrives=true")"

    if grep -q '"error"' <<<"${resp}"; then
      falha=$((falha + 1))
      printf '  FALHOU   %s\n' "${nome}"
    else
      ok=$((ok + 1))
      printf '  ok       %s\n' "${nome}"
    fi
  done < <(listar "$(consulta_lixeira)")

  echo
  echo "============================================"
  echo "restaurados: ${ok}"
  [[ ${falha} -gt 0 ]] && echo "falhas:      ${falha}"
  [[ ${ok} -gt 0 ]] && echo && echo "Os arquivos voltaram para as pastas de origem."
  return 0
}

acao_listar_publicos() {
  echo "Procurando o que esta acessivel por link publico..."
  echo

  local n=0
  while IFS=$'\t' read -r id nome tipo tamanho; do
    [[ -z "${id}" ]] && continue
    n=$((n + 1))
    local marca="arquivo"
    [[ "${tipo}" == "application/vnd.google-apps.folder" ]] && marca="PASTA "
    printf '  %s  %s\n' "${marca}" "${nome}"
  done < <(listar "visibility = 'anyoneWithLink'")

  echo
  echo "============================================"
  if [[ ${n} -eq 0 ]]; then
    echo "Nada esta compartilhado por link publico."
  else
    echo "${n} item(ns) acessivel(is) a qualquer pessoa com o link."
    echo
    echo "Fechar as PASTAS resolve o conteudo delas junto, por heranca."
    echo
    echo "Para fechar todos:"
    echo "  $0 fechar-publicos --confirmar"
  fi
}

acao_fechar_publicos() {
  if [[ ${CONFIRMAR} -eq 0 ]]; then
    echo "Este comando remove o acesso publico de TODOS os itens listados em:"
    echo "  $0 listar-publicos"
    echo
    echo "Links que voce compartilhou de proposito param de funcionar."
    echo "Revise a lista antes. Para prosseguir:"
    echo "  $0 fechar-publicos --confirmar"
    exit 2
  fi

  echo "Removendo acesso publico..."
  echo

  local ok=0 falha=0
  while IFS=$'\t' read -r id nome tipo tamanho; do
    [[ -z "${id}" ]] && continue

    # Descobre o id da permissao do tipo "anyone" neste item.
    local perms pid
    perms="$(curl -sS "${AUTH[@]}" \
      "${API}/files/${id}/permissions?fields=permissions(id,type)&supportsAllDrives=true")"
    pid="$(python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    for p in d.get('permissions', []):
        if p.get('type') == 'anyone':
            print(p['id']); break
except Exception:
    pass" <<<"${perms}")"

    if [[ -z "${pid}" ]]; then
      printf '  pulado   %s (sem permissao publica)\n' "${nome}"
      continue
    fi

    local resp
    resp="$(curl -sS -o /dev/null -w '%{http_code}' -X DELETE "${AUTH[@]}" \
      "${API}/files/${id}/permissions/${pid}?supportsAllDrives=true")"

    if [[ "${resp}" == "204" ]]; then
      ok=$((ok + 1))
      printf '  fechado  %s\n' "${nome}"
    else
      falha=$((falha + 1))
      printf '  FALHOU   %s (HTTP %s)\n' "${nome}" "${resp}"
    fi
  done < <(listar "visibility = 'anyoneWithLink'")

  echo
  echo "============================================"
  echo "fechados: ${ok}"
  [[ ${falha} -gt 0 ]] && echo "falhas:   ${falha}"
  echo
  echo "Atencao: fechar o link impede acesso NOVO. Quem ja baixou o conteudo"
  echo "continua com a copia — isso nenhuma ferramenta desfaz."
  return 0
}

# -------------------------------------------------------------------- rotas

case "${ACAO}" in
  listar-lixeira)   preparar; acao_listar_lixeira ;;
  restaurar)        preparar; acao_restaurar ;;
  listar-publicos)  preparar; acao_listar_publicos ;;
  fechar-publicos)  [[ ${CONFIRMAR} -eq 1 ]] && preparar; acao_fechar_publicos ;;
  ajuda|--help|-h)
    sed -n '2,23p' "$0" | sed 's/^# \{0,1\}//'
    ;;
  *)
    echo "Subcomando desconhecido: ${ACAO}" >&2
    echo "Use: $0 ajuda" >&2
    exit 2
    ;;
esac
