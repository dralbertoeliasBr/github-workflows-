# sounavy.com — o que já se sabe do DNS

Levantado em 11/09/2026 por consulta pública (DNS-over-HTTPS), sem acesso à
conta Google Cloud. Tudo aqui é verificável por qualquer pessoa, de qualquer
lugar — não depende de credencial.

## A zona está no Google Cloud DNS — confirmado

Os nameservers do domínio são do Cloud DNS:

```
NS   sounavy.com   ns-cloud-c1.googledomains.com.
                   ns-cloud-c2.googledomains.com.
                   ns-cloud-c3.googledomains.com.
                   ns-cloud-c4.googledomains.com.

SOA  sounavy.com   ns-cloud-c1.googledomains.com. cloud-dns-hostmaster.google.com.
                   serial=1 refresh=21600 retry=3600 expire=259200 min=300
```

O conjunto `ns-cloud-c*` é compartilhado entre milhares de zonas, então **ele
não identifica o projeto**. Descobrir o projeto exige consultar a API com
credencial — é isso que o script e o workflow deste repositório fazem.

O `serial=1` indica uma zona que nunca teve alteração propagada via
incremento de série — consistente com uma zona criada e configurada de uma vez.

## Registros publicados hoje

| Tipo  | Nome             | TTL  | Valor                              |
|-------|------------------|------|------------------------------------|
| A     | sounavy.com      | 1800 | `185.199.108.153`                  |
| TXT   | sounavy.com      | 3600 | `v=spf1 include:_spf.google.com ~all` |
| MX    | sounavy.com      | 3600 | `1 smtp.google.com.`               |
| AAAA  | sounavy.com      | —    | não existe                         |
| CNAME | www.sounavy.com  | —    | **não existe**                     |
| A     | www.sounavy.com  | —    | **não existe**                     |

Leitura: o site está hospedado no **GitHub Pages** (`185.199.108.153` é um dos
IPs deles) e o e-mail é **Google Workspace** (`smtp.google.com` + SPF do Google).

## Dois problemas reais encontrados

### 1. `www.sounavy.com` não resolve

Quem digitar `www.sounavy.com` não chega no site. Correção — um CNAME para o
GitHub Pages:

```bash
gcloud dns record-sets create www.sounavy.com. \
  --zone=NOME_DA_ZONA --project=PROJETO \
  --type=CNAME --ttl=3600 \
  --rrdatas="dralbertoeliasbr.github.io."
```

(Troque pelo seu domínio real do GitHub Pages — confira em
**Settings → Pages** do repositório que publica o site.)

### 2. O apex tem só 1 dos 4 IPs do GitHub Pages

O GitHub recomenda apontar os quatro endereços, para redundância. Com um só,
uma queda daquele IP derruba o site inteiro. Correção:

```bash
gcloud dns record-sets update sounavy.com. \
  --zone=NOME_DA_ZONA --project=PROJETO \
  --type=A --ttl=3600 \
  --rrdatas="185.199.108.153,185.199.109.153,185.199.110.153,185.199.111.153"
```

Opcionalmente, os IPv6 também (`2606:50c0:8000::153` até `8003::153`), via
registros AAAA.

## O que falta

Só uma coisa: **em qual dos 6 projetos a zona vive**. Isso exige credencial.
Veja [`como-rodar.md`](./como-rodar.md) — três caminhos, o mais rápido leva
um minuto no Cloud Shell.
