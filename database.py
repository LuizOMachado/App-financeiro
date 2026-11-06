
from __future__ import annotations

import functools
import logging
import os
import shutil
import sqlite3
from contextlib import closing, contextmanager
from datetime import date
from pathlib import Path
from typing import Iterator, Optional

logger = logging.getLogger("oria.database")

NOME_BANCO = "oria.db"
NOME_BANCO_LEGADO = "financeiro.db"
CATEGORIAS = ("Entrada", "Gasto", "Investimento")


def _pasta_de_dados() -> Path:
    # Em builds mobile (`flet build apk`) o Flet expõe a pasta persistente do app
    # nesta variável. No desktop mantemos o comportamento anterior: pasta do usuário.
    pasta = os.environ.get("FLET_APP_STORAGE_DATA")
    return Path(pasta) if pasta else Path.home()


# ORIA_DB_PATH permite apontar para outro arquivo (útil em testes).
DB_PATH: Path = Path(os.environ.get("ORIA_DB_PATH") or (_pasta_de_dados() / NOME_BANCO))


class ErroBanco(Exception):
    """Falha de acesso ao banco, com mensagem já legível para o usuário."""


def _traduz_erros(mensagem: str):
    """Converte sqlite3.Error em ErroBanco, registrando o erro original no log."""

    def decorador(funcao):
        @functools.wraps(funcao)
        def interna(*args, **kwargs):
            try:
                return funcao(*args, **kwargs)
            except sqlite3.Error as exc:
                logger.exception(mensagem)
                raise ErroBanco(mensagem) from exc

        return interna

    return decorador


@contextmanager
def _conexao() -> Iterator[sqlite3.Connection]:
    """Abre uma conexão, confirma (ou reverte) a transação e SEMPRE a fecha."""
    with closing(sqlite3.connect(DB_PATH, timeout=10)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        with conn:  # commit se tudo deu certo, rollback se houve exceção
            yield conn


# ---------------------------------------------------------------------------
# Esquema
# ---------------------------------------------------------------------------

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS investimentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    instituicao     TEXT NOT NULL COLLATE NOCASE,
    tipo            TEXT NOT NULL COLLATE NOCASE,
    valor_acumulado REAL NOT NULL DEFAULT 0.0,
    UNIQUE (instituicao, tipo)
);

