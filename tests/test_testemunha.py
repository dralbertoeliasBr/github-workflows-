#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de testemunha.py.

O que está sendo testado não é conveniência — são as três promessas que
tornam o desenho defensável:

  1. Ninguém abre sozinho.       (partilha com limiar)
  2. Adulterar é detectável.     (cadeia de hashes + etiqueta)
  3. Conferir não exige chave.   (existência sem revelação)

    python3 -m unittest discover -s tests -v
"""

import itertools
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))

import testemunha as t  # noqa: E402


class TestPartilha(unittest.TestCase):
    def test_k_partes_reconstroem(self):
        segredo = 123456789012345678901234567890
        for k, n in [(2, 3), (3, 5), (5, 5), (2, 2), (4, 7)]:
            with self.subTest(k=k, n=n):
                partes = t.partir(segredo, k, n)
                self.assertEqual(t.juntar(partes[:k]), segredo)

    def test_qualquer_combinacao_de_k_partes_serve(self):
        # Não pode haver parte "privilegiada": todas valem o mesmo.
        segredo = 987654321
        partes = t.partir(segredo, 3, 5)
        for combo in itertools.combinations(partes, 3):
            self.assertEqual(t.juntar(list(combo)), segredo)

    def test_mais_que_k_partes_tambem_reconstroem(self):
        segredo = 42
        partes = t.partir(segredo, 2, 5)
        self.assertEqual(t.juntar(partes), segredo)

    def test_k_menos_uma_parte_nao_revela_o_segredo(self):
        """A promessa central: k-1 partes não dão o segredo.

        Não é "dá um valor aproximado" — dá um valor sem relação com o
        original, e por isso nada se aprende.
        """
        segredo = 314159265358979323846
        partes = t.partir(segredo, 3, 5)
        for combo in itertools.combinations(partes, 2):
            self.assertNotEqual(t.juntar(list(combo)), segredo)

    def test_partes_repetidas_sao_recusadas(self):
        partes = t.partir(7, 2, 3)
        with self.assertRaises(ValueError):
            t.juntar([partes[0], partes[0]])

    def test_uma_parte_so_e_recusada(self):
        with self.assertRaises(ValueError):
            t.juntar(t.partir(7, 2, 3)[:1])

    def test_limiar_invalido(self):
        for k, n in [(1, 3), (0, 3), (4, 3), (3, 2)]:
            with self.subTest(k=k, n=n), self.assertRaises(ValueError):
                t.partir(7, k, n)

    def test_segredo_fora_do_corpo(self):
        with self.assertRaises(ValueError):
            t.partir(t.PRIMO, 2, 3)


class TestCifra(unittest.TestCase):
    def test_round_trip(self):
        m, _ = t.nova_mestra()
        for claro in [b"", b"a", b"x" * 31, b"y" * 32, b"z" * 33, b"n" * 5000]:
            with self.subTest(tamanho=len(claro)):
                self.assertEqual(t.decifrar(m, t.cifrar(m, claro)), claro)

    def test_texto_cifrado_nao_contem_o_claro(self):
        m, _ = t.nova_mestra()
        claro = b"acompanhante presente na sala"
        self.assertNotIn(claro.hex(), t.cifrar(m, claro)["cifrado"])

    def test_nonce_diferente_a_cada_chamada(self):
        m, _ = t.nova_mestra()
        a, b = t.cifrar(m, b"igual"), t.cifrar(m, b"igual")
        self.assertNotEqual(a["nonce"], b["nonce"])
        self.assertNotEqual(a["cifrado"], b["cifrado"])

    def test_etiqueta_adulterada_e_recusada(self):
        m, _ = t.nova_mestra()
        p = t.cifrar(m, b"conteudo")
        p["etiqueta"] = "00" * 32
        with self.assertRaises(ValueError):
            t.decifrar(m, p)

    def test_texto_cifrado_adulterado_e_recusado(self):
        m, _ = t.nova_mestra()
        p = t.cifrar(m, b"conteudo original")
        crus = bytearray(bytes.fromhex(p["cifrado"]))
        crus[0] ^= 0xFF
        p["cifrado"] = crus.hex()
        with self.assertRaises(ValueError):
            t.decifrar(m, p)

    def test_chave_errada_e_recusada(self):
        m1, _ = t.nova_mestra()
        m2, _ = t.nova_mestra()
        with self.assertRaises(ValueError):
            t.decifrar(m2, t.cifrar(m1, b"conteudo"))


class TestCadeia(unittest.TestCase):
    def _cadeia(self, quantas=4):
        m, _ = t.nova_mestra()
        c: list[dict] = []
        for i in range(quantas):
            t.selar(c, f"testemunho {i}".encode(), m)
        return c, m

    def test_cadeia_nova_e_integra(self):
        c, _ = self._cadeia()
        ok, _ = t.conferir_cadeia(c)
        self.assertTrue(ok)

    def test_cadeia_vazia_e_integra(self):
        ok, _ = t.conferir_cadeia([])
        self.assertTrue(ok)

    def test_conferir_nao_precisa_de_chave(self):
        # A verificação é feita por terceiro que não tem nada.
        c, _ = self._cadeia()
        ok, msg = t.conferir_cadeia([dict(e) for e in c])
        self.assertTrue(ok)
        self.assertIn("íntegra", msg)

    def test_primeira_entrada_aponta_para_a_genese(self):
        c, _ = self._cadeia(1)
        self.assertEqual(c[0]["hash_anterior"], t.GENESE)

    def test_cada_entrada_aponta_para_a_anterior(self):
        c, _ = self._cadeia()
        for i in range(1, len(c)):
            self.assertEqual(c[i]["hash_anterior"], c[i - 1]["hash_entrada"])

    def test_alterar_qualquer_campo_quebra_a_cadeia(self):
        for campo, valor in [("tamanho", 999), ("instante", "2020-01-01T00:00:00"),
                             ("hash_conteudo", "00" * 32)]:
            for pos in range(4):
                with self.subTest(campo=campo, posicao=pos):
                    c, _ = self._cadeia()
                    c[pos] = dict(c[pos], **{campo: valor})
                    ok, _ = t.conferir_cadeia(c)
                    self.assertFalse(ok)

    def test_remover_entrada_do_meio_quebra_a_cadeia(self):
        c, _ = self._cadeia()
        del c[1]
        self.assertFalse(t.conferir_cadeia(c)[0])

    def test_reordenar_quebra_a_cadeia(self):
        c, _ = self._cadeia()
        c[1], c[2] = c[2], c[1]
        self.assertFalse(t.conferir_cadeia(c)[0])

    def test_inserir_entrada_forjada_quebra_a_cadeia(self):
        c, m = self._cadeia()
        forjada = dict(c[-1], indice=2)
        c.insert(2, forjada)
        self.assertFalse(t.conferir_cadeia(c)[0])


class TestAbertura(unittest.TestCase):
    def test_k_partes_abrem_o_testemunho(self):
        m, segredo = t.nova_mestra()
        partes = t.partir(segredo, 2, 3)
        c: list[dict] = []
        t.selar(c, b"consulta encerrada sem intercorrencia", m)
        self.assertEqual(t.abrir(c[0], partes[:2]),
                         b"consulta encerrada sem intercorrencia")

    def test_uma_parte_nao_abre(self):
        m, segredo = t.nova_mestra()
        partes = t.partir(segredo, 2, 3)
        c: list[dict] = []
        t.selar(c, b"conteudo", m)
        with self.assertRaises(ValueError):
            t.abrir(c[0], partes[:1])

    def test_partes_de_outro_segredo_nao_abrem(self):
        m, _ = t.nova_mestra()
        _, outro = t.nova_mestra()
        alheias = t.partir(outro, 2, 3)
        c: list[dict] = []
        t.selar(c, b"conteudo", m)
        with self.assertRaises(ValueError):
            t.abrir(c[0], alheias[:2])

    def test_conteudo_aberto_confere_com_o_hash_publicado(self):
        m, segredo = t.nova_mestra()
        partes = t.partir(segredo, 3, 5)
        c: list[dict] = []
        dados = b"registro longo " * 200
        t.selar(c, dados, m)
        aberto = t.abrir(c[0], partes[:3])
        import hashlib
        self.assertEqual(hashlib.sha256(aberto).hexdigest(), c[0]["hash_conteudo"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
