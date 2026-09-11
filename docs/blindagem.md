# Blindagem do repositório

O que já está no código, e o que só você pode ligar (são interruptores de
configuração, não arquivos — nem eu nem nenhum commit os alteram).

## Já aplicado neste repositório

| Proteção | Onde | O que evita |
|---|---|---|
| `permissions: {}` no topo, mínimo por job | `.github/workflows/dns-zone-lookup.yml` | Workflow comprometido agir com o token amplo do repositório |
| `persist-credentials: false` no checkout | idem | `GITHUB_TOKEN` ficar gravado no disco do runner e vazar em step posterior |
| `timeout-minutes: 10` | idem | Job travado consumindo minutos e segurando credencial ativa |
| Credencial só via secret, com falha explícita se ausente | idem | Segredo em texto claro no YAML |
| `.gitignore` de credenciais | `.gitignore` | Commit acidental de chave de service account |
| `roles/dns.reader` (somente leitura) | `docs/como-rodar.md` | Uma chave vazada conseguir *alterar* DNS |
| Dependabot semanal | `.github/dependabot.yml` | Action vulnerável permanecer no CI sem ninguém notar |
| Revisão obrigatória do dono | `.github/CODEOWNERS` | Mudança em CI ou script entrar sem seu olhar |
| Fixação por SHA | `scripts/pin-actions.sh` | Tag `@v4` ser reapontada para código malicioso |

Rode a fixação de SHA agora (é a de maior retorno, e leva segundos):

```bash
./scripts/pin-actions.sh --dry-run   # ver o que mudaria
./scripts/pin-actions.sh             # aplicar
```

---

## O que só você liga — checklist do celular

Toque, ligue, volte. Ordem por retorno sobre esforço.

### 1. Token do Actions em somente-leitura

[**Settings → Actions → General**](https://github.com/dralbertoeliasBr/github-workflows-/settings/actions)

- Em *Workflow permissions*, marque **Read repository contents and packages permissions**.
- Desmarque *Allow GitHub Actions to create and approve pull requests*.

É o interruptor mais importante da lista: define o teto de poder de qualquer
workflow, inclusive um que entre por engano.

### 2. Proteger o branch

[**Settings → Branches**](https://github.com/dralbertoeliasBr/github-workflows-/settings/branches)

Crie uma regra para `claude/*` e para o branch padrão, com:

- **Require a pull request before merging** → 1 aprovação
- **Require review from Code Owners** (usa o `CODEOWNERS` já commitado)
- **Do not allow bypassing the above settings**
- **Block force pushes** e **Restrict deletions**

`Block force pushes` é o que protege o registro temporal: sem ele, o histórico
pode ser reescrito e o carimbo de `docs/registro-temporal.md` some.

### 3. Varredura de segredos

[**Settings → Code security**](https://github.com/dralbertoeliasBr/github-workflows-/settings/security_analysis)

- **Dependabot alerts** → ligar
- **Secret scanning** → ligar
- **Push protection** → ligar (bloqueia o push que contém uma chave, antes de
  ela chegar ao servidor)

> Em repositórios **públicos** essas três são gratuitas. Em **privados**,
> secret scanning e push protection dependem do plano — se não aparecerem, é
> isso, não é erro seu.

### 4. 2FA na conta

[**github.com/settings/security**](https://github.com/settings/security)

Todas as proteções acima caem juntas se a conta for tomada. Use app
autenticador ou passkey; SMS é o modo fraco.

### 5. Auditar os secrets

[**Settings → Secrets and variables → Actions**](https://github.com/dralbertoeliasBr/github-workflows-/settings/secrets/actions)

Se `GCP_SA_KEY` estiver cadastrado, prefira migrar para Workload Identity
Federation (`GCP_WIF_PROVIDER` + `GCP_SA_EMAIL`) e **apagar a chave**. Chave
JSON é credencial de longa duração: vazou, vale até ser revogada à mão.

---

## Fora do GitHub: o buraco mais grave é o DMARC

A blindagem do repositório não cobre o risco maior encontrado hoje. O domínio
`sounavy.com` **não tem registro DMARC** — qualquer um pode enviar e-mail se
passando por você, com chance real de entrega.

Isso não se resolve com nenhum arquivo aqui. Veja a correção em três etapas em
[`SECURITY.md`](../SECURITY.md).

## Verificação

Depois de ligar os interruptores, confira o que ficou de pé:

```bash
./scripts/pin-actions.sh --dry-run   # deve reportar 0 referencias por tag
git log --oneline --show-signature -1
```
