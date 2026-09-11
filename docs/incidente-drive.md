# Registro de ocorrência — Google Drive e apps vinculados

Levantado em 11/09/2026 a partir de capturas de tela da conta Google do dono.
Este documento registra **o que as evidências mostram** e separa isso do que
elas não permitem concluir.

> **Nota de privacidade:** nomes de arquivos pessoais vistos nas capturas não
> são transcritos aqui. Este repositório pode ser lido por terceiros; copiar
> para dentro dele os nomes de mídia privada repetiria a exposição que este
> documento existe para conter.

---

## 1. Exposição pública por herança de pasta — **severidade: crítica**

### O que o log de atividade mostra

| Data/hora | Evento | Escopo resultante |
|---|---|---|
| 26/07 23:51 | Um item compartilhado por mudança em pasta mãe | Qualquer pessoa na Internet com o link · Leitor |
| 26/07 23:52 | Permissões alteradas no mesmo item | Qualquer pessoa na Internet com o link · Comentador |
| 26/07 23:52 | Acesso restrito novamente a esse item | (revertido) |
| 06/08 16:13 | **"Você compartilhou um item" → pasta `00_COFRE_MESTRE`** | — |
| 06/08 16:13 | **"Devido a uma mudança em uma pasta mãe, 30 itens foram compartilhados"** | Qualquer pessoa na Internet com o link · Leitor |
| 06/08 16:43 | `00_COFRE_MESTRE / GAIA_COMAND…` | Qualquer pessoa na Internet com o link · Leitor |

### O mecanismo

No Google Drive, a permissão desce da pasta para o conteúdo. Compartilhar
**uma** pasta como "Qualquer pessoa com o link" torna público, em cascata,
tudo que está dentro dela — presente e futuro — sem confirmação item a item.
O log registra isso como "devido a uma mudança em uma pasta mãe".

```
compartilhar(pasta)  ⟹  público(todo descendente)
```

Os 30 itens não foram compartilhados individualmente por ninguém. Eles
herdaram o estado da pasta mãe no mesmo minuto — 16:13 — em que a pasta foi
compartilhada.

### Correção imediata

1. Abrir `00_COFRE_MESTRE` no Drive
2. Compartilhar → Acesso geral → trocar "Qualquer pessoa com o link" por
   **"Restrito"**
3. Repetir para qualquer outra pasta que apareça como pública
4. Conferir o resultado pesquisando no Drive por: `is:shared`

> Trocar para "Restrito" **não** revoga links já copiados por terceiros que já
> baixaram o conteúdo. Revoga o acesso futuro. Para material sensível, o
> correto é restringir **e** considerar o conteúdo como já circulante.

---

## 2. Apps com acesso à conta — **severidade: média**

Dois aplicativos aparecem em "Qualquer acesso à conta":

| App | Acesso observado |
|---|---|
| Google AI Studio | acesso à conta |
| **Grok** | **metadados do Google Drive** |

O escopo concedido ao Grok, conforme a própria tela do Google, permite ver:

- títulos e descrições dos arquivos;
- **nomes e endereços de e-mail das pessoas com quem os arquivos são compartilhados**;
- a estrutura de pastas e como os arquivos estão organizados.

**Precisão importante:** isso é o escopo de *metadados*
(`drive.metadata.readonly`). Ele **não** dá acesso ao conteúdo dos arquivos —
não baixa vídeo, não lê o texto dentro do documento. Mas expõe o mapa completo
do Drive e a rede de contatos com quem se compartilha, o que já é sensível.

### Correção

Em **myaccount.google.com/connections**, abrir cada app e usar
**"Remover todo o acesso"**. Remover derruba recursos daquele app que dependam
do Drive — é o custo esperado, não um erro.

Revise também "Fazer login com o Google (27)": 27 serviços autenticam com esta
conta. Todo app nessa lista que não for reconhecido deve sair.

---

## 3. Sobre os arquivos que desapareceram — **não concluído**

O dono relata remoções graduais e depois em massa, incluindo ~15 GB em um dia.
**As capturas fornecidas não comprovam nem descartam isso.** O que elas mostram
é a linha de atividade de compartilhamento; as entradas de lixeira visíveis
estão atribuídas ao próprio dono ("Você moveu 1 item para a lixeira"), o que
não é prova de ação de terceiro.

Isso não significa que o relato seja falso. Significa que ainda não foi
verificado. Onde a resposta está:

| Verificar | Onde | O que estabelece |
|---|---|---|
| Lixeira | `drive.google.com/drive/trash` | Itens apagados nos últimos 30 dias e por quem |
| Atividade completa | Drive → painel "Atividade" | Quem apagou, quando, de qual dispositivo |
| Sessões e dispositivos | `myaccount.google.com/device-activity` | Se há sessão que não é sua |
| Eventos de segurança | `myaccount.google.com/notifications` | Logins, mudanças de senha, novos apps |
| Encaminhamento e filtros | Gmail → Config. → Encaminhamento | Regra que exfiltra e-mail silenciosamente |
| Plano e cobrança | `one.google.com/storage` | Se o plano de 5 TB foi contratado por você e quando |

Sobre o plano: 5 TB é um degrau real do Google One (100 GB, 200 GB, 2 TB,
5 TB, 10 TB…). Se o salto de 2 TB para 5 TB não foi feito por você, o histórico
de pagamento em `pay.google.com` mostra a data e o meio de pagamento. Isso é
verificável e vale verificar — é uma pergunta com resposta objetiva, não uma
suspeita solta.

---

## 4. Preservar evidência antes de mexer

Se houver intenção de usar isto como prova em qualquer instância, exporte
**antes** de corrigir as permissões — a correção altera o estado que se quer
documentar.

1. **Google Takeout** (`takeout.google.com`): exportar Drive e Atividade.
2. **Capturas com relógio visível**, como as já feitas — a hora do sistema na
   imagem é parte da evidência.
3. **Histórico de conversas**: claude.ai → Configurações → Privacidade →
   Exportar dados.

Os hashes e carimbos deste repositório (ver `docs/registro-temporal.md`)
atestam integridade **dos arquivos daqui**. Eles não atestam nada sobre o
conteúdo do Drive — para aquilo, a exportação do Takeout é a fonte.

---

## Ordem de execução recomendada

1. Exportar evidência (Takeout), se for usar como prova
2. **Restringir `00_COFRE_MESTRE`** — é a exposição que está ativa agora
3. Remover acesso do Grok e revisar os 27 apps de login
4. Conferir dispositivos e eventos de segurança
5. Só então investigar as remoções, com a lixeira e a atividade completa
