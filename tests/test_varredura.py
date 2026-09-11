#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de varredura.py — o round-trip byte a byte que o adendo ao R45 exige
antes de qualquer reivindicação.

    python3 -m unittest discover -s tests -v
"""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))

import varredura as v  # noqa: E402


FORMATOS = [(1, 1), (1, 8), (8, 1), (2, 3), (3, 2), (4, 4), (5, 7), (32, 32)]


class TestOrdensSaoPermutacoes(unittest.TestCase):
    """Toda ordem precisa visitar cada coordenada exatamente uma vez."""

    def test_todas_as_ordens_em_todos_os_formatos(self):
        for nome, fn in v.ORDENS.items():
            for h, w in FORMATOS:
                with self.subTest(ordem=nome, formato=(h, w)):
                    ordem = fn(h, w)
                    self.assertEqual(len(ordem), h * w)
                    self.assertEqual(len(set(ordem)), h * w,
                                     "há coordenada repetida")
                    self.assertTrue(v.e_permutacao(ordem, h, w))


class TestRoundTrip(unittest.TestCase):
    """Ler e reconstruir precisa devolver a matriz idêntica."""

    def _matriz(self, h, w):
        return [[(i * w + j) % 256 for j in range(w)] for i in range(h)]

    def test_round_trip_exato_em_todas_as_ordens(self):
        for nome, fn in v.ORDENS.items():
            for h, w in FORMATOS:
                with self.subTest(ordem=nome, formato=(h, w)):
                    m = self._matriz(h, w)
                    self.assertTrue(v.round_trip_ok(m, fn(h, w)))

    def test_round_trip_nos_conjuntos_de_teste(self):
        for nome_conj, gerar in v.CONJUNTOS.items():
            m = gerar(16, 16)
            for nome, fn in v.ORDENS.items():
                with self.subTest(conjunto=nome_conj, ordem=nome):
                    self.assertTrue(v.round_trip_ok(m, fn(16, 16)))

    def test_reconstrucao_e_identica_e_nao_apenas_equivalente(self):
        m = v.foto_sintetica(9, 11)
        ordem = v.ordem_boustrofedon(9, 11)
        refeita = v.desvarrer(v.varrer(m, ordem), ordem, 9, 11)
        for i in range(9):
            for j in range(11):
                self.assertEqual(m[i][j], refeita[i][j], f"divergiu em ({i},{j})")


class TestBoustrofedon(unittest.TestCase):
    def test_linha_par_vai_para_a_direita(self):
        ordem = v.ordem_boustrofedon(2, 4)
        self.assertEqual(ordem[:4], [(0, 0), (0, 1), (0, 2), (0, 3)])

    def test_linha_impar_volta_para_a_esquerda(self):
        ordem = v.ordem_boustrofedon(2, 4)
        self.assertEqual(ordem[4:], [(1, 3), (1, 2), (1, 1), (1, 0)])

    def test_emenda_entre_linhas_e_adjacente(self):
        # A razão de existir do boustrofédon: o fim de uma linha e o começo
        # da seguinte ficam na mesma coluna, não em extremos opostos.
        ordem = v.ordem_boustrofedon(2, 4)
        self.assertEqual(ordem[3][1], ordem[4][1])

    def test_reto_tem_emenda_distante(self):
        ordem = v.ordem_reta(2, 4)
        self.assertNotEqual(ordem[3][1], ordem[4][1])


class TestBoustrofedonAninhado(unittest.TestCase):
    def test_troca_a_cada_duas_linhas(self):
        # Padrão do adendo: D→E, D→E, E→D, E→D
        ordem = v.ordem_boustrofedon_aninhado(4, 3, bloco=2)
        linhas = [ordem[i * 3:(i + 1) * 3] for i in range(4)]
        self.assertEqual([c for _, c in linhas[0]], [0, 1, 2])
        self.assertEqual([c for _, c in linhas[1]], [0, 1, 2])
        self.assertEqual([c for _, c in linhas[2]], [2, 1, 0])
        self.assertEqual([c for _, c in linhas[3]], [2, 1, 0])

    def test_com_bloco_1_vira_boustrofedon_simples(self):
        self.assertEqual(v.ordem_boustrofedon_aninhado(6, 5, bloco=1),
                         v.ordem_boustrofedon(6, 5))


class TestResiduos(unittest.TestCase):
    def test_diferenca_de_um_passo(self):
        self.assertEqual(v.residuos([10, 12, 15], 1), [2, 3])

    def test_deslocamento_maior(self):
        self.assertEqual(v.residuos([1, 2, 3, 10], 3), [9])

    def test_deslocamento_zero_e_recusado(self):
        with self.assertRaises(ValueError):
            v.residuos([1, 2, 3], 0)

    def test_round_trip_dos_residuos(self):
        seq = v.varrer(v.foto_sintetica(8, 8), v.ordem_reta(8, 8))
        for d in (1, 2, 8, 12):
            with self.subTest(d=d):
                refeita = v.reconstruir_de_residuos(
                    seq[:d], v.residuos(seq, d), d)
                self.assertEqual(refeita, seq)


class TestMetricas(unittest.TestCase):
    def test_entropia_de_sequencia_constante_e_zero(self):
        self.assertEqual(v.entropia([7] * 100), 0.0)

    def test_entropia_de_dois_simbolos_equiprovaveis_e_um_bit(self):
        self.assertAlmostEqual(v.entropia([0, 1] * 50), 1.0)

    def test_entropia_de_lista_vazia(self):
        self.assertEqual(v.entropia([]), 0.0)

    def test_delta_medio_de_sequencia_constante_e_zero(self):
        self.assertEqual(v.delta_medio([5, 5, 5, 5]), 0.0)

    def test_delta_medio_de_um_elemento(self):
        self.assertEqual(v.delta_medio([5]), 0.0)

    def test_bytes_comprimidos_lida_com_negativos(self):
        # Resíduos são negativos com frequência; o empacotamento precisa
        # aceitá-los sem estourar.
        self.assertGreater(v.bytes_comprimidos([-5, 3, -200, 128]), 0)


class TestAchadosDoExperimento(unittest.TestCase):
    """Trava os resultados que sustentam as conclusões, para que uma mudança
    futura no código não os altere em silêncio."""

    def test_aninhado_nunca_supera_o_boustrofedon_simples(self):
        # Conclusão: o padrão aninhado é decorativo.
        for gerar in (v.gradiente, v.foto_sintetica):
            m = gerar(32, 32)
            simples = v.avaliar(m, "boustrofedon")["bytes_d1"]
            aninhado = v.avaliar(m, "boustrofedon_aninhado")["bytes_d1"]
            with self.subTest(conjunto=gerar.__name__):
                self.assertGreaterEqual(aninhado, simples)

    def test_boustrofedon_piora_em_dado_regular(self):
        # Em gradiente, o modo reto gera delta constante (entropia baixa);
        # o boustrofédon alterna o sinal e destrói essa regularidade.
        m = v.gradiente(32, 32)
        self.assertLess(v.avaliar(m, "reto")["entropia_d1"],
                        v.avaliar(m, "boustrofedon")["entropia_d1"])

    def test_melhor_deslocamento_em_imagem_e_a_largura(self):
        # O achado principal: d = largura vence, e -12 nunca o alcançaria.
        r = v.avaliar(v.foto_sintetica(32, 32), "reto")
        self.assertEqual(r["melhor_deslocamento"], 32)
        self.assertLess(r["bytes_melhor"], r["bytes_d1"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
