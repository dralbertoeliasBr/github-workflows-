#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verificar_r15.py — recalcula, do zero, todas as contas do documento
"R15: Todas as Equações, Escritas e Testadas" (05/09/2026).

O documento original pede, por escrito, que as contas sejam conferidas à mão.
Este arquivo faz isso por máquina, sem copiar nenhum resultado de lá: parte
apenas dos dados de entrada e recalcula tudo.

Conclusão da verificação, adiantada: as seis equações do documento estão
corretas. Mas a Equação 4 SUBESTIMA a probabilidade de acaso — e corrigi-la
enfraquece ainda mais a coincidência que ela já classificava como fraca.
A correção está na seção 4-bis.

Só biblioteca padrão.
"""

from __future__ import annotations

# ---------------------------------------------------------------- entrada

NOS = {
    "Topo (Natureza/Humano)":      10,
    "Esquerda (Intenção/Verdad.)": 70,
    "Direita (Dinâmica/Alerta)":   54,
    "Semente (Neutra, centro)":     3,
    "Inferior (Criticid./Digital)":30,
}
PRIMOS = {"T": 2, "D": 3, "I": 5, "E": 7, "N": 11}
VALORES = set(NOS.values())


def regra(t: bool) -> str:
    return "CONFERE" if t else "DIVERGE"


def titulo(n: str) -> None:
    print("\n" + "=" * 68)
    print(n)
    print("=" * 68)


# ---------------------------------------------------------------- eq. 1

def equacao_1() -> bool:
    titulo("EQUAÇÃO 1 — a fórmula α + 5 + 8")
    obtidos = set()
    for nome, v in NOS.items():
        r = v + 5 + 8
        obtidos.add(r)
        print(f"  {nome:<30} {v:>3} + 5 + 8 = {r}")

    inter = obtidos & VALORES
    print(f"\n  nós do grafo        {sorted(VALORES)}")
    print(f"  resultados obtidos  {sorted(obtidos)}")
    print(f"  interseção          {sorted(inter) if inter else '{ }  (vazia)'}")
    print(f"\n  VEREDITO: FALHA — nenhum resultado é nó do grafo.  [{regra(not inter)}]")
    return not inter


# ---------------------------------------------------------------- eq. 2

def equacao_2() -> bool:
    titulo("EQUAÇÃO 2 — de onde sai o 8 (divisão por 11)")
    achou = []
    for nome, v in NOS.items():
        q, r = divmod(v, 11)
        marca = "  <- o 8 da fórmula" if r == 8 else ""
        print(f"  {nome:<30} {v:>3} = 11 x {q} + {r}{marca}")
        if r == 8:
            achou.append(nome)
    ok = achou == ["Inferior (Criticid./Digital)"]
    print(f"\n  resto 8 aparece em: {achou}  [{regra(ok)}]")
    return ok


# ---------------------------------------------------------------- eq. 3

def equacao_3() -> bool:
    titulo("EQUAÇÃO 3 — o 8 aparece com os outros primos? (controle)")
    ocorrencias = 0
    for sig, p in PRIMOS.items():
        restos = [v % p for v in NOS.values()]
        n8 = restos.count(8)
        ocorrencias += n8
        nota = f"{n8} resto(s) 8" if n8 else "nenhum resto 8"
        print(f"  mod {p:>2} ({sig})  restos: "
              f"{', '.join(str(x) for x in restos):<18} {nota}")

    print("\n  Observação aritmética que o documento não explicita:")
    print("  resto 8 é IMPOSSÍVEL para mod 2, 3, 5 e 7 — o resto é sempre")
    print("  menor que o divisor. Só mod 11 podia produzir 8.")
    print(f"\n  VEREDITO: ocorrência única.  [{regra(ocorrencias == 1)}]")
    return ocorrencias == 1


# ---------------------------------------------------------------- eq. 4

def equacao_4() -> bool:
    titulo("EQUAÇÃO 4 — qual a chance de ser acaso?")
    candidatos = [n for n in range(101) if n % 11 == 8]
    p = len(candidatos) / 101
    print(f"  números de 0 a 100 com resto 8 mod 11:")
    print(f"    {candidatos}")
    print(f"    {len(candidatos)} em 101 = {100 * p:.1f}%")
    ok = candidatos == [8, 19, 30, 41, 52, 63, 74, 85, 96]
    print(f"\n  o documento afirma 8,9%  [{regra(ok and abs(p - .089) < .002)}]")
    return ok


# ---------------------------------------------------------------- 4-bis

def equacao_4_bis() -> None:
    titulo("EQUAÇÃO 4-bis — CORREÇÃO: o documento subestima o acaso")
    print("""  A Equação 4 calcula a chance de UM número sorteado dar resto 8.
  Mas a busca não foi essa. Foram testados 5 nós contra 5 primos — e
  bastava UMA coincidência aparecer em qualquer um deles para a pista
  ser notada. Isso é o problema das comparações múltiplas: quanto mais
  lugares se olha, maior a chance de achar algo em algum deles.

  Como mod 2, 3, 5 e 7 não podem dar resto 8, as tentativas reais são 5
  (um por nó, todas sob mod 11), cada uma com chance 1/11:
