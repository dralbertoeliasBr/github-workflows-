# Testemunho selado — arquitetura, e onde ela não alcança

Nota de arquitetura para o ciclo GaIA. Implementação em
[`scripts/testemunha.py`](../scripts/testemunha.py), com testes em
[`tests/test_testemunha.py`](../tests/test_testemunha.py).

## A assimetria

No mercado, na rua, no elevador, no consultório, a pessoa **é gravada e não
grava**. Câmera de estabelecimento, câmera de rua, câmera de terceiro: a
imagem dela é colhida sem que ela decida. O inverso não vale.

E quem mais precisa de prova determinística é exatamente quem menos consegue
produzi-la: a vítima de um crime sem testemunha. Quando o crime depende
justamente de deixar a pessoa incapaz de registrar — o caso da substância que
apaga a noite — a ausência de prova não é acidente do caso, é **parte do
método do crime**.

O consultório mostra a mesma assimetria em forma administrativa: exige-se
acompanhante na sala para proteger paciente e profissional, mas proíbe-se
imagem. Fica-se com uma testemunha que esquece, que pode ser contestada, e
que não protege ninguém depois que a palavra vira palavra contra palavra.

## Por que "que cada um grave tudo" é a resposta errada

A saída ingênua cria dois males maiores:

1. **Vigilância total.** Se todo aparelho grava todo ambiente, o resultado
   não é proteção distribuída, é vigilância distribuída.
2. **A mesma arma na mão errada.** Toda capacidade entregue à vítima é
   entregue, no mesmo lote, ao agressor. Quem desenha para uma população
   precisa supor que o agressor recebe a mesma ferramenta, com a mesma
   qualidade.

Um desenho que não sobrevive a essas duas objeções não deve ser construído.

## O que este desenho faz

A chave está em separar duas coisas que costumam vir coladas:

```
existência e integridade  →  públicas, verificáveis por qualquer um, sem chave
conteúdo                  →  fechado, e só abre por acordo de k partes
```

Três mecanismos, todos testados:

**1. Cifra no aparelho.** O conteúdo nunca sai em claro.

**2. Chave partida com limiar (Shamir).** A chave é dividida em `n` partes,
das quais `k` são necessárias. Com `k ≥ 2` e as partes em mãos com interesses
divergentes, **ninguém abre sozinho** — nem o tutor, nem o profissional, nem
quem tomar o aparelho. E `k−1` partes não revelam *quase* nada: revelam
**nada**, no sentido matemático.

**3. Cadeia de hashes.** Cada entrada carrega o hash da anterior. Provar que
um testemunho existiu, quando, com que tamanho, e que não foi alterado
**não exige chave nenhuma**. Inserir, remover ou reordenar quebra a cadeia de
forma detectável por qualquer terceiro.

## A propriedade que torna o desenho defensável

Ele protege os dois lados com a **mesma operação**. A paciente contra o
abuso; o profissional contra a acusação falsa — e a acusação falsa é ruína
real para quem vive de reputação, em que o escândalo já basta, antes de
qualquer apuração.

Nenhum dos dois dispara sozinho. É o que o autor chamou de **paz armada**:
os dois lados seguram algo, e é justamente por isso que nenhum precisa usar.

## O que este desenho NÃO resolve

Esta seção é a mais importante do documento.

### O gatilho — quando selar

O módulo não decide quando selar, e essa omissão é deliberada: é o problema
difícil, e ele é político antes de ser técnico.

- **Sempre ligado** resolve o caso da vítima incapacitada — que é exatamente
  o caso mais grave — e cria gravação permanente de tudo. O selo reduz o
  dano, porque o mal da vigilância é em boa parte o mal do *acesso*, e aqui
  o acesso exige acordo. Mas não elimina: metadado continua vazando (que
  houve registro, quando, por quanto tempo).
- **Acionado pela pessoa** preserva autonomia e falha justamente onde mais se
  precisa: quem foi dopado não aciona nada.

Não há escolha limpa entre os dois. Quem disser que há está vendendo.

### A hipótese de interesses divergentes

O desenho supõe que as `k` partes não conluiam. Se o agressor detém uma das
partes, ele é coautor da custódia da prova contra si. No consultório isso se
resolve com a terceira parte neutra — conselho profissional, cartório,
custódia institucional. **Na rua, no motel, no transporte, não existe
terceira parte combinada de antemão**, e é aí que o desenho é mais fraco
justamente no caso que motivou pensá-lo.

### O custodiante vira centro de poder

Quem guarda a parte neutra acumula capacidade sobre muita gente. Isso precisa
de desenho institucional próprio — rodízio, pluralidade de custodiantes,
auditoria pública da cadeia — e nenhum desses é problema de código.

### A primitiva criptográfica

A cifra em `testemunha.py` é construída sobre HMAC-SHA256 porque a biblioteca
padrão do Python não traz AES. Serve para demonstrar e **testar o protocolo**.
Em produção, troque por AES-GCM (`cryptography`): a arquitetura não muda, só
a primitiva.

### O enquadramento legal

A licitude de registrar ambiente e pessoas **varia por jurisdição e por
situação** — quem participa da conversa, onde ocorre, que expectativa de
privacidade existe, que finalidade se declara. Este documento não dá
orientação jurídica e não deve ser lido como tal.

O que interessa à arquitetura é consequência de projeto: a regra de quando se
pode registrar tem de ser **parâmetro configurável do sistema, verificável e
auditável** — nunca suposição embutida no código. Um sistema que assume uma
jurisdição está errado em todas as outras.

## Estatuto deste documento

| Afirmação | Estatuto |
|---|---|
| Ninguém abre com menos de `k` partes | **verificado** — teste sobre todas as combinações |
| Adulterar a cadeia é detectável | **verificado** — teste em cada campo e posição |
| Conferir integridade não exige chave | **verificado** |
| O desenho protege os dois lados igualmente | **declarado** — decorre da estrutura, não medido em campo |
| Sempre-ligado com selo é preferível a não registrar | **não testado** — juízo de valor, não resultado |

Rode a demonstração:

```bash
./scripts/testemunha.py
python3 -m unittest tests.test_testemunha -v
```
