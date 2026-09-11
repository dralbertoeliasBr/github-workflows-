#!/usr/bin/env python3
"""
Testes do drive_socorro. Só biblioteca padrão.

    python3 -m unittest discover -s tests -v

Cobrem a lógica pura (montagem de consulta, escape, formatação, classificação
de erro) e a paginação, com a chamada de rede substituída por um dublê. Não
tocam na API real nem exigem credencial.
"""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))

import drive_socorro as ds  # noqa: E402


class TestEscapar(unittest.TestCase):
    def test_aspas_simples_sao_escapadas(self):
        # Sem isto, um nome com apóstrofo quebra a sintaxe da busca do Drive
        # e pode alterar o sentido da consulta.
        self.assertEqual(ds.escapar("d'Angelo"), r"d\'Angelo")

    def test_barra_invertida_escapada_antes_das_aspas(self):
        self.assertEqual(ds.escapar(r"a\b"), r"a\\b")

    def test_texto_simples_nao_muda(self):
        self.assertEqual(ds.escapar("raio-x 2024"), "raio-x 2024")


class TestMontarConsulta(unittest.TestCase):
    def test_lixeira(self):
        self.assertEqual(ds.montar_consulta(lixeira=True), "trashed = true")

    def test_lixeira_falsa(self):
        self.assertEqual(ds.montar_consulta(lixeira=False), "trashed = false")

    def test_midia_cobre_imagem_e_video(self):
        q = ds.montar_consulta(lixeira=True, midia=True)
        self.assertIn("mimeType contains 'image/'", q)
        self.assertIn("mimeType contains 'video/'", q)
        self.assertIn(" or ", q)

    def test_ano_vira_intervalo_fechado_a_esquerda(self):
        q = ds.montar_consulta(ano=2024)
        self.assertIn("createdTime >= '2024-01-01T00:00:00'", q)
        self.assertIn("createdTime < '2025-01-01T00:00:00'", q)

    def test_ano_nao_vaza_para_o_ano_seguinte(self):
        # 31/12/2024 entra; 01/01/2025 não.
        self.assertNotIn("2025-12", ds.montar_consulta(ano=2024))

    def test_nome_e_escapado(self):
        q = ds.montar_consulta(nome="d'Angelo")
        self.assertIn(r"name contains 'd\'Angelo'", q)

    def test_publico(self):
        self.assertEqual(ds.montar_consulta(publico=True),
                         "visibility = 'anyoneWithLink'")

    def test_filtros_combinam_com_and(self):
        q = ds.montar_consulta(lixeira=True, midia=True, ano=2024)
        self.assertEqual(q.count(" and "), 3)

    def test_sem_filtro_nao_devolve_consulta_vazia(self):
        # Consulta vazia listaria o Drive inteiro por engano.
        self.assertEqual(ds.montar_consulta(), "trashed = false")


class TestHumano(unittest.TestCase):
    def test_bytes(self):
        self.assertEqual(ds.humano(512), "512B")

    def test_kilobytes(self):
        self.assertEqual(ds.humano(2048), "2KB")

    def test_gigabytes(self):
        self.assertEqual(ds.humano(92 * 1024 ** 3), "92GB")

    def test_none_e_traco(self):
        self.assertEqual(ds.humano(None), "-")

    def test_texto_invalido_e_traco(self):
        self.assertEqual(ds.humano(""), "-")


class TestMarca(unittest.TestCase):
    def test_pasta(self):
        self.assertEqual(
            ds.marca({"mimeType": "application/vnd.google-apps.folder"}), "PA")

    def test_imagem(self):
        self.assertEqual(ds.marca({"mimeType": "image/jpeg"}), "IM")

    def test_video(self):
        self.assertEqual(ds.marca({"mimeType": "video/mp4"}), "VD")

    def test_pdf(self):
        self.assertEqual(ds.marca({"mimeType": "application/pdf"}), "PD")

    def test_desconhecido(self):
        self.assertEqual(ds.marca({}), "  ")


class TestData(unittest.TestCase):
    def test_corta_no_dia(self):
        self.assertEqual(ds.data({"createdTime": "2024-03-18T21:04:11.123Z"}),
                         "2024-03-18")

    def test_ausente_vira_traco(self):
        self.assertEqual(ds.data({}), "-")

    def test_campo_alternativo(self):
        self.assertEqual(
            ds.data({"modifiedTime": "2026-09-10T23:12:00Z"}, "modifiedTime"),
            "2026-09-10")


class TestTotalBytes(unittest.TestCase):
    def test_soma(self):
        self.assertEqual(ds.total_bytes([{"size": "100"}, {"size": "23"}]), 123)

    def test_ignora_item_sem_tamanho(self):
        # Pastas e documentos do Google não trazem "size".
        self.assertEqual(ds.total_bytes([{"size": "100"}, {}]), 100)


class TestClassificacaoDeErro(unittest.TestCase):
    def test_429_e_transitorio(self):
        self.assertTrue(ds._e_limite(429, {}))

    def test_503_e_transitorio(self):
        self.assertTrue(ds._e_limite(503, {}))

    def test_403_por_cota_e_transitorio(self):
        corpo = {"error": {"errors": [{"reason": "rateLimitExceeded"}]}}
        self.assertTrue(ds._e_limite(403, corpo))

    def test_403_por_permissao_nao_e_transitorio(self):
        # Este não pode ser repetido: repetir não resolve e mascara o problema.
        corpo = {"error": {"errors": [{"reason": "insufficientPermissions"}]}}
        self.assertFalse(ds._e_limite(403, corpo))

    def test_404_nao_e_transitorio(self):
        self.assertFalse(ds._e_limite(404, {}))


class TestPaginacao(unittest.TestCase):
    """A falha que motivou a reescrita: perder itens além da primeira página."""

    def setUp(self):
        self.original = ds.requisitar
        self.chamadas = []

    def tearDown(self):
        ds.requisitar = self.original

    def _dublar(self, paginas):
        def falso(token, caminho, metodo="GET", corpo=None, params=None):
            self.chamadas.append(params.get("pageToken"))
            return paginas[len(self.chamadas) - 1]
        ds.requisitar = falso

    def test_junta_todas_as_paginas(self):
        self._dublar([
            {"files": [{"id": "1"}, {"id": "2"}], "nextPageToken": "p2"},
            {"files": [{"id": "3"}], "nextPageToken": "p3"},
            {"files": [{"id": "4"}]},
        ])
        itens = ds.listar("tok", "trashed = true")
        self.assertEqual([i["id"] for i in itens], ["1", "2", "3", "4"])

    def test_encaminha_o_token_de_cada_pagina(self):
        self._dublar([
            {"files": [], "nextPageToken": "p2"},
            {"files": []},
        ])
        ds.listar("tok", "q")
        self.assertEqual(self.chamadas, [None, "p2"])

    def test_pagina_unica(self):
        self._dublar([{"files": [{"id": "1"}]}])
        self.assertEqual(len(ds.listar("tok", "q")), 1)

    def test_resposta_vazia(self):
        self._dublar([{}])
        self.assertEqual(ds.listar("tok", "q"), [])

    def test_nome_com_quebra_de_linha_sobrevive(self):
        # O TSV da versão em bash quebrava aqui.
        self._dublar([{"files": [{"id": "1", "name": "foto\nfamilia.jpg"}]}])
        self.assertEqual(ds.listar("tok", "q")[0]["name"], "foto\nfamilia.jpg")


if __name__ == "__main__":
    unittest.main(verbosity=2)
