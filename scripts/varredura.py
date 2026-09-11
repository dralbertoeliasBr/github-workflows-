#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
varredura.py — padrões de varredura de matriz, com round-trip verificado.

Implementa e MEDE os padrões descritos no adendo ao R45, para responder com
número, e não com suposição, a pergunta que o próprio adendo levanta:

    "Não sei ainda se isso captura mais informação real ou é só variação
     decorativa — precisa de teste com round-trip antes de entrar em
     qualquer reivindicação."

Padrões implementados:

  reto                     lê toda linha da esquerda para a direita (atual)
  boustrofedon             inverte a direção a cada linha
  boustrofedon_aninhado    inverte a direção a cada N linhas (padrão N=2)
  coluna                   varre por coluna, para servir de contraste
  zigue_diagonal           diagonais alternadas, o scan do JPEG

Uso:
    ./scripts/varredura.py               # roda o experimento completo
    ./scripts/varredura.py --largura 16  # muda a largura do teste

Só biblioteca padrão.
"""

from __future__ import annotations

import argparse
import math
import random
import zlib
from collections import Counter

Matriz = list[list[int]]
Ordem = list[tuple[int, int]]


# ========================================================================
# 1. ORDENS DE VARREDURA
#
# Cada função devolve a lista de coordenadas (linha, coluna) na ordem de
# visita. Separar a ORDEM da leitura em si é o que torna todos os padrões
# intercambiáveis e o round-trip trivialmente verificável: se a ordem é uma
# permutação das coordenadas, a reconstrução é exata por construção.
# ========================================================================

def ordem_reta(h: int, w: int) -> Ordem:
    return [(i, j) for i in range(h) for j in range(w)]


def ordem_coluna(h: int, w: int) -> Ordem:
    return [(i, j) for j in range(w) for i in range(h)]


def ordem_boustrofedon(h: int, w: int) -> Ordem:
    saida: Ordem = []
    for i in range(h):
        colunas = range(w) if i % 2 == 0 else range(w - 1, -1, -1)
        saida.extend((i, j) for j in colunas)
    return saida


def ordem_boustrofedon_aninhado(h: int, w: int, bloco: int = 2) -> Ordem:
    """Inverte a direção a cada `bloco` linhas, não a cada linha.

    Com bloco=2: D→E, D→E, E→D, E→D, ... — o padrão descrito no adendo.
    """
    saida: Ordem = []
    for i in range(h):
        para_direita = (i // bloco) % 2 == 0
        colunas = range(w) if para_direita else range(w - 1, -1, -1)
        saida.extend((i, j) for j in colunas)
    return saida


def ordem_zigue_diagonal(h: int, w: int) -> Ordem:
    """Diagonais alternadas — a varredura usada pelo JPEG."""
    saida: Ordem = []
    for d in range(h + w - 1):
        diagonal = [(i, d - i) for i in range(h) if 0 <= d - i < w]
        if d % 2 == 0:
            diagonal.reverse()
        saida.extend(diagonal)
    return saida


ORDENS = {
    "reto": ordem_reta,
    "boustrofedon": ordem_boustrofedon,
    "boustrofedon_aninhado": ordem_boustrofedon_aninhado,
    "coluna": ordem_coluna,
    "zigue_diagonal": ordem_zigue_diagonal,
}


# ========================================================================
# 2. LEITURA, RECONSTRUÇÃO E ROUND-TRIP
# ========================================================================

def varrer(m: Matriz, ordem: Ordem) -> list[int]:
    return [m[i][j] for i, j in ordem]


def desvarrer(seq: list[int], ordem: Ordem, h: int, w: int) -> Matriz:
    m = [[0] * w for _ in range(h)]
    for valor, (i, j) in zip(seq, ordem):
        m[i][j] = valor
    return m


def round_trip_ok(m: Matriz, ordem: Ordem) -> bool:
    """Verifica byte a byte que ler e reconstruir devolve o original."""
    h, w = len(m), len(m[0])
    return desvarrer(varrer(m, ordem), ordem, h, w) == m


def e_permutacao(ordem: Ordem, h: int, w: int) -> bool:
    """A ordem visita cada coordenada exatamente uma vez?"""
    return sorted(ordem) == sorted(ordem_reta(h, w))


# ========================================================================
# 3. PREDIÇÃO COM DESLOCAMENTO NEGATIVO
#
# O adendo lista "leitura com deslocamento negativo (até -12)" junto com os
# padrões de varredura, mas é outra categoria de coisa: não é uma ORDEM de
# visita, é um PREDITOR aplicado sobre a sequência já ordenada. As duas
# camadas se combinam — escolhe-se uma ordem E um deslocamento.
# ========================================================================

def residuos(seq: list[int], d: int) -> list[int]:
    """Resíduo em relação ao valor d posições atrás."""
    if d < 1:
        raise ValueError("o deslocamento precisa ser >= 1")
    return [seq[i] - seq[i - d] for i in range(d, len(seq))]


def reconstruir_de_residuos(inicio: list[int], res: list[int], d: int) -> list[int]:
    """Desfaz `residuos`. `inicio` são os d primeiros valores."""
    seq = list(inicio)
    for k, r in enumerate(res):
        seq.append(r + seq[k])
    return seq


# ========================================================================
# 4. MÉTRICAS
# ========================================================================

def entropia(valores: list[int]) -> float:
    """Entropia de Shannon em bits por símbolo."""
    if not valores:
        return 0.0
    n = len(valores)
    return -sum((c / n) * math.log2(c / n) for c in Counter(valores).values())


def bytes_comprimidos(valores: list[int]) -> int:
    """Tamanho real após zlib — a medida que não depende de teoria."""
    crus = bytes((v + 256) % 256 for v in valores)
    return len(zlib.compress(crus, 9))


def delta_medio(seq: list[int]) -> float:
    if len(seq) < 2:
        return 0.0
    return sum(abs(seq[i] - seq[i - 1]) for i in range(1, len(seq))) / (len(seq) - 1)


# ========================================================================
# 5. DADOS DE TESTE
# ========================================================================

def gradiente(h: int, w: int) -> Matriz:
    """Superfície suave: o melhor caso para codificação por diferença."""
    return [[(i * 3 + j * 2) % 256 for j in range(w)] for i in range(h)]


def foto_sintetica(h: int, w: int, semente: int = 33) -> Matriz:
    """Regiões suaves com bordas e ruído — estatística de imagem natural."""
    r = random.Random(semente)
    m = [[0] * w for _ in range(h)]
    for i in range(h):
        for j in range(w):
            base = 120 + 60 * math.sin(i / 7.0) + 40 * math.cos(j / 5.0)
            if j > w * 0.6:                      # uma borda vertical nítida
                base -= 70
            m[i][j] = max(0, min(255, int(base + r.gauss(0, 6))))
    return m


def ruido(h: int, w: int, semente: int = 33) -> Matriz:
    """Pior caso: sem correlação espacial, nenhuma ordem pode ajudar."""
    r = random.Random(semente)
    return [[r.randrange(256) for _ in range(w)] for _ in range(h)]


CONJUNTOS = {
    "gradiente": gradiente,
    "foto_sintetica": foto_sintetica,
    "ruido": ruido,
}


# ========================================================================
# 6. EXPERIMENTO
# ========================================================================

def avaliar(m: Matriz, nome_ordem: str) -> dict:
    h, w = len(m), len(m[0])
    ordem = ORDENS[nome_ordem](h, w)

    if not e_permutacao(ordem, h, w):
        raise AssertionError(f"{nome_ordem}: a ordem não é uma permutação")
    if not round_trip_ok(m, ordem):
        raise AssertionError(f"{nome_ordem}: round-trip falhou")

    seq = varrer(m, ordem)
    d1 = residuos(seq, 1)

    # O adendo propõe deslocamento até -12. Mas numa matriz de largura w,
    # lida em ordem reta, o deslocamento d = w é o que aponta para o valor
    # imediatamente ACIMA — é ele que torna o preditor bidimensional. Um
    # limite fixo de 12 nunca alcança isso, a não ser por coincidência.
    # Por isso a busca vai até w + 2, e o valor w é sempre incluído.
    candidatos = sorted(set(range(1, 13)) | set(range(w - 2, w + 3)) - {0})
    candidatos = [d for d in candidatos if 1 <= d < len(seq)]

    melhor_d, melhor_bytes = 1, bytes_comprimidos(d1)
    for d in candidatos:
        b = bytes_comprimidos(residuos(seq, d))
        if b < melhor_bytes:
            melhor_d, melhor_bytes = d, b

    return {
        "ordem": nome_ordem,
        "delta_medio": delta_medio(seq),
        "entropia_d1": entropia(d1),
        "bytes_d1": bytes_comprimidos(d1),
        "melhor_deslocamento": melhor_d,
        "bytes_melhor": melhor_bytes,
    }


def experimento(h: int, w: int) -> int:
    print("=" * 72)
    print(f"VARREDURA — experimento com round-trip · matriz {h}x{w}"
          f" ({h * w} elementos)")
    print("=" * 72)

    falhas = 0

    for nome_conj, gerar in CONJUNTOS.items():
        m = gerar(h, w)
        bruto = bytes_comprimidos([v for linha in m for v in linha])

        print(f"\n### {nome_conj}  (sem diferença, zlib: {bruto} B)\n")
        print(f"  {'ordem':<24} {'|Δ| médio':>10} {'H(Δ1)':>7} "
              f"{'zlib Δ1':>9} {'melhor d':>9} {'zlib':>7}")
        print("  " + "-" * 70)

        linhas = []
        for nome_ordem in ORDENS:
            try:
                r = avaliar(m, nome_ordem)
            except AssertionError as e:
                falhas += 1
                print(f"  {nome_ordem:<24} FALHOU: {e}")
                continue
            linhas.append(r)
            print(f"  {r['ordem']:<24} {r['delta_medio']:>10.2f} "
                  f"{r['entropia_d1']:>7.2f} {r['bytes_d1']:>9} "
                  f"{r['melhor_deslocamento']:>9} {r['bytes_melhor']:>7}")

        if linhas:
            base = next(x for x in linhas if x["ordem"] == "reto")
            melhor = min(linhas, key=lambda x: x["bytes_d1"])
            if melhor["ordem"] == "reto":
                print(f"\n  → nenhuma ordem supera o modo reto neste conjunto.")
            else:
                ganho = 100 * (base["bytes_d1"] - melhor["bytes_d1"]) / base["bytes_d1"]
                print(f"\n  → melhor: {melhor['ordem']} "
                      f"({ganho:+.1f}% de bytes em relação ao reto)")

    print("\n" + "=" * 72)
    print("LEITURA DOS NÚMEROS")
    print("=" * 72)
    print("""
