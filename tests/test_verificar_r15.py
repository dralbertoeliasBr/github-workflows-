#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes da verificação do R15 — travam os números para que a conclusão
não mude em silêncio."""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))

import verificar_r15 as r  # noqa: E402


class TestDados(unittest.TestCase):
    def test_cinco_nos(self):
        self.assertEqual(len(r.NOS), 5)

    def test_soma_total_e_primo(self):
        total = sum(r.NOS.values())
        self.assertEqual(total, 167)
        self.assertTrue(all(total % d for d in range(2, 13)))


class TestEquacoes(unittest.TestCase):
    def test_formula_nao_fecha(self):
        # A falha declarada pelo documento é real.
        obtidos = {v + 13 for v in r.NOS.values()}
        self.assertEqual(obtidos & set(r.NOS.values()), set())

    def test_oito_e_resto_de_trinta_mod_onze(self):
        self.assertEqual(30 % 11, 8)

    def test_resto_oito_e_impossivel_nos_primos_menores(self):
        # O ponto que o documento não explicita: resto < divisor.
        for p in (2, 3, 5, 7):
            for v in r.NOS.values():
                self.assertNotEqual(v % p, 8)

    def test_ocorrencia_unica_sob_mod_onze(self):
        self.assertEqual(sum(1 for v in r.NOS.values() if v % 11 == 8), 1)

    def test_fibonacci_cinco_e_oito_consecutivos(self):
        fib = [1, 1]
        while len(fib) < 8:
            fib.append(fib[-1] + fib[-2])
        self.assertEqual(fib.index(8), fib.index(5) + 1)


class TestCorrecaoDoAcaso(unittest.TestCase):
    """A correção 4-bis: comparações múltiplas."""

    def test_probabilidade_ingenua_do_documento(self):
        candidatos = [n for n in range(101) if n % 11 == 8]
        self.assertEqual(len(candidatos), 9)
        self.assertAlmostEqual(len(candidatos) / 101, 0.0891, places=3)

    def test_probabilidade_corrigida_e_muito_maior(self):
        p = 1 - (10 / 11) ** 5
        self.assertAlmostEqual(p, 0.379, places=2)
        self.assertGreater(p, 4 * 0.0891)

    def test_a_correcao_enfraquece_a_pista(self):
        # Acima de ~1/3 de chance ao acaso, não é pista — é ruído.
        self.assertGreater(1 - (10 / 11) ** 5, 1 / 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
