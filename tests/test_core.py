import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from decimal import Decimal
from pathlib import Path

from gastos import core
from gastos.cli import main
from gastos.core import GastosError, Repositorio


class TestParseValor(unittest.TestCase):
    def test_aceita_virgula_e_ponto(self):
        self.assertEqual(core.parse_valor("12,50"), Decimal("12.50"))
        self.assertEqual(core.parse_valor("12.5"), Decimal("12.50"))

    def test_arredonda_para_duas_casas(self):
        self.assertEqual(core.parse_valor("10"), Decimal("10.00"))

    def test_rejeita_valores_invalidos(self):
        for entrada in ["abc", "", "0", "-5", "NaN", "Infinity"]:
            with self.subTest(entrada=entrada):
                with self.assertRaises(GastosError):
                    core.parse_valor(entrada)


class TestFormatarBrl(unittest.TestCase):
    def test_formata_milhar_e_centavos(self):
        self.assertEqual(core.formatar_brl(Decimal("1234.5")), "R$ 1.234,50")

    def test_zero(self):
        self.assertEqual(core.formatar_brl(Decimal("0")), "R$ 0,00")


class TestOperacoes(unittest.TestCase):
    def setUp(self):
        self.despesas = []
        core.adicionar(self.despesas, "Almoço", "30", "Comida", date(2026, 10, 5))
        core.adicionar(self.despesas, "Ônibus", "4,50", "transporte", date(2026, 11, 2))
        core.adicionar(self.despesas, "Jantar", "50", "comida", date(2026, 11, 10))

    def test_ids_sequenciais_e_categoria_normalizada(self):
        self.assertEqual([d.id for d in self.despesas], [1, 2, 3])
        self.assertEqual(self.despesas[0].categoria, "comida")

    def test_descricao_vazia_e_rejeitada(self):
        with self.assertRaises(GastosError):
            core.adicionar(self.despesas, "   ", "10")

    def test_remover_existente_e_inexistente(self):
        removida = core.remover(self.despesas, 2)
        self.assertEqual(removida.descricao, "Ônibus")
        self.assertEqual(len(self.despesas), 2)
        with self.assertRaises(GastosError):
            core.remover(self.despesas, 99)

    def test_novo_id_e_sempre_maior_que_o_maior_existente(self):
        core.remover(self.despesas, 1)
        nova = core.adicionar(self.despesas, "Café", "8")
        self.assertEqual(nova.id, 4)

    def test_filtrar(self):
        self.assertEqual(len(core.filtrar(self.despesas, categoria="COMIDA")), 2)
        self.assertEqual(len(core.filtrar(self.despesas, ano=2026, mes=11)), 2)
        self.assertEqual(len(core.filtrar(self.despesas, mes=10)), 1)

    def test_filtrar_rejeita_mes_invalido(self):
        with self.assertRaises(GastosError):
            core.filtrar(self.despesas, mes=13)

    def test_total_e_resumo(self):
        self.assertEqual(core.total(self.despesas), Decimal("84.50"))
        resumo = core.resumo_por_categoria(self.despesas)
        self.assertEqual(list(resumo), ["comida", "transporte"])
        self.assertEqual(resumo["comida"], Decimal("80.00"))


class TestRepositorio(unittest.TestCase):
    def test_salvar_e_carregar(self):
        with tempfile.TemporaryDirectory() as pasta:
            repo = Repositorio(Path(pasta) / "dados" / "gastos.json")
            despesas = []
            core.adicionar(despesas, "Café", "7,25", "comida", date(2026, 1, 15))
            repo.salvar(despesas)
            carregadas = repo.carregar()
            self.assertEqual(carregadas, despesas)

    def test_arquivo_inexistente_retorna_lista_vazia(self):
        with tempfile.TemporaryDirectory() as pasta:
            self.assertEqual(Repositorio(Path(pasta) / "nao_existe.json").carregar(), [])

    def test_arquivo_corrompido(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "ruim.json"
            caminho.write_text("{ isso não é json", encoding="utf-8")
            with self.assertRaises(GastosError):
                Repositorio(caminho).carregar()


class TestCli(unittest.TestCase):
    def executar(self, *argv):
        saida, erro = io.StringIO(), io.StringIO()
        with redirect_stdout(saida), redirect_stderr(erro):
            codigo = main(list(argv))
        return codigo, saida.getvalue(), erro.getvalue()

    def test_fluxo_completo(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = str(Path(pasta) / "gastos.json")
            base = ["--arquivo", arquivo]

            codigo, saida, _ = self.executar(*base, "add", "Almoço", "25,90", "-c", "comida", "-d", "2026-11-10")
            self.assertEqual(codigo, 0)
            self.assertIn("#1", saida)

            self.executar(*base, "add", "Metrô", "5", "-c", "transporte", "-d", "2026-11-11")

            codigo, saida, _ = self.executar(*base, "list")
            self.assertEqual(codigo, 0)
            self.assertIn("Almoço", saida)
            self.assertIn("R$ 30,90", saida)

            codigo, saida, _ = self.executar(*base, "summary", "--mes", "11")
            self.assertIn("comida", saida)
            self.assertIn("%", saida)

            codigo, saida, _ = self.executar(*base, "remove", "1")
            self.assertEqual(codigo, 0)

            _, saida, _ = self.executar(*base, "list")
            self.assertNotIn("Almoço", saida)

    def test_erro_retorna_codigo_1(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = str(Path(pasta) / "gastos.json")
            codigo, _, erro = self.executar("--arquivo", arquivo, "remove", "42")
            self.assertEqual(codigo, 1)
            self.assertIn("não encontrada", erro)


if __name__ == "__main__":
    unittest.main()
