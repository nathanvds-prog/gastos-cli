# 💸 Gastos CLI

Gerenciador de gastos pessoais para o terminal, feito em Python puro (somente biblioteca padrão, sem dependências externas).

Registre despesas, filtre por categoria ou mês e veja quanto você gastou em cada categoria.

## Funcionalidades

- Adicionar, listar e remover despesas
- Filtro por categoria, ano e mês
- Resumo por categoria com percentual do total
- Valores em formato brasileiro (`R$ 1.234,50`), aceitando `25,90` ou `25.90` na entrada
- Dados guardados em um arquivo JSON local
- Testes automatizados com `unittest`

## Requisitos

- Python 3.9 ou superior

## Como usar

Clone o repositório e, dentro da pasta do projeto, rode:

```bash
# adicionar despesas
python -m gastos add "Almoço" 25,90 -c comida
python -m gastos add "Metrô" 5 -c transporte -d 2026-11-10

# listar (com filtros opcionais)
python -m gastos list
python -m gastos list -c comida --mes 11 --ano 2026

# resumo por categoria
python -m gastos summary --mes 11

# remover pela id mostrada na listagem
python -m gastos remove 1
```

Exemplo de saída:

```
$ python -m gastos summary
comida               R$ 25,90   83,8%
transporte            R$ 5,00   16,2%

Total: R$ 30,90
```

Por padrão os dados ficam em `~/.gastos.json`. Para usar outro arquivo:

```bash
python -m gastos --arquivo meus_gastos.json list
```

## Testes

```bash
python -m unittest -v
```

## Estrutura do projeto

```
gastos-cli/
├── gastos/
│   ├── core.py      # regras de negócio e persistência (sem I/O de terminal)
│   ├── cli.py       # interface de linha de comando (argparse)
│   └── __main__.py  # permite rodar com `python -m gastos`
└── tests/
    └── test_core.py # testes unitários e de fluxo da CLI
```

## Decisões de design

- **`Decimal` em vez de `float`** para dinheiro, evitando erros de arredondamento (`0.1 + 0.2`).
- **Separação entre lógica e interface:** `core.py` não sabe nada sobre terminal, o que torna as regras fáceis de testar e de reaproveitar (por exemplo, numa API ou interface web).
- **Camada de persistência isolada** na classe `Repositorio`, que pode ser trocada por SQLite sem alterar as regras de negócio.
- **Erros de domínio** (`GastosError`) tratados em um único ponto, com mensagens claras e código de saída diferente de zero.

## Ideias de evolução

- Orçamento mensal por categoria com alertas
- Exportação para CSV
- Despesas recorrentes
- Trocar o JSON por SQLite
- Gráficos de gastos no terminal
