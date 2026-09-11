# github-workflows-

Automações operacionais rodáveis do celular — pelo Cloud Shell ou por um botão
no GitHub Actions, sem precisar de terminal na máquina.

## Buscar a zona DNS de um domínio no Google Cloud

Descobre em qual projeto GCP mora a zona Cloud DNS de um domínio, e imprime
os registros dela.

| Arquivo | O que é |
|---|---|
| [`scripts/find-dns-zone.sh`](scripts/find-dns-zone.sh) | O script. Roda em qualquer lugar com `gcloud` autenticado. |
| [`.github/workflows/dns-zone-lookup.yml`](.github/workflows/dns-zone-lookup.yml) | Roda o script pelo GitHub Actions, disparado por botão. |
| [`docs/como-rodar.md`](docs/como-rodar.md) | Os três caminhos, incluindo o que funciona no celular. |
| [`docs/sounavy-dns.md`](docs/sounavy-dns.md) | O que já foi apurado sobre `sounavy.com`, e dois problemas achados. |

### O jeito mais rápido

Em **https://shell.cloud.google.com** (já vem autenticado, abre no navegador
do celular):

```bash
git clone https://github.com/dralbertoeliasBr/github-workflows-.git && \
  bash github-workflows-/scripts/find-dns-zone.sh sounavy.com
```

### Uso do script

```bash
./scripts/find-dns-zone.sh                          # sounavy.com, projetos padrão
./scripts/find-dns-zone.sh exemplo.com              # outro domínio
./scripts/find-dns-zone.sh exemplo.com proj-a proj-b  # projetos específicos
PROJETOS="proj-a proj-b" ./scripts/find-dns-zone.sh exemplo.com
```

Requer `roles/dns.reader` nos projetos consultados. O script distingue as
falhas comuns — API desabilitada, falta de permissão, projeto inacessível — em
vez de reportar tudo como "zona não encontrada".

Códigos de saída: `0` achou · `2` não achou · `1` sem autenticação · `127` sem `gcloud`.

## Segurança

O `.gitignore` bloqueia os nomes usuais de arquivo de credencial. Nunca faça
commit de chave de service account. O caminho sem chave (Workload Identity
Federation) já é suportado pelo workflow — veja `docs/como-rodar.md`.
