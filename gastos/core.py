"""Lógica de negócio do gerenciador de gastos (sem nenhuma I/O de terminal)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional


class GastosError(Exception):
    """Erro de domínio: entrada inválida, item inexistente etc."""


@dataclass
class Despesa:
    id: int
    descricao: str
    valor: Decimal
    categoria: str
    data: date

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "descricao": self.descricao,
            "valor": str(self.valor),
            "categoria": self.categoria,
            "data": self.data.isoformat(),
        }

    @classmethod
    def from_dict(cls, dados: dict) -> "Despesa":
        return cls(
            id=int(dados["id"]),
            descricao=dados["descricao"],
            valor=Decimal(dados["valor"]),
            categoria=dados["categoria"],
            data=date.fromisoformat(dados["data"]),
        )


def parse_valor(texto) -> Decimal:
    """Converte '12,50' ou '12.5' em Decimal('12.50'). Rejeita zero e negativos."""
    try:
        valor = Decimal(str(texto).strip().replace(",", ".")).quantize(Decimal("0.01"))
    except InvalidOperation:
        raise GastosError(f"Valor inválido: {texto!r}") from None
    if not valor.is_finite() or valor <= 0:
        raise GastosError("O valor deve ser maior que zero.")
    return valor


def formatar_brl(valor: Decimal) -> str:
    """Formata como moeda brasileira: 1234.5 -> 'R$ 1.234,50'."""
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "#").replace(".", ",").replace("#", ".")
    return f"R$ {texto}"


class Repositorio:
    """Persistência das despesas em um arquivo JSON."""

    def __init__(self, caminho) -> None:
        self.caminho = Path(caminho)

    def carregar(self) -> list[Despesa]:
        if not self.caminho.exists():
            return []
        try:
            with self.caminho.open(encoding="utf-8") as arquivo:
                return [Despesa.from_dict(item) for item in json.load(arquivo)]
        except (json.JSONDecodeError, KeyError, ValueError, InvalidOperation) as erro:
            raise GastosError(f"Arquivo de dados corrompido ({self.caminho}): {erro}") from erro

    def salvar(self, despesas: list[Despesa]) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        with self.caminho.open("w", encoding="utf-8") as arquivo:
            json.dump([d.to_dict() for d in despesas], arquivo, ensure_ascii=False, indent=2)


def adicionar(
    despesas: list[Despesa],
    descricao: str,
    valor,
    categoria: str = "outros",
    data: Optional[date] = None,
) -> Despesa:
    descricao = descricao.strip()
    if not descricao:
        raise GastosError("A descrição não pode ser vazia.")
    nova = Despesa(
        id=max((d.id for d in despesas), default=0) + 1,
        descricao=descricao,
        valor=parse_valor(valor),
        categoria=categoria.strip().lower() or "outros",
        data=data or date.today(),
    )
    despesas.append(nova)
    return nova


def remover(despesas: list[Despesa], id_: int) -> Despesa:
    for posicao, despesa in enumerate(despesas):
        if despesa.id == id_:
            return despesas.pop(posicao)
    raise GastosError(f"Despesa {id_} não encontrada.")


def filtrar(
    despesas: list[Despesa],
    categoria: Optional[str] = None,
    ano: Optional[int] = None,
    mes: Optional[int] = None,
) -> list[Despesa]:
    if mes is not None and not 1 <= mes <= 12:
        raise GastosError("O mês deve estar entre 1 e 12.")
    resultado = despesas
    if categoria:
        resultado = [d for d in resultado if d.categoria == categoria.strip().lower()]
    if ano is not None:
        resultado = [d for d in resultado if d.data.year == ano]
    if mes is not None:
        resultado = [d for d in resultado if d.data.month == mes]
    return sorted(resultado, key=lambda d: (d.data, d.id))


def total(despesas: list[Despesa]) -> Decimal:
    return sum((d.valor for d in despesas), Decimal("0.00"))


def resumo_por_categoria(despesas: list[Despesa]) -> dict[str, Decimal]:
    """Total gasto por categoria, da maior para a menor."""
    acumulado: dict[str, Decimal] = {}
    for despesa in despesas:
        acumulado[despesa.categoria] = acumulado.get(despesa.categoria, Decimal("0.00")) + despesa.valor
    return dict(sorted(acumulado.items(), key=lambda par: par[1], reverse=True))
