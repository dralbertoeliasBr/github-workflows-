# Segurança

## Como reportar uma vulnerabilidade

Abra um **Security Advisory** privado em
`Security → Advisories → Report a vulnerability`. Não abra issue pública para
falha de segurança.

---

## Achado aberto: sounavy.com não tem DMARC

**Severidade: alta.** Verificado por consulta pública em 11/09/2026.

O domínio publica SPF e DKIM, mas **não publica DMARC**:

```
_dmarc.sounavy.com   TXT   (não existe)
```

Sem DMARC, o domínio não diz aos servidores receptores o que fazer quando uma
mensagem falha na checagem. Consequências práticas:

- Qualquer um pode enviar e-mail **se passando por `@sounavy.com`** com chance
  real de entrega na caixa de entrada do destinatário.
- Você não recebe nenhum relatório de quem está tentando isso.
- SPF e DKIM sozinhos não bastam: eles validam, mas sem DMARC não há política
  de aplicação nem visibilidade.

Agrava: o SPF atual termina em `~all` (falha branda), que pede ao receptor
apenas que marque a mensagem, não que a rejeite.

### Correção

Implante em três etapas — nunca comece por `p=reject`, isso derruba e-mail
legítimo que você ainda não mapeou.

**Etapa 1 — observar (deixe rodando de 2 a 4 semanas):**

```bash
gcloud dns record-sets create _dmarc.sounavy.com. \
  --zone=NOME_DA_ZONA --project=PROJETO \
  --type=TXT --ttl=3600 \
  --rrdatas='"v=DMARC1; p=none; rua=mailto:dmarc@sounavy.com; fo=1"'
```

`p=none` não bloqueia nada ainda; serve para os relatórios começarem a chegar
em `rua` e você enxergar quem envia em seu nome.

**Etapa 2 — quarentena**, depois de confirmar nos relatórios que todo remetente
legítimo passa: troque para `p=quarantine`.

**Etapa 3 — rejeição:** `p=reject`, e aí sim aperte o SPF de `~all` para `-all`.

> A zona vive em um dos 6 projetos GCP listados em `CLAUDE.md`. Rode
> `scripts/find-dns-zone.sh` para descobrir qual, e substitua `NOME_DA_ZONA` e
> `PROJETO` acima.

---

## Credenciais

- Nunca faça commit de chave de service account. O `.gitignore` bloqueia os
  nomes usuais (`chave.json`, `*service-account*.json`, `gha-creds-*.json`).
- O workflow aceita **Workload Identity Federation** (`GCP_WIF_PROVIDER` +
  `GCP_SA_EMAIL`), que não usa chave de longa duração. Prefira isso à
  `GCP_SA_KEY` sempre que possível.
- A permissão concedida é `roles/dns.reader` — somente leitura. Não amplie sem
  necessidade demonstrada.
- Se uma chave for exposta, revogue primeiro e investigue depois:
  `gcloud iam service-accounts keys delete ID --iam-account=CONTA`.

## Cadeia de suprimentos das Actions

As actions de terceiros usadas no CI devem ser fixadas por **SHA de commit**,
não por tag — tags são móveis e podem ser reapontadas para código malicioso.
Rode `scripts/pin-actions.sh` para resolver e aplicar os SHAs atuais.

O Dependabot (`.github/dependabot.yml`) acompanha as atualizações semanalmente
e abre PR quando houver versão nova.
