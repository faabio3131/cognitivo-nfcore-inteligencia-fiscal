"""Regressões do pacote COG-1: sem emissão, defaults fiscais ou classificação inventada."""

from __future__ import annotations

import unittest
from decimal import Decimal

from kordena_fiscal.cognitive.cross_tax_matrix import review_cross_tax_dimensions
from kordena_fiscal.connectors.erp_pme import ConnectorValidationError, normalize_erp_order


class Cog1EvolucaoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bling = {
            "data": {
                "id": "19827364",
                "contato": {
                    "nome": "Cliente Sintético",
                    "numeroDocumento": "12345678000190",
                    "endereco": {"uf": "SP"},
                },
                "itens": [
                    {
                        "codigo": "SKU-001",
                        "descricao": "Monitor",
                        "ncm": "85285200",
                        "cfop": "5102",
                        "quantidade": "2",
                        "valor": "1200.00",
                    }
                ],
                "transporte": {"frete": "50.00"},
                "desconto": {"valor": "100.00"},
            }
        }

    def test_bling_value_and_advisory_only(self) -> None:
        result = normalize_erp_order(self.bling, platform="BLING_V3")
        self.assertEqual(result["items"][0]["vProd"], Decimal("2400.00"))
        self.assertEqual(result["totals"]["vFrete"], Decimal("50.00"))
        self.assertFalse(result["authoritative"])
        self.assertTrue(result["fiscal_review_required"])

    def test_formatted_cnpj_accepted_without_implicit_identity(self) -> None:
        payload = {
            "data": {
                **self.bling["data"],
                "contato": {
                    **self.bling["data"]["contato"],
                    "numeroDocumento": "12.345.678/0001-90",
                },
            }
        }
        result = normalize_erp_order(payload, platform="BLING_V3")
        self.assertEqual(result["customer"]["document"], "12345678000190")
        self.assertFalse(result["authoritative"])

    def test_tiny_value_and_advisory_only(self) -> None:
        result = normalize_erp_order(
            {
                "pedido": {
                    "id": "887766",
                    "cliente": {
                        "nome": "Empresa Sintética",
                        "cpf_cnpj": "98765432000110",
                        "uf": "MG",
                    },
                    "itens": [
                        {
                            "item": {
                                "codigo": "BEB-099",
                                "descricao": "Suco",
                                "ncm": "20097900",
                                "cfop": "6102",
                                "quantidade": "10",
                                "valor_unitario": "15.50",
                            }
                        }
                    ],
                }
            },
            platform="TINY_ERP",
        )
        self.assertEqual(result["items"][0]["vProd"], Decimal("155.00"))
        self.assertFalse(result["authoritative"])

    def test_reject_missing_cfop_and_ncm(self) -> None:
        for missing in ("cfop", "ncm"):
            with self.subTest(missing=missing):
                payload = {
                    "data": {
                        **self.bling["data"],
                        "itens": [
                            {
                                k: v
                                for k, v in self.bling["data"]["itens"][0].items()
                                if k != missing
                            }
                        ],
                    }
                }
                with self.assertRaises(ConnectorValidationError):
                    normalize_erp_order(payload, platform="BLING_V3")

    def test_reject_negative_and_nonfinite_amounts(self) -> None:
        for value in ("NaN", "Infinity", "-1"):
            with self.subTest(value=value):
                line = {**self.bling["data"]["itens"][0], "quantidade": value}
                with self.assertRaises(ConnectorValidationError):
                    normalize_erp_order(
                        {"data": {**self.bling["data"], "itens": [line]}}, platform="BLING_V3"
                    )

    def test_reject_unknown_platform(self) -> None:
        with self.assertRaises(ConnectorValidationError):
            normalize_erp_order(self.bling, platform="OMIE")

    def test_no_generic_tax_determination(self) -> None:
        for cfop, crt in (("7102", 3), ("5102", 1), ("6102", 3)):
            assessment = review_cross_tax_dimensions(
                cnae="4711301",
                ncm="85181020",
                cfop=cfop,
                crt=crt,
                uf_origem="SP",
                uf_destino="EX" if cfop.startswith("7") else "SP",
            )
            self.assertEqual(assessment.status, "REVIEW_REQUIRED")
            self.assertFalse(assessment.authoritative)
            self.assertIsNone(assessment.cst)
            self.assertIsNone(assessment.cclasstrib)
            self.assertTrue(assessment.approval_required)

    def test_invalid_cross_dimensions(self) -> None:
        result = review_cross_tax_dimensions(
            cnae="xxx", ncm="1", cfop="bad", crt=99, uf_origem="ZZ", uf_destino="SP"
        )
        self.assertEqual(result.status, "INVALID_INPUT")
        self.assertIsNone(result.cst)


if __name__ == "__main__":
    unittest.main()
