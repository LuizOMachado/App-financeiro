
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

import database
from database import ErroBanco

CATEGORIAS = database.CATEGORIAS
TIPOS_INVESTIMENTO = (
    "Renda fixa",
    "Tesouro Direto",
    "CDB",
    "Ações",
    "Fundos imobiliários",
    "Fundos de investimento",
    "Criptomoedas",
    "Poupança",
    "Outro",
)
TEMAS = ("claro", "escuro")
PIN_MIN, PIN_MAX = 4, 6

_ITERACOES_PIN = 120_000
_LIMITE_DESCRICAO = 60
_LIMITE_LOCAL = 40

MESES_PT_BR = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}
DIAS_PT_BR = ("segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo")


class ErroOria(Exception):
    """Erro de validação ou de regra, com mensagem pronta para mostrar ao usuário."""


# A interface captura esta tupla e mostra str(erro) ao usuário.
ERROS_ESPERADOS = (ErroOria, ErroBanco)


# ---------------------------------------------------------------------------
# Resultados entregues à interface
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ResumoMes:
    entradas: float
    gastos: float
    investido: float
    saldo_livre: float
    a_receber: float
    a_pagar: float
    a_investir: float


@dataclass(frozen=True)
class ItemExtrato:
    id: int
    descricao: str
    valor: float
    categoria: str
    data_iso: str
    data_br: str
    efetivada: bool
    local: Optional[str]  # "Nubank · CDB" para investimentos


@dataclass(frozen=True)
class LocalInvestimento:
    id: int
    instituicao: str
    tipo: str
    valor: float
    percentual: float  # fração do total guardado, de 0 a 1


@dataclass(frozen=True)
class ResumoCofre:
    total: float
    locais: tuple[LocalInvestimento, ...]


@dataclass(frozen=True)
class LocalDisponivel:
    instituicao: str
    tipo: str
    rotulo: str


# ---------------------------------------------------------------------------
# Datas e formatação
# ---------------------------------------------------------------------------

def _hoje(hoje: Optional[date] = None) -> date:
    return hoje or date.today()


def formatar_data_br(data_iso: str) -> str:
    try:
        ano, mes, dia = data_iso.split("-")
        return f"{dia}/{mes}/{ano}"
    except ValueError:
        return data_iso


def obter_nome_mes_ano(mes: int, ano: int) -> str:
    try:
        return f"{MESES_PT_BR.get(int(mes), 'Mês inválido')} de {ano}"
    except (ValueError, TypeError):
        return f"Período inválido ({mes}/{ano})"


def rotulo_do_dia(data_iso: str, hoje: Optional[date] = None) -> str:
    """'Hoje', 'Ontem', 'Amanhã' ou 'Quarta, 12 de novembro' (com o ano, se for outro)."""
    try:
        dia = date.fromisoformat(data_iso)
    except ValueError:
        return data_iso
    base = _hoje(hoje)
    if dia == base:
        return "Hoje"
    if dia == base - timedelta(days=1):
        return "Ontem"
    if dia == base + timedelta(days=1):
        return "Amanhã"
    texto = f"{DIAS_PT_BR[dia.weekday()].capitalize()}, {dia.day} de {MESES_PT_BR[dia.month].lower()}"
    return texto if dia.year == base.year else f"{texto} de {dia.year}"


def formatar_moeda(valor: float) -> str:
    valor = round(float(valor), 2)
    if valor == 0:
        valor = 0.0  # evita "-R$ 0,00"
    texto = f"{abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"-R$ {texto}" if valor < 0 else f"R$ {texto}"


