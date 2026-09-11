#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de cuidado.py.

    python3 -m unittest discover -s tests -v
"""

import pathlib
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))

import cuidado as c  # noqa: E402
import testemunha as t  # noqa: E402

FIM = datetime(2026, 9, 11, tzinfo=timezone.utc)


class TestVocabulario(unittest.TestCase):
    def test_evento_fora_do_vocabulario_e_recusado(self):
        # Vocabulário fechado impede que o registro vire diário da vida.
        mestra, _ = t.nova_mestra()
        with self.assertRaises(ValueError):
            c.registrar([], mestra, "almocou_com_a_vizinha", FIM)

    def test_todo_evento_tem_descricao_e_gravidade(self):
        for tipo in c.EVENTOS:
            with self.subTest(tipo=tipo):
                self.assertTrue(c.descrever(tipo))
                self.assertIn(c.gravidade(tipo), (1, 2, 3))

    def test_queda_pesa_mais_que_porta_aberta(self):
        self.assertGreater(c.gravidade("queda"), c.gravidade("porta_aberta"))


class TestRegistro(unittest.TestCase):
    def test_evento_entra_na_cadeia_e_ela_segue_integra(self):
        mestra, _ = t.nova_mestra()
        cadeia = []
        c.registrar(cadeia, mestra, "queda", FIM)
        c.registrar(cadeia, mestra, "dose_perdida", FIM)
        ok, _ = t.conferir_cadeia(cadeia)
        self.assertTrue(ok)
        self.assertEqual(len(cadeia), 2)

    def test_evento_e_recuperado_com_a_chave(self):
        mestra, _ = t.nova_mestra()
        cadeia = []
        c.registrar(cadeia, mestra, "saida_noturna", FIM)
        instante, tipo = c.eventos_de(cadeia, mestra)[0]
        self.assertEqual(tipo, "saida_noturna")
        self.assertEqual(instante, FIM)

    def test_adulterar_o_registro_de_cuidado_e_detectavel(self):
        # Protege a pessoa contra internação por conveniência e o cuidador
        # contra acusação de negligência: ninguém reescreve depois.
        mestra, _ = t.nova_mestra()
        cadeia = []
        for _ in range(3):
            c.registrar(cadeia, mestra, "queda", FIM)
        cadeia[1] = dict(cadeia[1], instante="2020-01-01T00:00:00+00:00")
        self.assertFalse(t.conferir_cadeia(cadeia)[0])

    def test_o_tipo_nao_aparece_em_claro_na_entrada(self):
        mestra, _ = t.nova_mestra()
        cadeia = []
        c.registrar(cadeia, mestra, "desorientacao", FIM)
        self.assertNotIn("desorientacao", str(cadeia[0]))


class TestJanelas(unittest.TestCase):
    def test_agrupa_na_janela_certa(self):
        eventos = [(FIM - timedelta(days=5), "queda"),
                   (FIM - timedelta(days=40), "queda")]
        js = c.por_janela(eventos, FIM, dias=30, janelas=2)
        self.assertEqual(js[0]["n"], 1)   # a mais antiga
        self.assertEqual(js[1]["n"], 1)   # a mais recente

    def test_janelas_vem_da_mais_antiga_para_a_mais_recente(self):
        js = c.por_janela([], FIM, dias=30, janelas=3)
        self.assertLess(js[0]["fim"], js[-1]["fim"])

    def test_evento_fora_de_todas_as_janelas_e_ignorado(self):
        eventos = [(FIM - timedelta(days=500), "queda")]
        js = c.por_janela(eventos, FIM, dias=30, janelas=3)
        self.assertEqual(sum(j["n"] for j in js), 0)

    def test_peso_soma_gravidades_e_nao_conta_eventos(self):
        eventos = [(FIM - timedelta(days=1), "queda")]          # gravidade 3
        js = c.por_janela(eventos, FIM, dias=30, janelas=1)
        self.assertEqual(js[0]["n"], 1)
        self.assertEqual(js[0]["peso"], 3)


class TestInclinacao(unittest.TestCase):
    def test_serie_constante_tem_inclinacao_zero(self):
        self.assertAlmostEqual(c.inclinacao([4, 4, 4, 4]), 0.0)

    def test_serie_crescente_tem_inclinacao_positiva(self):
        self.assertGreater(c.inclinacao([1, 2, 3, 4]), 0)

    def test_serie_decrescente_tem_inclinacao_negativa(self):
        self.assertLess(c.inclinacao([4, 3, 2, 1]), 0)

    def test_inclinacao_de_um_ponto_e_zero(self):
        self.assertEqual(c.inclinacao([7]), 0.0)

    def test_inclinacao_de_lista_vazia_e_zero(self):
        self.assertEqual(c.inclinacao([]), 0.0)

    def test_valor_da_inclinacao_e_o_passo_da_serie(self):
        self.assertAlmostEqual(c.inclinacao([0, 2, 4, 6]), 2.0)


class TestTrajetoria(unittest.TestCase):
    def _janelas(self, pesos):
        return [{"inicio": FIM, "fim": FIM, "n": p, "peso": p, "tipos": []}
                for p in pesos]

    def test_rampa_e_detectada(self):
        a = c.avaliar_trajetoria(self._janelas([1, 3, 4, 5, 9, 13]))
        self.assertGreater(a["inclinacao"], 1.0)
        self.assertGreater(a["variacao"], 2)

    def test_estabilidade_nao_e_confundida_com_rampa(self):
        a = c.avaliar_trajetoria(self._janelas([5, 5, 5, 5, 5, 5]))
        self.assertAlmostEqual(a["inclinacao"], 0.0)
        self.assertAlmostEqual(a["variacao"], 0.0)

    def test_melhora_da_inclinacao_negativa(self):
        a = c.avaliar_trajetoria(self._janelas([12, 9, 7, 4, 2, 1]))
        self.assertLess(a["inclinacao"], 0)

    def test_um_episodio_isolado_nao_vira_rampa(self):
        # O ponto central: uma queda não decide nada.
        a = c.avaliar_trajetoria(self._janelas([0, 0, 0, 9, 0, 0]))
        self.assertLess(a["inclinacao"], 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