Toda ordem aqui é uma PERMUTAÇÃO das mesmas coordenadas, e o round-trip é
verificado elemento a elemento antes de qualquer medida. Disso decorre um
fato que precisa ficar explícito, porque desfaz a pergunta original:

  Nenhuma ordem de varredura captura mais informação que outra.
  Todas contêm exatamente os mesmos dados — a transformação é bijetiva.

O que muda é a LOCALIDADE: o quanto valores vizinhos na sequência lida são
parecidos entre si. Isso não altera a informação, altera o custo de
codificá-la por diferença. Por isso a medida honesta é bytes após zlib, e
não "informação capturada".

O ganho do boustrofédon tem teto conhecido: ele só conserta a emenda entre o
fim de uma linha e o começo da seguinte. São (altura - 1) transições num
total de (altura x largura), ou seja, cerca de 1/largura das emendas. Quanto
mais larga a matriz, menor o ganho — e é por isso que ele aparece pequeno
aqui e desapareceria numa imagem de 4000 pixels de largura.

Sobre o deslocamento negativo: o limite de -12 proposto no adendo é
arbitrário em relação à geometria do dado. Em ordem reta, o deslocamento com
significado é d = largura, porque é ele que aponta para o valor diretamente
acima — é o que transforma um preditor de linha num preditor de plano. A
coluna "melhor d" mostra qual venceu de fato; quando ela imprime a largura da
matriz, é este efeito, e não um número escolhido a priori.
""")

    return 1 if falhas else 0


def main() -> int:
    p = argparse.ArgumentParser(description="Experimento de padrões de varredura.")
    p.add_argument("--altura", type=int, default=32)
    p.add_argument("--largura", type=int, default=32)
    args = p.parse_args()
    return experimento(args.altura, args.largura)


if __name__ == "__main__":
    raise SystemExit(main())
