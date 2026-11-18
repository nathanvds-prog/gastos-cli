"""Interface de linha de comando do gerenciador de gastos."""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from . import core
from .core import GastosError, Repositorio

ARQUIVO_PADRAO = Path.home() / ".gastos.json"


def _data_iso(texto: str) -> date:
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(f"data inválida: {texto!r} (use AAAA-MM-DD)") from None


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gastos",
        description="Gerenciador de gastos pessoais no terminal.",
    )
    parser.add_argument(
        "--arquivo",
        type=Path,
        default=ARQUIVO_PADRAO,
        help="arquivo JSON onde os dados são guardados (padrão: ~/.gastos.json)",
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    add = sub.add_parser("add", help="adiciona uma despesa")
    add.add_argument("descricao", help="ex.: 'Almoço'")
    add.add_argument("valor", help="ex.: 25,90")
    add.add_argument("-c", "--categoria", default="outros")
    add.add_argument("-d", "--data", type=_data_iso, default=None, help="AAAA-MM-DD (padrão: hoje)")

    lst = sub.add_parser("list", help="lista as despesas")
    lst.add_argument("-c", "--categoria")
    lst.add_argument("--ano", type=int)
    lst.add_argument("--mes", type=int)

    rm = sub.add_parser("remove", help="remove uma despesa pelo id")
    rm.add_argument("id", type=int)

    res = sub.add_parser("summary", help="mostra o total gasto por categoria")
    res.add_argument("--ano", type=int)
    res.add_argument("--mes", type=int)
    return parser


def _imprimir_lista(itens: list[core.Despesa]) -> None:
    if not itens:
        print("Nenhuma despesa encontrada.")
        return
    for d in itens:
        print(
            f"{d.id:>3}  {d.data.isoformat()}  {d.categoria:<12} "
            f"{d.descricao:<30} {core.formatar_brl(d.valor):>14}"
        )
    print(f"\nTotal: {core.formatar_brl(core.total(itens))}")


def _imprimir_resumo(itens: list[core.Despesa]) -> None:
    if not itens:
        print("Nenhuma despesa encontrada.")
        return
    soma = core.total(itens)
    for categoria, valor in core.resumo_por_categoria(itens).items():
        percentual = f"{valor / soma * 100:5.1f}".replace(".", ",")
        print(f"{categoria:<14} {core.formatar_brl(valor):>14}  {percentual}%")
    print(f"\nTotal: {core.formatar_brl(soma)}")


def main(argv=None) -> int:
    args = criar_parser().parse_args(argv)
    repo = Repositorio(args.arquivo)
    try:
        despesas = repo.carregar()
        if args.comando == "add":
            nova = core.adicionar(despesas, args.descricao, args.valor, args.categoria, args.data)
            repo.salvar(despesas)
            print(f"Despesa #{nova.id} adicionada: {nova.descricao} ({core.formatar_brl(nova.valor)})")
        elif args.comando == "list":
            _imprimir_lista(core.filtrar(despesas, args.categoria, args.ano, args.mes))
        elif args.comando == "remove":
            removida = core.remover(despesas, args.id)
            repo.salvar(despesas)
            print(f"Despesa #{removida.id} removida: {removida.descricao}")
        elif args.comando == "summary":
            _imprimir_resumo(core.filtrar(despesas, ano=args.ano, mes=args.mes))
    except GastosError as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    return 0
