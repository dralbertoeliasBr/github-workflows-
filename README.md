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
| [`docs/sounavy-dns.md`](docs/sounavy-dns.md) | O que já foi apurado sobre `sounavy.com`, e os problemas achados. |

## Blindagem

| Arquivo | O que é |
|---|---|
| [`docs/blindagem.md`](docs/blindagem.md) | O que já está aplicado e o checklist de interruptores do GitHub, feito para o celular. |
| [`SECURITY.md`](SECURITY.md) | Política de segurança e o achado aberto: **`sounavy.com` não tem DMARC**. |
| [`scripts/pin-actions.sh`](scripts/pin-actions.sh) | Fixa as GitHub Actions por SHA de commit, em vez de tag móvel. |
| [`docs/registro-temporal.md`](docs/registro-temporal.md) | Carimbo de tempo verificável do commit fundador, e o que ele prova. |
| [`scripts/drive_socorro.py`](scripts/drive_socorro.py) | **Recupera a lixeira do Drive e fecha compartilhamentos públicos, em lote.** |
| [`scripts/varredura.py`](scripts/varredura.py) | Padrões de varredura de matriz, com round-trip verificado e medição por zlib. |
| [`scripts/testemunha.py`](scripts/testemunha.py) | Testemunho selado: cifra + chave partida com limiar + cadeia de hashes. |
| [`docs/testemunha.md`](docs/testemunha.md) | A arquitetura do testemunho selado, e onde ela não alcança. |
| [`scripts/cuidado.py`](scripts/cuidado.py) | Trajetória de cuidado: a inclinação do declínio, que a convivência esconde. |
| [`tests/`](tests/) | Suíte de testes — `python3 -m unittest discover -s tests` |
| [`docs/incidente-drive.md`](docs/incidente-drive.md) | Ocorrência aberta: exposição pública em cascata no Google Drive e apps com acesso à conta. |
| [`CLAUDE.md`](CLAUDE.md) | Contexto que sobrevive ao fim de cada sessão. |

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
