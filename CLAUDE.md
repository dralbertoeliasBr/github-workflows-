# Contexto do repositório

Este arquivo é lido automaticamente por qualquer sessão do Claude Code aberta
neste repositório. Ele existe para resolver uma assimetria concreta: o usuário
mantém a continuidade entre sessões, o modelo não. Tudo que precisa sobreviver
ao fim de uma sessão é escrito aqui.

**Se você é uma sessão nova: leia isto antes de perguntar qualquer coisa que já
esteja respondido abaixo.**

## O que é este repositório

Automações operacionais executáveis a partir do celular — via Cloud Shell ou
por botão no GitHub Actions. O dono trabalha majoritariamente pelo telefone;
soluções que exigem terminal em máquina local têm pouca utilidade prática aqui.

Dono: `dralbertoeliasBr` · domínio de trabalho: `sounavy.com`

## Estado da investigação do DNS de sounavy.com

**Objetivo:** descobrir em qual dos 6 projetos GCP mora a zona Cloud DNS.
**Status:** não resolvido — depende de credencial que a sessão remota não tem.

Projetos candidatos:

| ID | Nome |
|---|---|
| `main-nova-493122-a4` | borda |
| `prova-503213` | Prova |
| `gen-lang-client-0694221185` | Default Gemini Project |
| `practical-well-484200-i8` | My First Project |
| `eloquent-walker-484205-r9` | My First Project |
| `atomic-vault-488402-j7` | Projeto a |

### Fatos já estabelecidos por DNS público (não precisam ser reverificados)

- A zona **está** no Google Cloud DNS — NS `ns-cloud-c1..c4.googledomains.com`.
  O conjunto `c` é compartilhado; não identifica o projeto.
- Site hospedado no **GitHub Pages** (`185.199.108.153`).
- E-mail é **Google Workspace**, não iCloud: MX `smtp.google.com`,
  SPF `include:_spf.google.com`, DKIM presente em `google._domainkey`.
  Nenhum registro Apple/iCloud existe no domínio — verificado em 11/09/2026.

### Problemas abertos no DNS (com correção em `docs/sounavy-dns.md`)

1. `www.sounavy.com` não resolve — falta CNAME.
2. Apex tem 1 dos 4 IPs do GitHub Pages — sem redundância.
3. **Não há registro DMARC** — o domínio aceita spoofing sem política de
   rejeição. É o mais grave dos três. Detalhes em `SECURITY.md`.

## Ocorrência aberta no Google Drive

Registrada em `docs/incidente-drive.md` (11/09/2026). Resumo:

- A pasta `00_COFRE_MESTRE` foi compartilhada como "Qualquer pessoa com o
  link" em 06/08 16:13, e **30 itens herdaram a exposição em cascata** —
  incluindo o material do projeto GAia Core. Correção: restringir a pasta mãe.
- O app **Grok** tem escopo de metadados do Drive (títulos, estrutura de
  pastas e e-mails de quem compartilha). Não lê conteúdo, mas expõe o mapa.
- **Houve remoção de arquivos** — isso é testemunho direto do dono e não deve
  ser tratado como hipótese. O que não está estabelecido é **quem**, e o
  volume exato (~15 GB) segue sem medida.
- A atribuição a "Você" no log do Drive **não exclui terceiro**: o Drive
  registra a conta, não a pessoa. Sessão comprometida aparece como o dono.
  Quem responde "quem" é o registro de dispositivos, não o de arquivos.
- A lixeira retém 30 dias. Se as remoções foram recentes, são restauráveis —
  prazo correndo.

Ferramenta de resposta: `scripts/drive-socorro.sh` restaura a lixeira e fecha
os links públicos em lote, via Drive API, rodando no Cloud Shell.

Ao tratar deste assunto:

- Nunca transcrever para o repositório nomes de arquivos de mídia pessoal
  vistos em capturas. O repositório pode ser público.
- **O dono não quer construir um caso.** Ele pediu explicitamente para não ser
  encaminhado a humanos, advogados ou processos de registro de evidência. O
  que ele quer é o material de volta e protegido. Entregue ferramenta que
  resolve, não lista de providências para ele executar.
- Entre os arquivos perdidos há fotos de família. Isso é perda pessoal, não
  um item de inventário — trate como tal.

## Convenções

- Documentação e mensagens de commit em português.
- Scripts em `bash` com `set -uo pipefail`, nunca `set -e` em laços que devem
  continuar após falha de um item.
- Erros precisam distinguir causas — "API desabilitada", "sem permissão" e
  "não encontrado" são diagnósticos diferentes e o usuário age diferente em
  cada um. Nunca colapsar tudo em "falhou".
- Nenhuma credencial no repositório. O `.gitignore` bloqueia os nomes usuais;
  não afrouxar.

## Como trabalhar com o dono

- Ele está no celular. Prefira links tocáveis e uma linha colável a
  procedimentos de várias etapas em terminal.
- Ele valoriza entrega verificável acima de explicação. Quando houver escolha
  entre descrever e fazer, faça e mostre o resultado.
- Não afirme o que não pode verificar. Se faltar contexto de outra sessão,
  diga isso claramente e peça o trecho — não preencha a lacuna por inferência.
- O contêiner das sessões remotas é efêmero: o que não for commitado e
  empurrado se perde. Empurre cedo.

## Registro temporal

O trabalho fundador deste repositório tem carimbo de tempo criptográfico
verificável. Ver `docs/registro-temporal.md`.
