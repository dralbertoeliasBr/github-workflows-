#!/usr/bin/env bash
#
# pin-actions.sh — fixa as GitHub Actions por SHA de commit.
#
# Tags como @v4 são móveis: quem controla o repositório da action pode
# reapontá-las para outro código a qualquer momento, e o seu CI passa a
# executar isso sem aviso. Um SHA de commit é imutável.
#
# Este script resolve o SHA real de cada tag usada nos workflows e reescreve
# as linhas `uses:`, deixando a versão legível no comentário ao lado:
#
#   uses: actions/checkout@v4
#   -> uses: actions/checkout@8f4b7f8...  # v4
#
# Uso:
#   ./scripts/pin-actions.sh            # aplica
#   ./scripts/pin-actions.sh --dry-run  # só mostra o que faria
#
# Requer: curl, python3. Um token em GITHUB_TOKEN é opcional e só serve para
# elevar o limite de requisições da API pública.

set -uo pipefail

DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR_WF="${RAIZ}/.github/workflows"

if [[ ! -d "${DIR_WF}" ]]; then
  echo "ERRO: ${DIR_WF} nao existe." >&2
  exit 1
fi

cabecalhos=(-H "Accept: application/vnd.github+json")
[[ -n "${GITHUB_TOKEN:-}" ]] && cabecalhos+=(-H "Authorization: Bearer ${GITHUB_TOKEN}")

# Resolve uma tag para o SHA do commit, desreferenciando tag anotada.
resolver_sha() {
  local repo="$1" tag="$2" resp tipo sha

  resp="$(curl -sS "${cabecalhos[@]}" \
    "https://api.github.com/repos/${repo}/git/ref/tags/${tag}" 2>/dev/null)"

  read -r tipo sha <<<"$(python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    o = d.get('object') or {}
    print(o.get('type', ''), o.get('sha', ''))
except Exception:
    print('', '')
" <<<"${resp}")"

  if [[ -z "${sha}" ]]; then
    return 1
  fi

  # Tag anotada aponta para um objeto tag; é preciso mais um salto.
  if [[ "${tipo}" == "tag" ]]; then
    resp="$(curl -sS "${cabecalhos[@]}" \
      "https://api.github.com/repos/${repo}/git/tags/${sha}" 2>/dev/null)"
    sha="$(python3 -c "
import sys, json
try:
    print((json.load(sys.stdin).get('object') or {}).get('sha', ''))
except Exception:
    print('')
" <<<"${resp}")"
  fi

  [[ -n "${sha}" ]] && printf '%s\n' "${sha}"
}

total=0
fixadas=0
falhas=0

for arquivo in "${DIR_WF}"/*.yml "${DIR_WF}"/*.yaml; do
  [[ -e "${arquivo}" ]] || continue
  echo "=== $(basename "${arquivo}") ==="

  # Só linhas `uses:` que ainda apontam para uma tag de versão (vN / vN.N.N).
  while IFS= read -r referencia; do
    [[ -z "${referencia}" ]] && continue
    repo="${referencia%@*}"
    tag="${referencia#*@}"
    total=$((total + 1))

    # Actions locais (./...) e de container (docker://) não se aplicam.
    if [[ "${repo}" == ./* || "${repo}" == docker://* ]]; then
      continue
    fi

    printf '  %-45s %-8s ' "${repo}" "${tag}"

    if ! sha="$(resolver_sha "${repo}" "${tag}")"; then
      echo "FALHOU (tag inexistente ou API indisponivel)"
      falhas=$((falhas + 1))
      continue
    fi

    echo "-> ${sha}"

    if [[ ${DRY_RUN} -eq 0 ]]; then
      python3 - "${arquivo}" "${repo}" "${tag}" "${sha}" <<'PY'
import re, sys
caminho, repo, tag, sha = sys.argv[1:5]
with open(caminho) as f:
    texto = f.read()
padrao = re.compile(
    r'(uses:\s*)' + re.escape(repo) + r'@' + re.escape(tag) + r'(?![\w.-])[^\n]*'
)
texto = padrao.sub(lambda m: f"{m.group(1)}{repo}@{sha}  # {tag}", texto)
with open(caminho, 'w') as f:
    f.write(texto)
PY
    fi
    fixadas=$((fixadas + 1))
  done < <(grep -oE 'uses:[[:space:]]*[^[:space:]]+@v[0-9][^[:space:]]*' "${arquivo}" \
             | sed -E 's/uses:[[:space:]]*//' | sort -u)
  echo
done

echo "============================================"
echo "referencias encontradas: ${total}"
echo "fixadas:                 ${fixadas}"
echo "falhas:                  ${falhas}"

if [[ ${DRY_RUN} -eq 1 ]]; then
  echo
  echo "(--dry-run: nenhum arquivo foi alterado)"
elif [[ ${fixadas} -gt 0 ]]; then
  echo
  echo "Revise e commite:"
  echo "  git diff .github/workflows"
fi

[[ ${falhas} -gt 0 ]] && exit 1
exit 0
