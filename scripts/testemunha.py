#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
testemunha.py — testemunho selado: ninguém na sala abre sozinho.

PROBLEMA
--------
Há uma assimetria real: no mercado, na rua, no elevador, a pessoa é gravada
e não grava. Quem precisa de prova determinística — a vítima de um crime sem
testemunha — é justamente quem não tem como produzi-la. E a solução ingênua,
"que cada um grave tudo", cria vigilância total e entrega ao agressor a mesma
ferramenta que se quis dar à vítima.

O consultório é o caso que mostra a saída. Exige-se acompanhante na sala para
proteger a paciente E o profissional: a presença de um terceiro protege os
dois lados ao mesmo tempo, e nenhum deles controla o que o terceiro viu.

ARQUITETURA
-----------
Este módulo implementa esse terceiro em software:

  1. O conteúdo é cifrado no aparelho. Nunca sai em claro.
  2. A chave é PARTIDA em n partes, das quais k são necessárias para abrir.
     Com k >= 2 e as partes em mãos diferentes, NINGUÉM abre sozinho — nem
     o tutor, nem o profissional, nem quem tomar o aparelho.
  3. O registro é uma CADEIA DE HASHES: cada entrada carrega o hash da
     anterior. Provar que um testemunho existiu, quando existiu e que não
     foi alterado NÃO exige abrir o conteúdo nem ter chave nenhuma.

Disso decorre a propriedade que torna o desenho defensável:

    existência e integridade  ->  públicas, verificáveis por qualquer um
    conteúdo                  ->  fechado, e só abre por acordo de k partes

O selo protege a vítima de abuso e o profissional de acusação falsa, com a
mesma operação. É paz armada: os dois lados seguram algo, nenhum dos dois
dispara sozinho.

LIMITE HONESTO DESTE ARQUIVO
----------------------------
A cifra aqui é construída sobre HMAC-SHA256 (fluxo de chave + autenticação),
porque a biblioteca padrão do Python não traz AES. A construção é íntegra e
serve para demonstrar e testar o PROTOCOLO. Em produção, troque por AES-GCM
(pacote `cryptography`) — a arquitetura não muda, só a primitiva.

Este módulo não decide QUANDO selar. Esse é o problema difícil, é político
antes de ser técnico, e está discutido em docs/testemunha.md.

Só biblioteca padrão.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import secrets
import sys
from datetime import datetime, timezone

# Primo de Mersenne 2^521-1: espaço grande o bastante para segredos de 256 bits
# com folga, e bem conhecido.
PRIMO = 2 ** 521 - 1


# ========================================================================
# 1. PARTILHA DE SEGREDO (Shamir) — o "ninguém sozinho"
# ========================================================================

def _avaliar(coeficientes: list[int], x: int) -> int:
    """Avalia o polinômio em x, por Horner, módulo PRIMO."""
    acc = 0
    for c in reversed(coeficientes):
        acc = (acc * x + c) % PRIMO
    return acc


def partir(segredo: int, k: int, n: int) -> list[tuple[int, int]]:
    """Parte `segredo` em n partes; k partes quaisquer o reconstroem.

    k-1 partes não revelam NADA sobre o segredo — não é "quase nada", é
    nada: qualquer segredo continua igualmente possível.
    """
    if not 2 <= k <= n:
        raise ValueError("é preciso 2 <= k <= n")
    if not 0 <= segredo < PRIMO:
        raise ValueError("segredo fora do corpo")

    coeficientes = [segredo] + [secrets.randbelow(PRIMO) for _ in range(k - 1)]
    return [(x, _avaliar(coeficientes, x)) for x in range(1, n + 1)]


def juntar(partes: list[tuple[int, int]]) -> int:
    """Reconstrói o segredo por interpolação de Lagrange em x=0."""
    if len(partes) < 2:
        raise ValueError("são necessárias ao menos 2 partes")
    if len({x for x, _ in partes}) != len(partes):
        raise ValueError("há partes repetidas")

    total = 0
    for i, (xi, yi) in enumerate(partes):
        num = den = 1
        for j, (xj, _) in enumerate(partes):
            if i == j:
                continue
            num = (num * -xj) % PRIMO
            den = (den * (xi - xj)) % PRIMO
        total = (total + yi * num * pow(den, -1, PRIMO)) % PRIMO
    return total


