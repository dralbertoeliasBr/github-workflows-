# Como rodar a busca da zona DNS

Três caminhos. O primeiro é o melhor se você está no celular.

---

## Caminho 1 — Cloud Shell (funciona no navegador do celular, sem configurar nada)

O Cloud Shell já vem autenticado com a sua conta Google. Não precisa de secret,
não precisa instalar nada.

1. Abra **https://shell.cloud.google.com**
2. Cole e execute:

```bash
git clone https://github.com/dralbertoeliasBr/github-workflows-.git && \
  bash github-workflows-/scripts/find-dns-zone.sh sounavy.com
```

Pronto. Ele varre os 6 projetos e imprime a zona e os registros.

Se quiser sem clonar nada, é uma linha só:

```bash
for P in main-nova-493122-a4 prova-503213 gen-lang-client-0694221185 \
         practical-well-484200-i8 eloquent-walker-484205-r9 atomic-vault-488402-j7; do
  echo "=== $P ==="
  gcloud dns managed-zones list --project="$P" --filter="dnsName~sounavy" \
    --format="table(name,dnsName)" 2>&1 | grep -v "^Listed 0"
done
```

---

## Caminho 2 — GitHub Actions (um botão, do app do GitHub)

Depois de configurado uma vez, você roda pelo telefone sem abrir terminal
nenhum: **Actions → Buscar zona DNS no Google Cloud → Run workflow**. O
resultado aparece na aba **Summary**, formatado para leitura.

### Configuração, uma única vez

Isso precisa ser feito num terminal com `gcloud` (o próprio Cloud Shell serve).

```bash
# 1. Escolha um projeto para hospedar a conta de serviço
PROJ_HOST=main-nova-493122-a4

# 2. Crie a conta de serviço
gcloud iam service-accounts create dns-leitor \
  --project="$PROJ_HOST" \
  --display-name="Leitor DNS para GitHub Actions"

SA="dns-leitor@${PROJ_HOST}.iam.gserviceaccount.com"

# 3. Dê permissão de LEITURA de DNS em cada projeto que será consultado
for P in main-nova-493122-a4 prova-503213 gen-lang-client-0694221185 \
         practical-well-484200-i8 eloquent-walker-484205-r9 atomic-vault-488402-j7; do
  gcloud projects add-iam-policy-binding "$P" \
    --member="serviceAccount:${SA}" \
    --role="roles/dns.reader" >/dev/null 2>&1 \
    && echo "ok: $P" || echo "falhou (sem permissao de admin?): $P"
done

# 4. Gere a chave
gcloud iam service-accounts keys create chave.json --iam-account="$SA"
cat chave.json
```

5. Copie **todo** o conteúdo de `chave.json`.
6. No GitHub: **Settings → Secrets and variables → Actions → New repository secret**
   - Nome: `GCP_SA_KEY`
   - Valor: o JSON inteiro
7. Apague a chave local: `rm chave.json`

> **Sobre segurança:** `roles/dns.reader` só lê, não altera nada — é o mínimo
> necessário. Ainda assim, uma chave JSON é uma credencial de longa duração:
> nunca faça commit dela, e revogue-a quando não precisar mais
> (`gcloud iam service-accounts keys list --iam-account=$SA` e depois `keys delete`).
> A alternativa sem chave é o Workload Identity Federation — o workflow já
> aceita, via os secrets `GCP_WIF_PROVIDER` e `GCP_SA_EMAIL`.

---

## Caminho 3 — Console web, no dedo

Sem terminal e sem configuração. Abra cada link e veja se aparece uma zona
`sounavy.com`:

- [borda — main-nova-493122-a4](https://console.cloud.google.com/net-services/dns/zones?project=main-nova-493122-a4)
- [Prova — prova-503213](https://console.cloud.google.com/net-services/dns/zones?project=prova-503213)
- [Default Gemini — gen-lang-client-0694221185](https://console.cloud.google.com/net-services/dns/zones?project=gen-lang-client-0694221185)
- [My First Project — practical-well-484200-i8](https://console.cloud.google.com/net-services/dns/zones?project=practical-well-484200-i8)
- [My First Project — eloquent-walker-484205-r9](https://console.cloud.google.com/net-services/dns/zones?project=eloquent-walker-484205-r9)
- [Projeto a — atomic-vault-488402-j7](https://console.cloud.google.com/net-services/dns/zones?project=atomic-vault-488402-j7)

---

## Atalho, se você tiver acesso de organização

Acha a zona em todos os projetos de uma vez, sem varredura:

```bash
gcloud asset search-all-resources \
  --scope=organizations/SEU_ORG_ID \
  --asset-types=dns.googleapis.com/ManagedZone \
  --query=sounavy
```
