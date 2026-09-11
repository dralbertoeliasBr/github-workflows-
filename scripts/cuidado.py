#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cuidado.py — trajetória de cuidado: a inclinação, não o episódio.

O PROBLEMA
----------
"Qual é a hora de tirar a pessoa da casa dela?" Essa pergunta nunca é
respondida por um evento isolado. Uma queda não decide nada; três quedas em
um mês, depois de seis meses com nenhuma, decidem.

E há uma razão específica pela qual as famílias erram essa conta:
HABITUAÇÃO. Quem convive se adapta ao declínio na mesma velocidade em que
ele acontece, e deixa de enxergá-lo. O filho que visita toda semana não
percebe a rampa — percebe o degrau, quando já é tarde. Um registro objetivo
não habitua.

Essa é a contribuição real de um cuidado digital: não vigiar, e sim
sustentar a memória longitudinal que nenhum cuidador humano consegue manter
com fidelidade.

O QUE ESTE MÓDULO NÃO FAZ
-------------------------
Não decide internação. Não diagnostica. Não substitui avaliação clínica.
A decisão é clínica e humana; o que a ferramenta entrega é a trajetória
objetiva sobre a qual essa decisão é tomada, e o registro de que ela existiu.

PRINCÍPIOS DE DESENHO
---------------------
1. EVENTO, NÃO CENA. Não é preciso câmera para saber que alguém caiu. Grava-
   se o evento e sua hora — nunca imagem, nunca áudio, nunca o conteúdo da
   vida da pessoa. O que não é coletado não vaza.

2. O APARELHO QUE JÁ EXISTE. O desenho supõe o telefone no bolso, não
   equipamento novo. Cuidado digital que exige hardware caro só chega a quem
   já tem tudo — e essa é exatamente a população que menos precisa.

3. DIRETIVA ANTECIPADA. A pessoa configura as regras ENQUANTO AINDA PODE.
   Quando a capacidade declina, valem as regras que ela mesma deixou, não as
   que a família decidir depois. É testamento vital em forma de configuração.

4. REGISTRO À PROVA DE ADULTERAÇÃO. A trajetória entra numa cadeia de hashes
   (a mesma de testemunha.py). Isso protege os dois lados: a pessoa contra
   internação por conveniência alheia, e o cuidador contra acusação de
   negligência. Ninguém reescreve a história depois.