CREATE TABLE IF NOT EXISTS transacoes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao       TEXT NOT NULL,
    valor           REAL NOT NULL,
    categoria       TEXT NOT NULL
                    CHECK (categoria IN ('Entrada', 'Gasto', 'Investimento')),
    data            TEXT NOT NULL,                     -- AAAA-MM-DD
    efetivada       INTEGER NOT NULL DEFAULT 0 CHECK (efetivada IN (0, 1)),
    investimento_id INTEGER REFERENCES investimentos (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_transacoes_data ON transacoes (data);

CREATE TABLE IF NOT EXISTS preferencias (
    id          INTEGER PRIMARY KEY CHECK (id = 1),
    tema        TEXT NOT NULL DEFAULT 'claro' CHECK (tema IN ('claro', 'escuro')),
    pin_hash    TEXT,
    pin_tamanho INTEGER
);

INSERT OR IGNORE INTO preferencias (id) VALUES (1);
"""


@_traduz_erros("Não foi possível preparar o banco de dados.")
def inicializar() -> None:
    """Cria o banco e as tabelas (idempotente). Na primeira execução, importa o
    `financeiro.db` da versão anterior, se existir ao lado do novo arquivo."""
    primeira_vez = not DB_PATH.exists()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _conexao() as conn:
        conn.executescript(_ESQUEMA)
    if primeira_vez:
        try:
            _migrar_dados_legados()
        except (sqlite3.Error, OSError):
            # A migração é uma cortesia: se falhar, o app abre vazio e o
            # financeiro.db antigo continua intacto (foi aberto só para leitura).
            logger.exception("Não foi possível importar o financeiro.db anterior.")


_CATEGORIAS_LEGADAS = {
    "Entrada Efetivada": "Entrada",
    "Entrada Futura": "Entrada",
    "Gasto Fixo": "Gasto",
    "Gasto Variável": "Gasto",
}


def _migrar_dados_legados() -> int:
    legado = DB_PATH.with_name(NOME_BANCO_LEGADO)
    if not legado.exists():
        return 0
    with closing(sqlite3.connect(f"{legado.resolve().as_uri()}?mode=ro", uri=True)) as origem:
        origem.row_factory = sqlite3.Row
        linhas = origem.execute(
            "SELECT descricao, valor, categoria, data, efetivada FROM transacoes"
        ).fetchall()

    migradas = 0
    with _conexao() as conn:
        for linha in linhas:
            categoria = _CATEGORIAS_LEGADAS.get(linha["categoria"])
            if categoria is None:
                continue
            # Entradas futuras ainda pendentes continuam pendentes (o gatilho por
            # data as efetiva); o restante já contava no saldo e continua contando.
            pendente = linha["categoria"] == "Entrada Futura" and not linha["efetivada"]
            conn.execute(
                "INSERT INTO transacoes (descricao, valor, categoria, data, efetivada) "
                "VALUES (?, ?, ?, ?, ?)",
                (linha["descricao"], linha["valor"], categoria, linha["data"], 0 if pendente else 1),
            )
            migradas += 1
    logger.info("%d transações importadas do financeiro.db.", migradas)
    return migradas


# ---------------------------------------------------------------------------
# Preferências (tema e PIN)
# ---------------------------------------------------------------------------

@_traduz_erros("Não foi possível ler as preferências.")
def obter_preferencias() -> dict:
    with _conexao() as conn:
        linha = conn.execute(
            "SELECT tema, pin_hash, pin_tamanho FROM preferencias WHERE id = 1"
        ).fetchone()
        return dict(linha)


@_traduz_erros("Não foi possível salvar o tema.")
def salvar_tema(tema: str) -> None:
    with _conexao() as conn:
        conn.execute("UPDATE preferencias SET tema = ? WHERE id = 1", (tema,))


@_traduz_erros("Não foi possível salvar o PIN.")
def salvar_pin(pin_hash: str, tamanho: int) -> None:
    with _conexao() as conn:
        conn.execute(
            "UPDATE preferencias SET pin_hash = ?, pin_tamanho = ? WHERE id = 1",
            (pin_hash, tamanho),
        )


@_traduz_erros("Não foi possível remover o PIN.")
def remover_pin() -> None:
    with _conexao() as conn:
        conn.execute("UPDATE preferencias SET pin_hash = NULL, pin_tamanho = NULL WHERE id = 1")


# ---------------------------------------------------------------------------
# Transações
# ---------------------------------------------------------------------------

def _limites_do_mes(mes: int, ano: int) -> tuple[str, str]:
    """Intervalo [início, fim) do mês em ISO. Comparar texto ISO usa o índice,
    ao contrário do `LIKE '2026-11-%'` que a versão anterior usava."""
    inicio = date(ano, mes, 1)
    fim = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
    return inicio.isoformat(), fim.isoformat()


def _efetivar_pendentes(conn: sqlite3.Connection, hoje: str) -> int:
    """Gatilho por tempo: torna efetivas as transações com data <= hoje.

    Para investimentos, o valor só entra no Cofre no momento da efetivação, na
    mesma transação SQL. Assim, um aporte agendado para o futuro não infla o
    patrimônio antes de sair do saldo.

    `hoje` vem do Python (data local). Usar `date('now')` do SQLite seria UTC, e
    no Brasil isso já "vira o dia" às 21h.
    """
    conn.execute(
        """
        UPDATE investimentos
           SET valor_acumulado = ROUND(valor_acumulado + (
                   SELECT COALESCE(SUM(t.valor), 0)
                     FROM transacoes t
                    WHERE t.investimento_id = investimentos.id
                      AND t.efetivada = 0 AND t.data <= :hoje), 2)
         WHERE id IN (SELECT investimento_id FROM transacoes
                       WHERE efetivada = 0 AND data <= :hoje
                         AND investimento_id IS NOT NULL)
        """,
        {"hoje": hoje},
    )
    cursor = conn.execute(
        "UPDATE transacoes SET efetivada = 1 WHERE efetivada = 0 AND data <= ?", (hoje,)
    )
    return cursor.rowcount


@_traduz_erros("Não foi possível atualizar os lançamentos agendados.")
def efetivar_transacoes_ate(hoje: str) -> int:
    """Roda ao abrir o app (e ao navegar). Retorna quantas transações foram efetivadas."""
    with _conexao() as conn:
        return _efetivar_pendentes(conn, hoje)


def _obter_ou_criar_investimento(conn: sqlite3.Connection, instituicao: str, tipo: str) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO investimentos (instituicao, tipo) VALUES (?, ?)",
        (instituicao, tipo),
    )
    linha = conn.execute(
        "SELECT id FROM investimentos WHERE instituicao = ? AND tipo = ?", (instituicao, tipo)
    ).fetchone()
    return linha["id"]


@_traduz_erros("Não foi possível salvar o lançamento.")
def adicionar_transacao(
    descricao: str,
    valor: float,
    categoria: str,
    data: str,
    hoje: str,
    instituicao: Optional[str] = None,
    tipo_investimento: Optional[str] = None,
) -> int:
    """Insere o lançamento e já efetiva o que estiver vencido, tudo atomicamente."""
    with _conexao() as conn:
        investimento_id = None
        if categoria == "Investimento":
            investimento_id = _obter_ou_criar_investimento(conn, instituicao, tipo_investimento)
        cursor = conn.execute(
            "INSERT INTO transacoes (descricao, valor, categoria, data, efetivada, investimento_id) "
            "VALUES (?, ?, ?, ?, 0, ?)",
            (descricao, valor, categoria, data, investimento_id),
        )
        _efetivar_pendentes(conn, hoje)
        return cursor.lastrowid


@_traduz_erros("Não foi possível excluir o lançamento.")
def excluir_transacao(id_transacao: int) -> bool:
    """Exclui o lançamento. Se ele já tinha entrado no Cofre, devolve o valor."""
    with _conexao() as conn:
        linha = conn.execute(
            "SELECT valor, efetivada, investimento_id FROM transacoes WHERE id = ?",
            (id_transacao,),
        ).fetchone()
        if linha is None:
            return False

        investimento_id = linha["investimento_id"]
        if investimento_id is not None and linha["efetivada"]:
            conn.execute(
                "UPDATE investimentos SET valor_acumulado = ROUND(valor_acumulado - ?, 2) WHERE id = ?",
                (linha["valor"], investimento_id),
            )
        conn.execute("DELETE FROM transacoes WHERE id = ?", (id_transacao,))

        if investimento_id is not None:
            # Se o local ficou zerado e sem nenhum lançamento, some do Cofre.
            conn.execute(
                """
                DELETE FROM investimentos
                 WHERE id = ? AND valor_acumulado < 0.005
                   AND NOT EXISTS (SELECT 1 FROM transacoes WHERE investimento_id = ?)
                """,
                (investimento_id, investimento_id),
            )
        return True


@_traduz_erros("Não foi possível carregar os lançamentos.")
def listar_transacoes_do_mes(mes: int, ano: int, apenas_pendentes: bool = False) -> list[dict]:
    inicio, fim = _limites_do_mes(mes, ano)
    filtro = "AND t.efetivada = 0" if apenas_pendentes else ""
    ordem = "t.data ASC, t.id ASC" if apenas_pendentes else "t.data DESC, t.id DESC"
    with _conexao() as conn:
        linhas = conn.execute(
            f"""
            SELECT t.id, t.descricao, t.valor, t.categoria, t.data, t.efetivada,
                   i.instituicao, i.tipo AS tipo_investimento
              FROM transacoes t
              LEFT JOIN investimentos i ON i.id = t.investimento_id
             WHERE t.data >= ? AND t.data < ? {filtro}
             ORDER BY {ordem}
            """,
            (inicio, fim),
        ).fetchall()
        return [dict(linha) for linha in linhas]


@_traduz_erros("Não foi possível calcular o resumo do mês.")
def totais_do_mes(mes: int, ano: int) -> dict[tuple[str, int], float]:
    """Soma por (categoria, efetivada), calculada pelo próprio SQLite."""
    inicio, fim = _limites_do_mes(mes, ano)
    with _conexao() as conn:
        linhas = conn.execute(
            """
            SELECT categoria, efetivada, COALESCE(SUM(valor), 0) AS total
              FROM transacoes
             WHERE data >= ? AND data < ?
             GROUP BY categoria, efetivada
            """,
            (inicio, fim),
        ).fetchall()
        return {(linha["categoria"], linha["efetivada"]): linha["total"] for linha in linhas}


@_traduz_erros("Não foi possível listar os meses.")
def listar_meses_com_transacoes() -> list[tuple[int, int]]:
    """Pares (ano, mês) que possuem lançamentos."""
    with _conexao() as conn:
        linhas = conn.execute("SELECT DISTINCT substr(data, 1, 7) AS ym FROM transacoes").fetchall()
    meses = []
    for linha in linhas:
        try:
            ano, mes = linha["ym"].split("-")
            meses.append((int(ano), int(mes)))
        except (ValueError, AttributeError):
            continue  # linha com data corrompida: ignora em vez de derrubar o app
    return meses


# ---------------------------------------------------------------------------
# Cofre
# ---------------------------------------------------------------------------

@_traduz_erros("Não foi possível carregar o Cofre.")
def listar_investimentos() -> list[dict]:
    with _conexao() as conn:
        linhas = conn.execute(
            "SELECT id, instituicao, tipo, valor_acumulado FROM investimentos "
            "ORDER BY valor_acumulado DESC, instituicao COLLATE NOCASE"
        ).fetchall()
        return [dict(linha) for linha in linhas]


# ---------------------------------------------------------------------------
# Backup e restauração
# ---------------------------------------------------------------------------

_TABELAS_OBRIGATORIAS = {"transacoes", "investimentos", "preferencias"}


def exportar_banco(destino: Path) -> Path:
    """Copia o oria.db para `destino` com shutil. Como cada operação fecha a sua
    conexão, o arquivo está consistente no momento da cópia."""
    destino = Path(destino)
    try:
        if destino.resolve() == DB_PATH.resolve():
            raise ErroBanco("Escolha um local diferente do banco em uso.")
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DB_PATH, destino)
    except OSError as exc:
        logger.exception("Falha ao exportar o banco")
        raise ErroBanco(
            "Não foi possível gravar o backup nesse local. Escolha outra pasta."
        ) from exc
    return destino


def _validar_banco_oria(caminho: Path) -> None:
    """Confere se o arquivo é um banco SQLite íntegro com as tabelas do Oria."""
    mensagem = "O arquivo escolhido não é um backup válido do Oria."
    try:
        with closing(sqlite3.connect(f"{caminho.resolve().as_uri()}?mode=ro", uri=True)) as conn:
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ErroBanco(mensagem)
            tabelas = {
                linha[0]
                for linha in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
    except sqlite3.Error as exc:
        raise ErroBanco(mensagem) from exc
    if not _TABELAS_OBRIGATORIAS <= tabelas:
        raise ErroBanco(mensagem)


def importar_banco(origem: Path) -> None:
    """Substitui o oria.db pelo arquivo escolhido.

    Antes de trocar, valida o arquivo e guarda o banco atual em `oria.db.bak`.
    A troca usa um arquivo temporário + os.replace para não deixar o banco pela metade.
    """
    origem = Path(origem)
    if not origem.is_file():
        raise ErroBanco("Não encontrei o arquivo escolhido.")
    _validar_banco_oria(origem)

    temporario = DB_PATH.with_name(DB_PATH.name + ".tmp")
    copia_seguranca = DB_PATH.with_name(DB_PATH.name + ".bak")
    try:
        shutil.copy2(origem, temporario)
        if DB_PATH.exists():
            shutil.copy2(DB_PATH, copia_seguranca)
        os.replace(temporario, DB_PATH)
    except OSError as exc:
        logger.exception("Falha ao importar o banco")
        raise ErroBanco("Não foi possível importar o arquivo escolhido.") from exc
    finally:
        temporario.unlink(missing_ok=True)

    inicializar()  # idempotente: garante tabelas/índices ausentes em backups mais antigos


if __name__ == "__main__":
    inicializar()
    print(f"Banco '{DB_PATH}' criado/verificado com sucesso e pronto para uso.")