def converter_valor(texto: str) -> float:
    """Converte o que o usuário digitou em número positivo.

    Aceita '1250', '1250,90', '1.250,90', '1250.90' e 'R$ 1.250,90'. Um único
    ponto seguido de exatamente 3 dígitos ('1.500') é lido como milhar.
    """
    mensagem = "Informe um valor maior que zero, por exemplo 1.250,90."
    bruto = (texto or "").replace("R$", "").replace(" ", "").strip()
    if not re.fullmatch(r"[0-9.,]+", bruto):
        raise ErroOria(mensagem)

    if "," in bruto:
        bruto = bruto.replace(".", "").replace(",", ".")
    elif bruto.count(".") > 1:
        bruto = bruto.replace(".", "")
    elif bruto.count(".") == 1:
        inteiro, decimais = bruto.split(".")
        if len(decimais) == 3 and inteiro not in ("", "0"):
            bruto = inteiro + decimais

    try:
        # Decimal + meio-para-cima: round() do Python arredonda 0,125 para 0,12.
        valor = float(Decimal(bruto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    except InvalidOperation:
        raise ErroOria(mensagem) from None
    if valor <= 0:
        raise ErroOria(mensagem)
    if valor > 999_999_999_999:
        raise ErroOria("Esse valor é grande demais. Confira se digitou corretamente.")
    return valor


def _limpar_texto(texto: Optional[str]) -> str:
    return " ".join((texto or "").split())


# ---------------------------------------------------------------------------
# Inicialização e automação por tempo
# ---------------------------------------------------------------------------

def efetivar_vencidas(hoje: Optional[date] = None) -> int:
    """Efetiva toda transação com data <= hoje. Retorna quantas mudaram."""
    return database.efetivar_transacoes_ate(_hoje(hoje).isoformat())


def inicializar(hoje: Optional[date] = None) -> int:
    """Prepara o banco e roda o gatilho por tempo. Chamada ao abrir o app."""
    database.inicializar()
    return efetivar_vencidas(hoje)


# ---------------------------------------------------------------------------
# Lançamentos
# ---------------------------------------------------------------------------

def registrar_transacao(
    descricao: str,
    valor_texto: str,
    categoria: str,
    data_transacao: date,
    instituicao: str = "",
    tipo_investimento: str = "",
    hoje: Optional[date] = None,
) -> bool:
    """Valida e grava um lançamento. Retorna True se ele já foi efetivado e
    False se ficou agendado para uma data futura."""
    if categoria not in CATEGORIAS:
        raise ErroOria("Escolha se o lançamento é entrada, gasto ou investimento.")

    descricao = _limpar_texto(descricao)
    if not descricao:
        raise ErroOria("Informe uma descrição.")
    if len(descricao) > _LIMITE_DESCRICAO:
        raise ErroOria(f"A descrição pode ter até {_LIMITE_DESCRICAO} caracteres.")

    valor = converter_valor(valor_texto)

    if not isinstance(data_transacao, date):
        raise ErroOria("Escolha a data do lançamento.")

    instituicao = _limpar_texto(instituicao)
    tipo_investimento = _limpar_texto(tipo_investimento)
    if categoria == "Investimento":
        if not instituicao:
            raise ErroOria("Informe onde o dinheiro será guardado.")
        if not tipo_investimento:
            raise ErroOria("Escolha o tipo de investimento.")
        if len(instituicao) > _LIMITE_LOCAL or len(tipo_investimento) > _LIMITE_LOCAL:
            raise ErroOria(f"Instituição e tipo podem ter até {_LIMITE_LOCAL} caracteres.")
    else:
        instituicao = tipo_investimento = ""

    base = _hoje(hoje)
    database.adicionar_transacao(
        descricao,
        valor,
        categoria,
        data_transacao.isoformat(),
        base.isoformat(),
        instituicao or None,
        tipo_investimento or None,
    )
    return data_transacao <= base


def excluir_transacao(id_transacao: int) -> bool:
    return database.excluir_transacao(id_transacao)


def _montar_item(linha: dict) -> ItemExtrato:
    local = None
    if linha["categoria"] == "Investimento" and linha["instituicao"]:
        local = f"{linha['instituicao']} · {linha['tipo_investimento']}"
    return ItemExtrato(
        id=linha["id"],
        descricao=linha["descricao"],
        valor=linha["valor"],
        categoria=linha["categoria"],
        data_iso=linha["data"],
        data_br=formatar_data_br(linha["data"]),
        efetivada=bool(linha["efetivada"]),
        local=local,
    )


def listar_extrato(mes: int, ano: int, categoria: Optional[str] = None) -> list[ItemExtrato]:
    """Lançamentos do mês, do mais recente para o mais antigo."""
    linhas = database.listar_transacoes_do_mes(mes, ano)
    return [_montar_item(l) for l in linhas if categoria is None or l["categoria"] == categoria]


def listar_agendadas(mes: int, ano: int) -> list[ItemExtrato]:
    """Lançamentos do mês que ainda aguardam a data, do mais próximo ao mais distante."""
    return [_montar_item(l) for l in database.listar_transacoes_do_mes(mes, ano, apenas_pendentes=True)]


def obter_meses_disponiveis(hoje: Optional[date] = None) -> list[tuple[int, int]]:
    """Pares (ano, mês) com lançamentos, mais o mês atual, em ordem crescente."""
    base = _hoje(hoje)
    meses = {(base.year, base.month)}
    meses.update(database.listar_meses_com_transacoes())
    return sorted(meses)


def calcular_resumo_mes(mes: int, ano: int) -> ResumoMes:
    """Saldo livre = entradas efetivadas - gastos efetivados - investimentos efetivados.

    Entradas, gastos e investimentos só contam depois de efetivados (a data chegou).
    O que ainda está agendado aparece à parte (a_receber, a_pagar, a_investir).
    """
    totais = database.totais_do_mes(mes, ano)

    def soma(categoria: str, efetivada: int) -> float:
        return totais.get((categoria, efetivada), 0.0)

    entradas = soma("Entrada", 1)
    gastos = soma("Gasto", 1)
    investido = soma("Investimento", 1)
    return ResumoMes(
        entradas=round(entradas, 2),
        gastos=round(gastos, 2),
        investido=round(investido, 2),
        saldo_livre=round(entradas - gastos - investido, 2),
        a_receber=round(soma("Entrada", 0), 2),
        a_pagar=round(soma("Gasto", 0), 2),
        a_investir=round(soma("Investimento", 0), 2),
    )


# ---------------------------------------------------------------------------
# Cofre
# ---------------------------------------------------------------------------

def resumo_cofre() -> ResumoCofre:
    linhas = [l for l in database.listar_investimentos() if l["valor_acumulado"] >= 0.005]
    total = round(sum(l["valor_acumulado"] for l in linhas), 2)
    locais = tuple(
        LocalInvestimento(
            id=l["id"],
            instituicao=l["instituicao"],
            tipo=l["tipo"],
            valor=l["valor_acumulado"],
            percentual=(l["valor_acumulado"] / total) if total > 0 else 0.0,
        )
        for l in linhas
    )
    return ResumoCofre(total=total, locais=locais)


def listar_locais_disponiveis() -> list[LocalDisponivel]:
    """Locais já usados, para reaproveitar ao registrar um novo aporte."""
    return [
        LocalDisponivel(l["instituicao"], l["tipo"], f"{l['instituicao']} · {l['tipo']}")
        for l in database.listar_investimentos()
    ]


# ---------------------------------------------------------------------------
# Tema
# ---------------------------------------------------------------------------

def obter_tema() -> str:
    return database.obter_preferencias()["tema"]


def definir_tema(tema: str) -> None:
    if tema not in TEMAS:
        raise ErroOria("Tema desconhecido.")
    database.salvar_tema(tema)


# ---------------------------------------------------------------------------
# PIN de acesso
# ---------------------------------------------------------------------------
# O PIN nunca é guardado em texto: gravamos PBKDF2-HMAC-SHA256 com sal aleatório.
# Ele protege o acesso à interface; o arquivo oria.db em si não é criptografado.

def _hash_pin(pin: str) -> str:
    sal = secrets.token_bytes(16)
    resumo = hashlib.pbkdf2_hmac("sha256", pin.encode(), sal, _ITERACOES_PIN)
    return f"pbkdf2_sha256${_ITERACOES_PIN}${sal.hex()}${resumo.hex()}"


def _confere_pin(pin: str, armazenado: str) -> bool:
    try:
        _, iteracoes, sal_hex, resumo_hex = armazenado.split("$")
        calculado = hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(sal_hex), int(iteracoes))
    except (ValueError, TypeError, AttributeError):
        return False
    return hmac.compare_digest(calculado.hex(), resumo_hex)


def _validar_formato_pin(pin: str) -> None:
    if not re.fullmatch(rf"[0-9]{{{PIN_MIN},{PIN_MAX}}}", pin or ""):
        raise ErroOria(f"O PIN deve ter de {PIN_MIN} a {PIN_MAX} números.")


def pin_configurado() -> bool:
    return bool(database.obter_preferencias()["pin_hash"])


def tamanho_do_pin() -> int:
    """Quantos dígitos tem o PIN cadastrado (0 se não houver)."""
    prefs = database.obter_preferencias()
    return int(prefs["pin_tamanho"] or 0) if prefs["pin_hash"] else 0


def validar_pin(pin: str) -> bool:
    armazenado = database.obter_preferencias()["pin_hash"]
    return bool(armazenado) and _confere_pin(pin or "", armazenado)


def definir_pin(novo: str, confirmacao: str, atual: Optional[str] = None) -> None:
    """Cadastra o PIN ou troca o existente (nesse caso, exige o PIN atual)."""
    if pin_configurado() and not validar_pin(atual or ""):
        raise ErroOria("O PIN atual está incorreto.")
    _validar_formato_pin(novo)
    if novo != confirmacao:
        raise ErroOria("A confirmação não confere com o novo PIN.")
    database.salvar_pin(_hash_pin(novo), len(novo))


def remover_pin(atual: str) -> None:
    if not validar_pin(atual):
        raise ErroOria("O PIN atual está incorreto.")
    database.remover_pin()


# ---------------------------------------------------------------------------
# Backup e restauração
# ---------------------------------------------------------------------------

def nome_sugerido_backup(agora: Optional[datetime] = None) -> str:
    return f"oria_backup_{(agora or datetime.now()):%Y%m%d_%H%M}.db"


def exportar_backup(destino: str) -> str:
    """Copia o banco para `destino` (arquivo ou pasta). Retorna o caminho final."""
    caminho = Path(destino)
    if caminho.is_dir():
        caminho = caminho / nome_sugerido_backup()
    elif not caminho.suffix:
        caminho = caminho.with_suffix(".db")
    return str(database.exportar_banco(caminho))


def importar_backup(origem: str) -> None:
    """Substitui os dados atuais pelos do backup (o banco atual vai para oria.db.bak)."""
    database.importar_banco(Path(origem))