""")
    p_uma = 1 / 11
    p_nenhuma = (1 - p_uma) ** 5
    p_alguma = 1 - p_nenhuma

    print(f"    chance de UM nó dar resto 8 .............. 1/11  = {100*p_uma:.1f}%")
    print(f"    chance de NENHUM dos 5 dar ............... (10/11)^5 = {100*p_nenhuma:.1f}%")
    print(f"    chance de PELO MENOS UM dar .............. {100*p_alguma:.1f}%")

    print(f"""
  O documento declara 8,9%. O número correto para o que de fato foi
  procurado é {100*p_alguma:.0f}% — mais de quatro vezes maior.

  Isso NÃO contradiz o documento: ele já classificava a pista como
  "evidência fraca" e escrevia, com todas as letras, que não havia
  provado nada. A correção apenas mostra que ele foi generoso consigo
  mesmo no único ponto em que poderia ter sido mais duro.

  Com ~38% de chance ao acaso, a coincidência do 8 deixa de ser pista
  fraca e passa a ser ruído esperado.""")


# ---------------------------------------------------------------- eq. 5

def equacao_5() -> bool:
    titulo("EQUAÇÃO 5 — 5 e 8 em Fibonacci")
    fib = [1, 1]
    while len(fib) < 10:
        fib.append(fib[-1] + fib[-2])
    print(f"  Fibonacci: {fib}")
    i5, i8 = fib.index(5), fib.index(8)
    print(f"  posição de 5 (base 0): {i5}      posição de 8: {i8}")
    print(f"  consecutivos: {regra(i8 == i5 + 1)}")
    print(f"  razão 8/5 = {8/5}   razão áurea ≈ 1,618034")
    print(f"  erro em relação à áurea: {abs(8/5 - 1.6180339887):.4f}")
    print("\n  Esta explicação não depende do grafo: é propriedade da")
    print("  sequência. É a parte mais sólida do documento.")
    return i8 == i5 + 1


# ---------------------------------------------------------------- eq. 6

def equacao_6() -> bool:
    titulo("EQUAÇÃO 6 — somas estruturais")
    vert = NOS["Topo (Natureza/Humano)"] + NOS["Inferior (Criticid./Digital)"]
    horiz = NOS["Esquerda (Intenção/Verdad.)"] + NOS["Direita (Dinâmica/Alerta)"]
    total = sum(NOS.values())
    dif = NOS["Esquerda (Intenção/Verdad.)"] - NOS["Direita (Dinâmica/Alerta)"]

    def primo(n: int) -> bool:
        return n > 1 and all(n % d for d in range(2, int(n ** .5) + 1))

    print(f"  eixo vertical    10 + 30 = {vert}          [{regra(vert == 40)}]")
    print(f"  eixo horizontal  70 + 54 = {horiz}         [{regra(horiz == 124)}]")
    print(f"  soma total               = {total}  primo? {primo(total)}"
          f"   [{regra(total == 167 and primo(total))}]")
    print(f"  diferença        70 - 54 = {dif}          [{regra(dif == 16)}]")
    print(f"\n  40 / 8   = {vert // 8}     [{regra(vert / 8 == 5)}]")
    print(f"  124 / 4  = {horiz // 4}    [{regra(horiz / 4 == 31)}]")
    print(f"  16 = 2^4 = {2**4}     [{regra(dif == 2**4)}]")
    print("\n  O próprio documento registra isto como observação e não como")
    print("  prova, pela mesma razão da 4-bis: com cinco números pequenos,")
    print("  relações assim aparecem sozinhas.")
    return vert == 40 and horiz == 124 and total == 167 and dif == 16


# ---------------------------------------------------------------- main

def main() -> int:
    print("=" * 68)
    print("VERIFICAÇÃO INDEPENDENTE — R15, 05/09/2026")
    print("Recalculado do zero, sem copiar resultados do original.")
    print("=" * 68)

    resultados = [equacao_1(), equacao_2(), equacao_3(), equacao_4()]
    equacao_4_bis()
    resultados += [equacao_5(), equacao_6()]

    titulo("RESULTADO DA VERIFICAÇÃO")
    print(f"  equações conferidas: {len(resultados)}")
    print(f"  todas batem:         {all(resultados)}")
    print("""
  1. As seis equações estão aritmeticamente corretas.
  2. A Equação 1 realmente FALHA — e o documento declara a própria falha,
     que é o que o torna confiável.
  3. A Equação 5 (Fibonacci) é a única explicação que se sustenta sozinha.
  4. A Equação 4 subestima o acaso em mais de quatro vezes. Corrigida,
     a coincidência do 8 vira ruído esperado, não pista.
  5. Segue faltando a definição operacional de α. Sem ela, nenhuma
     reivindicação pode ser feita sobre a fórmula.""")
    return 0 if all(resultados) else 1


if __name__ == "__main__":
    raise SystemExit(main())
