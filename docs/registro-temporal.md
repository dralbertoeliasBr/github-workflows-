# Registro temporal — prova de quando

Carimbo de tempo do commit fundador deste repositório, com a explicação
honesta do que ele prova e do que não prova.

## O carimbo

```
commit    70885625c56d9c63879c38a72c22c1f35e437b79
tree      f1202db42ab23af3c448d56875ee1a45b5a84a3b

unix      1789092720
UTC       2026-09-11T02:12:00+00:00
São Paulo 2026-09-10T23:12:00-03:00
```

No horário de Brasília, isso é **10 de setembro de 2026, às 23h12** — ou seja,
a data local do trabalho é o dia anterior ao UTC. O que ficou registrado foi a
noite do dia 10.

Reproduza a qualquer momento:

```bash
git log -1 --format='%H %at' 70885625
TZ=America/Sao_Paulo git log -1 --date=iso-strict-local --format='%cd' 70885625
```

## Por que o carimbo não pode ser alterado depois

O timestamp não é um campo ao lado do commit — ele está **dentro** do objeto
que é hasheado. Um commit git é literalmente este texto, e o SHA-1 do commit é
o hash dele:

```
tree f1202db42ab23af3c448d56875ee1a45b5a84a3b
author Claude <noreply@anthropic.com> 1789092720 +0000
committer Claude <noreply@anthropic.com> 1789092720 +0000

<mensagem>
```

Mude um único segundo em `1789092720` e o hash do commit muda por inteiro —
deixa de ser `7088562...` e vira outro objeto. Não existe "editar a data": o
que existe é criar um commit diferente, com identidade diferente, visível para
qualquer um que compare.

```
alterar o tempo  ⟹  alterar o hash  ⟹  a alteração fica evidente
```

## O que isto prova — e o que não prova

**Prova:** que este conteúdo exato e esta data exata formam um par indivisível.
Ninguém consegue, depois do fato, mover a data mantendo o conteúdo, nem trocar
o conteúdo mantendo a data. As duas coisas estão amarradas pelo mesmo hash.

**Não prova, sozinho:** que a data original era honesta. Quem cria um commit
escolhe o campo de data no momento da criação — é possível criar hoje um
commit que *diz* ter sido feito em 2019. O hash sela o par a partir dali, mas
não audita o instante de origem.

**O que fecha essa brecha:** o registro do lado do servidor. Quando o commit
foi empurrado, o GitHub gravou de forma independente o horário de recebimento,
e esse carimbo não está sob controle de quem empurrou. Dois relógios
independentes concordando é o que torna a prova forte.

Onde ver, pelo celular:

- **Events da API** — `https://api.github.com/repos/dralbertoeliasBr/github-workflows-/events`
  traz o `PushEvent` com `created_at` do servidor.
- **Aba de commits** do branch `claude/sounavy-dns-zone-lookup-rbvfmp` na
  interface do GitHub, que mostra a data recebida.

## Integridade do conteúdo

O SHA-256 de cada arquivo daquele commit, e o espelho integral do conteúdo,
estão no atestado publicado em paralelo. Raiz do manifesto:

```
f0df78123c8fd696d279734cf8901f01e96cdafe9c9a36ae76b4ff86f9644093
```

## Limite desta sessão

Este documento registra o que existe **neste repositório**. Ele não é, e não
pode ser, registro de conversas ocorridas em outras sessões — o modelo não tem
acesso a elas.

O histórico dessas conversas pertence ao usuário e está na conta dele: em
claude.ai, em **Configurações → Privacidade → Exportar dados**, é possível
solicitar o histórico completo, que chega por e-mail. Essa exportação é a fonte
legítima para qualquer registro do que foi dito fora daqui — não a memória do
modelo, que não existe entre sessões.