# ========================================================================
# 2. CIFRA AUTENTICADA — o conteúdo nunca em claro
# ========================================================================

def _derivar(mestra: bytes, uso: bytes) -> bytes:
    return hmac.new(mestra, uso, hashlib.sha256).digest()


def _fluxo(chave: bytes, nonce: bytes, tamanho: int) -> bytes:
    """Fluxo de chave: HMAC(chave, nonce || contador), blocos de 32 bytes."""
    saida = bytearray()
    contador = 0
    while len(saida) < tamanho:
        saida += hmac.new(chave, nonce + contador.to_bytes(8, "big"),
                          hashlib.sha256).digest()
        contador += 1
    return bytes(saida[:tamanho])


def cifrar(mestra: bytes, claro: bytes) -> dict:
    """Cifra e autentica. Retorna nonce, texto cifrado e etiqueta."""
    nonce = os.urandom(16)
    k_cifra = _derivar(mestra, b"cifra")
    k_etiq = _derivar(mestra, b"etiqueta")

    cifrado = bytes(a ^ b for a, b in zip(claro, _fluxo(k_cifra, nonce, len(claro))))
    etiqueta = hmac.new(k_etiq, nonce + cifrado, hashlib.sha256).digest()

    return {"nonce": nonce.hex(), "cifrado": cifrado.hex(),
            "etiqueta": etiqueta.hex()}


def decifrar(mestra: bytes, pacote: dict) -> bytes:
    """Decifra após conferir a etiqueta. Etiqueta errada = recusa."""
    nonce = bytes.fromhex(pacote["nonce"])
    cifrado = bytes.fromhex(pacote["cifrado"])
    k_cifra = _derivar(mestra, b"cifra")
    k_etiq = _derivar(mestra, b"etiqueta")

    esperada = hmac.new(k_etiq, nonce + cifrado, hashlib.sha256).digest()
    if not hmac.compare_digest(esperada, bytes.fromhex(pacote["etiqueta"])):
        raise ValueError("etiqueta inválida: o conteúdo foi alterado")

    return bytes(a ^ b for a, b in zip(cifrado, _fluxo(k_cifra, nonce, len(cifrado))))


# ========================================================================
# 3. CADEIA DE HASHES — existência sem revelação
# ========================================================================

GENESE = "0" * 64


