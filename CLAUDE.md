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

Ferramenta de resposta: `scripts/drive_socorro.py` restaura a lixeira, busca
por ano de criação e fecha os links públicos em lote, via Drive API, rodando
no Cloud Shell. Tem testes em `tests/`, executados pelo CI.

Ao tratar deste assunto:

- Nunca transcrever para o repositório nomes de arquivos de mídia pessoal
  vistos em capturas. O repositório pode ser público.
- **O dono não quer construir um caso.** Ele pediu explicitamente para não ser
  encaminhado a humanos, advogados ou processos de registro de evidência. O
  que ele quer é o material de volta e protegido. Entregue ferramenta que
  resolve, não lista de providências para ele executar.
- Entre os arquivos perdidos há fotos de família. Isso é perda pessoal, não
  um item de inventário — trate como tal.

## Varredura de matriz (adendo ao R45)

`scripts/varredura.py` implementa e mede os padrões de leitura propostos.
Resultados já estabelecidos, com round-trip verificado — não refazer sem
motivo:

- Toda ordem de varredura é **permutação**: nenhuma captura mais informação
  que outra. O que muda é localidade, medida em bytes após zlib.
- O **boustrofédon aninhado** (troca a cada 2 linhas) é sempre pior que o
  simples. É decorativo — a conclusão está travada em teste.
- O **boustrofédon simples** ajuda ~2,5% em dado tipo foto e **piora** em dado
  regular, porque troca delta constante por delta alternado.
- O ganho do boustrofédon é limitado a ~1/largura das transições.
- O achado principal: o **deslocamento d = largura** vence tudo (−10,5% em
  foto sintética), e o teto de −12 proposto no adendo nunca o alcança. O
  deslocamento importa mais que a ordem de varredura.
- O zigue-zague diagonal do JPEG aplicado a pixel cru é muito pior; no JPEG
  ele opera sobre coeficientes DCT, não sobre o pixel.

## Testemunho selado (ciclo de arquitetura GaIA)

`scripts/testemunha.py` + `docs/testemunha.md`. Responde à assimetria de
registro: a pessoa é gravada e não grava, e quem mais precisa de prova é quem
menos consegue produzi-la.

Desenho: cifra no aparelho + chave partida em n com limiar k (Shamir) +
cadeia de hashes. Separa **existência e integridade** (públicas, verificáveis
sem chave alguma) de **conteúdo** (fechado, só abre com k partes reunidas).
Protege a pessoa atendida contra abuso e o profissional contra acusação falsa
com a mesma operação — "paz armada", termo do dono.

Limites já registrados, não reabrir como se fossem resolvidos:

- O **gatilho** (quando selar) não está resolvido e é político antes de
  técnico. Sempre-ligado cobre a vítima incapacitada e cria registro
  permanente; acionado-pela-pessoa falha justamente em quem foi dopado.
- O desenho supõe **interesses divergentes** entre os guardiões das partes.
  Funciona no consultório, com terceira parte institucional; é fraco na rua
  e no motel, onde não há custodiante combinado de antemão.
- A cifra usa HMAC-SHA256 porque a stdlib não traz AES. É demonstração de
  protocolo; produção pede AES-GCM.
- Licitude de registro varia por jurisdição: tem de ser parâmetro
  configurável e auditável, nunca suposição embutida. Não dar orientação
  jurídica.

## Trajetória de cuidado (ciclo GaIA)

`scripts/cuidado.py`. Responde a "qual é a hora de tirar a pessoa da casa
dela?" — pergunta que nenhum evento isolado responde. Quem responde é a
**inclinação** ao longo de janelas.

Tese central: **habituação**. Quem convive se adapta ao declínio na mesma
velocidade em que ele ocorre e deixa de enxergá-lo; percebe o degrau, não a
rampa. Registro objetivo não habitua — essa é a contribuição real do cuidado
digital, e não vigiar.

Desenho:

- **Evento, não cena.** Vocabulário fechado de nove eventos de segurança.
  Nunca imagem, nunca áudio. O que não é coletado não vaza.
- **O aparelho que já existe.** Supõe o telefone no bolso. Cuidado digital
  que exige hardware caro só alcança quem menos precisa — a objeção de
  desigualdade de recurso é do dono e é procedente.
- **Diretiva antecipada.** A pessoa configura enquanto ainda pode; depois
  valem as regras dela, não as que a família decidir.
- Reaproveita a cadeia de hashes de `testemunha.py`: protege a pessoa contra
  internação por conveniência e o cuidador contra acusação de negligência.

Limite explícito no código e na saída: **não decide internação, não
diagnostica.** Entrega a trajetória; a decisão é clínica e humana.

## Convenções

- Documentação e mensagens de commit em português.
- `bash` só para casca fina em volta de um binário (ex.: `gcloud`), com
  `set -uo pipefail` e nunca `set -e` em laços que devem continuar após falha
  de um item. Qualquer coisa que manipule JSON ou fale com API REST é Python:
  a versão em bash do drive-socorro foi reescrita por esse motivo.
- Código novo em Python vem com teste em `tests/`, usando só a biblioteca
  padrão e substituindo a rede por dublê.
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
