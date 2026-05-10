import os
import sys
import unittest
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routes.relatorios import calcular_primeira_fatura


class TestCalculoFaturaCartao(unittest.TestCase):
    def test_fechamento_menor_que_vencimento(self):
        self.assertEqual(
            calcular_primeira_fatura(date(2026, 1, 5), 5, 10),
            date(2026, 1, 1),
        )
        self.assertEqual(
            calcular_primeira_fatura(date(2026, 1, 6), 5, 10),
            date(2026, 2, 1),
        )

    def test_fechamento_maior_que_vencimento(self):
        self.assertEqual(
            calcular_primeira_fatura(date(2026, 1, 28), 28, 10),
            date(2026, 2, 1),
        )
        self.assertEqual(
            calcular_primeira_fatura(date(2026, 1, 29), 28, 10),
            date(2026, 3, 1),
        )


if __name__ == '__main__':
    unittest.main()