def _hash_entrada(e: dict) -> str:
    corpo = {c: e[c] for c in
             ("indice", "instante", "hash_conteudo", "tamanho", "hash_anterior")}
    return hashlib.sha256(
        json.dumps(corpo, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def selar(cadeia: list[dict], conteudo: bytes, mestra: bytes,
          instante: str | None = None) -> dict:
    """Acrescenta um testemunho selado à cadeia.

    A entrada torna públicos: quando, que tamanho, e o hash do conteúdo.
    NÃO torna público: o conteúdo. Para isso é preciso reunir k partes.
    """
    anterior = cadeia[-1]["hash_entrada"] if cadeia else GENESE
    entrada = {
        "indice": len(cadeia),
        "instante": instante or datetime.now(timezone.utc).isoformat(),
        "hash_conteudo": hashlib.sha256(conteudo).hexdigest(),
        "tamanho": len(conteudo),
        "hash_anterior": anterior,
        "selo": cifrar(mestra, conteudo),
    }
    entrada["hash_entrada"] = _hash_entrada(entrada)
    cadeia.append(entrada)
    return entrada


def conferir_cadeia(cadeia: list[dict]) -> tuple[bool, str]:
    """Verifica a cadeia inteira SEM chave nenhuma.

    É esta função que qualquer terceiro — perito, juiz, a outra parte —
    executa para saber que nada foi inserido, removido ou reordenado.
    """
    anterior = GENESE
    for i, e in enumerate(cadeia):
        if e["indice"] != i:
            return False, f"entrada {i}: índice fora de ordem"
        if e["hash_anterior"] != anterior:
            return False, f"entrada {i}: elo quebrado com a anterior"
        if _hash_entrada(e) != e["hash_entrada"]:
            return False, f"entrada {i}: conteúdo do registro alterado"
        anterior = e["hash_entrada"]
    return True, f"cadeia íntegra: {len(cadeia)} entrada(s)"


def abrir(entrada: dict, partes: list[tuple[int, int]]) -> bytes:
    """Abre um testemunho reunindo as partes da chave."""
    mestra = juntar(partes).to_bytes(32, "big", signed=False)[-32:]
    claro = decifrar(mestra, entrada["selo"])
    if hashlib.sha256(claro).hexdigest() != entrada["hash_conteudo"]:
        raise ValueError("o conteúdo aberto não confere com o hash registrado")
    return claro


def nova_mestra() -> tuple[bytes, int]:
    """Gera uma chave mestra de 256 bits e seu valor inteiro."""
    b = os.urandom(32)
    return b, int.from_bytes(b, "big")


# ========================================================================
# 4. DEMONSTRAÇÃO
# ========================================================================

def demonstrar() -> int:
    print("=" * 70)
    print("TESTEMUNHA SELADA — demonstração")
    print("=" * 70)

    mestra, segredo = nova_mestra()
    k, n = 2, 3
    partes = partir(segredo, k, n)

    print(f"\nChave partida em {n} partes; {k} abrem.")
    print("  parte 1 -> tutor (a pessoa atendida)")
    print("  parte 2 -> profissional")
    print("  parte 3 -> guarda neutra (conselho, cartório, custódia)")

    cadeia: list[dict] = []
    for texto in (b"consulta iniciada 19:02, acompanhante presente",
                  b"consulta encerrada 19:41, sem intercorrencia"):
        e = selar(cadeia, texto, mestra)
        print(f"\nselado #{e['indice']}  {e['instante'][:19]}  "
              f"{e['tamanho']} B")
        print(f"  hash do conteudo  {e['hash_conteudo'][:48]}…")
        print(f"  hash da entrada   {e['hash_entrada'][:48]}…")

    print("\n" + "-" * 70)
    print("A) QUALQUER UM confere a cadeia, sem chave alguma:")
    ok, msg = conferir_cadeia(cadeia)
    print(f"   {'OK ' if ok else 'FALHA'} {msg}")

    print("\nB) Uma parte sozinha NÃO abre:")
    try:
        abrir(cadeia[0], partes[:1])
        print("   FALHA: abriu, e não deveria")
    except ValueError as err:
        print(f"   OK  recusado — {err}")

    print(f"\nC) {k} partes reunidas abrem:")
    print(f"   {abrir(cadeia[0], partes[:k]).decode()!r}")

    print("\nD) Adulterar o registro quebra a cadeia:")
    copia = [dict(x) for x in cadeia]
    copia[0] = dict(copia[0], tamanho=999)
    ok, msg = conferir_cadeia(copia)
    print(f"   {'FALHA' if ok else 'OK '} {msg}")

    print("\n" + "=" * 70)
    print("""O que está público e o que está fechado

  PÚBLICO   que existiu, quando, que tamanho, e que não foi alterado.
            Verificável por qualquer pessoa, sem chave nenhuma.

  FECHADO   o conteúdo. Só abre com k partes reunidas — ou seja, por
            acordo, nunca por decisão de um lado só.

Isso protege a pessoa atendida contra abuso e o profissional contra
acusação falsa, com a mesma operação. Nenhum dos dois dispara sozinho.""")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="Testemunho selado: ninguém na sala abre sozinho.")
    p.add_argument("--demo", action="store_true", default=True)
    p.parse_args()
    return demonstrar()


if __name__ == "__main__":
    sys.exit(main())