Só biblioteca padrão.
"""

from __future__ import annotations

import argparse
import pathlib
import statistics
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import testemunha  # noqa: E402  — reaproveita a cadeia de hashes


# ========================================================================
# 1. VOCABULÁRIO DE EVENTOS
#
# Fechado de propósito. Um vocabulário aberto viraria diário da vida da
# pessoa; este só admite sinais de segurança e autonomia.
# ========================================================================

EVENTOS = {
    "queda":               ("queda detectada", 3),
    "quase_queda":         ("desequilíbrio sem queda", 1),
    "saida_noturna":       ("saiu de casa entre 0h e 5h", 2),
    "dose_perdida":        ("medicação não confirmada", 2),
    "inatividade":         ("sem movimento por período atípico", 2),
    "desorientacao":       ("relato de desorientação", 2),
    "fogao_aceso":         ("fogão aceso sem uso prolongado", 3),
    "porta_aberta":        ("porta externa aberta por muito tempo", 1),
    "chamada_ajuda":       ("pedido de ajuda acionado", 3),
}


def descrever(tipo: str) -> str:
    return EVENTOS.get(tipo, (tipo, 1))[0]


def gravidade(tipo: str) -> int:
    return EVENTOS.get(tipo, (tipo, 1))[1]


# ========================================================================
# 2. REGISTRO
# ========================================================================

def registrar(cadeia: list[dict], mestra: bytes, tipo: str,
              instante: datetime, nota: str = "") -> dict:
    """Sela um evento na cadeia. O corpo cifrado guarda só tipo e nota."""
    if tipo not in EVENTOS:
        raise ValueError(f"evento fora do vocabulário: {tipo}")
    corpo = f"{tipo}|{nota}".encode()
    return testemunha.selar(cadeia, corpo, mestra,
                            instante=instante.astimezone(timezone.utc).isoformat())


def eventos_de(cadeia: list[dict], mestra: bytes) -> list[tuple[datetime, str]]:
    """Abre a cadeia e devolve (instante, tipo). Requer a chave."""
    saida = []
    for e in cadeia:
        claro = testemunha.decifrar(mestra, e["selo"]).decode()
        saida.append((datetime.fromisoformat(e["instante"]), claro.split("|")[0]))
    return saida


# ========================================================================
# 3. TRAJETÓRIA — a inclinação
# ========================================================================

def por_janela(eventos: list[tuple[datetime, str]], fim: datetime,
               dias: int = 30, janelas: int = 6) -> list[dict]:
    """Agrupa em janelas consecutivas, da mais antiga para a mais recente."""
    saida = []
    for k in range(janelas - 1, -1, -1):
        fim_j = fim - timedelta(days=dias * k)
        ini_j = fim_j - timedelta(days=dias)
        dentro = [(i, t) for i, t in eventos if ini_j < i <= fim_j]
        saida.append({
            "inicio": ini_j,
            "fim": fim_j,
            "n": len(dentro),
            "peso": sum(gravidade(t) for _, t in dentro),
            "tipos": sorted({t for _, t in dentro}),
        })
    return saida


def inclinacao(valores: list[float]) -> float:
    """Coeficiente angular por mínimos quadrados. Positivo = piorando."""
    n = len(valores)
    if n < 2:
        return 0.0
    xs = list(range(n))
    mx, my = statistics.fmean(xs), statistics.fmean(valores)
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, valores)) / den


def avaliar_trajetoria(janelas: list[dict]) -> dict:
    pesos = [j["peso"] for j in janelas]
    incl = inclinacao(pesos)
    recentes = pesos[-2:] if len(pesos) >= 2 else pesos
    antigos = pesos[:-2] if len(pesos) > 2 else []

    media_antiga = statistics.fmean(antigos) if antigos else 0.0
    media_recente = statistics.fmean(recentes) if recentes else 0.0

    return {
        "inclinacao": incl,
        "media_antiga": media_antiga,
        "media_recente": media_recente,
        "variacao": (media_recente - media_antiga),
        "graves_recentes": sum(1 for j in janelas[-2:] for t in j["tipos"]
                               if gravidade(t) >= 3),
    }


# ========================================================================
# 4. RELATÓRIO
# ========================================================================

def relatorio(cadeia: list[dict], mestra: bytes, fim: datetime,
              dias: int = 30, janelas: int = 6) -> int:
    ok, msg = testemunha.conferir_cadeia(cadeia)
    eventos = eventos_de(cadeia, mestra)
    js = por_janela(eventos, fim, dias, janelas)
    a = avaliar_trajetoria(js)

    print("=" * 70)
    print("TRAJETÓRIA DE CUIDADO")
    print("=" * 70)
    print(f"registro: {'íntegro' if ok else 'ADULTERADO'} — {msg}")
    print(f"janelas de {dias} dias, da mais antiga para a mais recente\n")

    maior = max((j["peso"] for j in js), default=1) or 1
    for j in js:
        barra = "█" * round(24 * j["peso"] / maior)
        print(f"  {j['fim'].strftime('%d/%m/%Y')}  "
              f"{j['n']:>2} ev  peso {j['peso']:>3}  {barra}")

    print("\n" + "-" * 70)
    print(f"  inclinação        {a['inclinacao']:+.2f} por janela")
    print(f"  média anterior    {a['media_antiga']:.1f}")
    print(f"  média recente     {a['media_recente']:.1f}")
    print(f"  variação          {a['variacao']:+.1f}")

    print("\n" + "=" * 70)
    if a["inclinacao"] > 1.0 and a["variacao"] > 2:
        print("LEITURA: trajetória de agravamento sustentado.")
        print("\nNão é um episódio. É inclinação positiva ao longo de várias")
        print("janelas — o padrão que a convivência diária esconde por")
        print("habituação, e que uma reavaliação clínica deve considerar.")
    elif a["inclinacao"] > 0.3:
        print("LEITURA: leve tendência de aumento. Acompanhar.")
    else:
        print("LEITURA: sem tendência de agravamento nas janelas observadas.")

    print("\nEsta ferramenta NÃO decide internação e NÃO diagnostica.")
    print("Ela entrega a trajetória objetiva; a decisão é clínica e humana.")
    return 0


# ========================================================================
# 5. DEMONSTRAÇÃO
# ========================================================================

def demonstrar() -> int:
    from random import Random
    r = Random(33)
    mestra, _ = testemunha.nova_mestra()
    cadeia: list[dict] = []
    fim = datetime(2026, 9, 11, tzinfo=timezone.utc)

    # Seis meses em que a frequência e a gravidade sobem devagar — a rampa
    # que a família não enxerga porque se adapta junto.
    perfil = [
        (6, ["quase_queda"]),
        (5, ["quase_queda", "dose_perdida"]),
        (4, ["quase_queda", "dose_perdida", "porta_aberta"]),
        (3, ["dose_perdida", "saida_noturna", "quase_queda"]),
        (2, ["queda", "saida_noturna", "dose_perdida", "desorientacao"]),
        (1, ["queda", "queda", "fogao_aceso", "saida_noturna", "desorientacao"]),
    ]
    for meses_atras, tipos in perfil:
        base = fim - timedelta(days=30 * meses_atras)
        for tipo in tipos:
            registrar(cadeia, mestra, tipo,
                      base + timedelta(days=r.randrange(1, 29),
                                       hours=r.randrange(24)))

    return relatorio(cadeia, mestra, fim)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Trajetória de cuidado: a inclinação, não o episódio.")
    p.add_argument("--demo", action="store_true", default=True)
    p.parse_args()
    return demonstrar()


if __name__ == "__main__":
    sys.exit(main())
