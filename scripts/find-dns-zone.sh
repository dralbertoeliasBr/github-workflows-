#!/usr/bin/env bash
#
# find-dns-zone.sh — descobre em qual projeto do Google Cloud está a zona DNS
# de um domínio, e imprime os registros dessa zona.
#
# Uso:
#   ./scripts/find-dns-zone.sh                       # procura sounavy.com nos projetos padrão
#   ./scripts/find-dns-zone.sh exemplo.com           # procura outro domínio
#   ./scripts/find-dns-zone.sh exemplo.com proj-a proj-b
#
# Requer: gcloud autenticado (`gcloud auth login`) com permissão de leitura
# de DNS (roles/dns.reader) nos projetos consultados.

set -uo pipefail

DOMINIO="${1:-sounavy.com}"
shift || true

# Projetos padrão. Sobrescreva passando os IDs como argumentos, ou via
# a variável de ambiente PROJETOS (separada por espaços).
PROJETOS_PADRAO=(
  main-nova-493122-a4          # borda
  prova-503213                 # Prova
  gen-lang-client-0694221185   # Default Gemini Project
  practical-well-484200-i8     # My First Project
  eloquent-walker-484205-r9    # My First Project
  atomic-vault-488402-j7       # Projeto a
)

if [[ $# -gt 0 ]]; then
  PROJETOS=("$@")
elif [[ -n "${PROJETOS:-}" ]]; then
  read -r -a PROJETOS <<<"${PROJETOS}"
else
  PROJETOS=("${PROJETOS_PADRAO[@]}")
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "ERRO: gcloud nao encontrado no PATH." >&2
  echo "Instale o Google Cloud SDK ou rode isto no Cloud Shell:" >&2
  echo "  https://shell.cloud.google.com" >&2
  exit 127
fi

if ! gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | grep -q .; then
  echo "ERRO: nenhuma conta gcloud ativa. Rode: gcloud auth login" >&2
  exit 1
fi

# O gcloud casa o dnsName com o ponto final (sounavy.com.), entao filtramos
# pela raiz do dominio sem ancorar o final.
FILTRO="dnsName~${DOMINIO%.}"

encontrados=0

echo "Procurando zonas de '${DOMINIO}' em ${#PROJETOS[@]} projeto(s)..."
echo

for projeto in "${PROJETOS[@]}"; do
  printf '=== %s ===\n' "${projeto}"

  saida="$(gcloud dns managed-zones list \
    --project="${projeto}" \
    --filter="${FILTRO}" \
    --format='value(name,dnsName,visibility)' 2>&1)"
  status=$?

  if [[ ${status} -ne 0 ]]; then
    # Distingue as falhas comuns para nao parecer que a zona nao existe.
    if grep -qi 'has not been used\|is disabled\|SERVICE_DISABLED' <<<"${saida}"; then
      echo "  ignorado: API Cloud DNS nao habilitada neste projeto"
    elif grep -qi 'permission\|PERMISSION_DENIED\|does not have' <<<"${saida}"; then
      echo "  ignorado: sem permissao de leitura de DNS"
    elif grep -qi 'not found\|does not exist' <<<"${saida}"; then
      echo "  ignorado: projeto inexistente ou inacessivel"
    else
      echo "  erro ao consultar:"
      sed 's/^/    /' <<<"${saida}"
    fi
    echo
    continue
  fi

  if [[ -z "${saida//[[:space:]]/}" ]]; then
    echo "  nenhuma zona com '${DOMINIO}'"
    echo
    continue
  fi

  while IFS=$'\t' read -r zona dns_name visibilidade; do
    [[ -z "${zona}" ]] && continue
    encontrados=$((encontrados + 1))

    echo "  ENCONTRADA: ${zona}  (${dns_name})  visibilidade=${visibilidade}"
    echo
    echo "  --- nameservers da zona ---"
    gcloud dns managed-zones describe "${zona}" \
      --project="${projeto}" \
      --format='value(nameServers.list())' 2>/dev/null | sed 's/^/    /'

    echo
    echo "  --- registros A e CNAME ---"
    gcloud dns record-sets list \
      --zone="${zona}" \
      --project="${projeto}" \
      --filter='type=A OR type=CNAME' \
      --format='table(name,type,ttl,rrdatas.list())' 2>&1 | sed 's/^/    /'

    echo
    echo "  --- todos os registros ---"
    gcloud dns record-sets list \
      --zone="${zona}" \
      --project="${projeto}" \
      --format='table(name,type,ttl,rrdatas.list())' 2>&1 | sed 's/^/    /'
    echo
  done <<<"${saida}"
done

echo "============================================"
if [[ ${encontrados} -eq 0 ]]; then
  echo "Nenhuma zona de '${DOMINIO}' encontrada nos projetos consultados."
  echo
  echo "Isso pode significar que:"
  echo "  - a zona esta em outro projeto ao qual voce tem acesso;"
  echo "  - a API Cloud DNS nao esta habilitada onde a zona vive;"
  echo "  - sua conta nao tem roles/dns.reader no projeto correto."
  echo
  echo "Com acesso de organizacao, este comando acha em todos de uma vez:"
  echo "  gcloud asset search-all-resources \\"
  echo "    --scope=organizations/SEU_ORG_ID \\"
  echo "    --asset-types=dns.googleapis.com/ManagedZone \\"
  echo "    --query='${DOMINIO%%.*}'"
  exit 2
fi

echo "${encontrados} zona(s) encontrada(s) para '${DOMINIO}'."
