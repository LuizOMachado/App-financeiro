
from __future__ import annotations

import functools
import logging
import os
from datetime import date, datetime
from typing import Callable, Optional

import flet as ft

import logic

# ===========================================================================
# Design tokens
# ===========================================================================

COR_SEMENTE = "#4B2BA3"  # violeta profundo
FUNDO_DA_PAGINA = {"claro": "#F6F4FB", "escuro": "#0E0B18"}

PALETA_CLARA = dict(
    primary="#4B2BA3", on_primary="#FFFFFF",
    primary_container="#E7DFFF", on_primary_container="#24106B",
    secondary="#0B7A75", on_secondary="#FFFFFF",
    secondary_container="#E7DFFF", on_secondary_container="#24106B",
    tertiary="#946300", on_tertiary="#FFFFFF",
    tertiary_container="#FFE7B0", on_tertiary_container="#3A2800",
    error="#BA2D52", on_error="#FFFFFF",
    error_container="#FFD9E0", on_error_container="#4A0618",
    surface="#FFFFFF", on_surface="#1B1530",
    surface_variant="#EFEBF8", on_surface_variant="#675F80",
    surface_container_lowest="#FFFFFF", surface_container_low="#FAF8FE",
    surface_container="#F4F1FB", surface_container_high="#EFEBF8",
    outline="#8C84A6", outline_variant="#E4DFF0",
    inverse_surface="#2A2340", on_inverse_surface="#F1EDFF",
    surface_tint="#FFFFFF", shadow="#000000",
)
PALETA_ESCURA = dict(
    primary="#BFA9FF", on_primary="#2A1170",
    primary_container="#3F2A94", on_primary_container="#E9DEFF",
    secondary="#4FD3C4", on_secondary="#00201E",
    secondary_container="#3B2A78", on_secondary_container="#EADFFF",
    tertiary="#F0BF5E", on_tertiary="#3A2800",
    tertiary_container="#5A4100", on_tertiary_container="#FFE9B8",
    error="#FF8FA6", on_error="#4A0618",
    error_container="#7A1530", on_error_container="#FFD9E0",
    surface="#1B1530", on_surface="#EEE9FB",
    surface_variant="#2A2243", on_surface_variant="#B2A9CF",
    surface_container_lowest="#0E0B18", surface_container_low="#17112A",
    surface_container="#201A38", surface_container_high="#272046",
    outline="#8279A3", outline_variant="#33294F",
    inverse_surface="#EEE9FB", on_inverse_surface="#1B1530",
    surface_tint="#1B1530", shadow="#000000",
)

COR_TEXTO = ft.Colors.ON_SURFACE
COR_SUAVE = ft.Colors.ON_SURFACE_VARIANT
COR_CARTAO = ft.Colors.SURFACE
COR_REALCE = ft.Colors.SURFACE_CONTAINER_HIGHEST  # preenchimentos discretos (= surface_variant)
COR_LINHA = ft.Colors.OUTLINE_VARIANT
COR_MARCA = ft.Colors.PRIMARY
COR_ENTRADA = ft.Colors.SECONDARY
COR_GASTO = ft.Colors.ERROR
COR_COFRE = ft.Colors.TERTIARY

# Elementos sobre o gradiente violeta (iguais nos dois temas)
HERO_DE, HERO_PARA = "#5B3CD6", "#2B1A7A"
BRANCO = ft.Colors.WHITE
BRANCO_SUAVE = ft.Colors.with_opacity(0.78, ft.Colors.WHITE)
BRANCO_LINHA = ft.Colors.with_opacity(0.18, ft.Colors.WHITE)
PONTO_ENTRADA, PONTO_GASTO, PONTO_COFRE = "#5EEAD4", "#FDA4AF", "#FCD34D"

# Raios de borda: o hero é o mais arredondado; campos e botões, o menor.
R_HERO, R_BLOCO, R_BOTAO, R_CAMPO = 28, 24, 18, 16

LARGURA_MENU_LATERAL = 840  # a partir daqui a barra inferior dá lugar ao menu lateral
LARGURA_DO_MENU = 96
LARGURA_MAXIMA_CONTEUDO = 1080

_PESOS = {
    400: ft.FontWeight.W_400, 500: ft.FontWeight.W_500, 600: ft.FontWeight.W_600,
    700: ft.FontWeight.W_700, 800: ft.FontWeight.W_800,
}
_NOVO_LOCAL = "__novo__"


def criar_tema(escuro: bool) -> ft.Theme:
    # A semente gera os papéis que não definimos (ex.: menus e calendário);
    # o ColorScheme fixa os que formam a identidade do Oria.
    return ft.Theme(
        color_scheme_seed=COR_SEMENTE,
        use_material3=True,
        color_scheme=ft.ColorScheme(**(PALETA_ESCURA if escuro else PALETA_CLARA)),
    )


# ===========================================================================
# Componentes básicos
# ===========================================================================

def txt(valor="", tamanho=15, peso=400, cor=COR_TEXTO, espacamento=None, **kw) -> ft.Text:
    """Texto com a escala tipográfica do Oria (peso e tamanho explícitos, cor do tema)."""
    estilo = ft.TextStyle(letter_spacing=espacamento) if espacamento is not None else None
    return ft.Text(valor, size=tamanho, weight=_PESOS[peso], color=cor, style=estilo, **kw)


def superficie(conteudo: ft.Control, padding=20, **kw) -> ft.Container:
    """Bloco de conteúdo: fundo do cartão e filete de borda, sem sombra."""
    return ft.Container(
        content=conteudo,
        padding=padding,
        border_radius=R_BLOCO,
        bgcolor=COR_CARTAO,
        border=ft.border.all(1, COR_LINHA),
        **kw,
    )


def criar_hero(conteudo: ft.Control, **kw) -> ft.Container:
    return ft.Container(
        content=conteudo,
        padding=ft.padding.all(24),
        border_radius=R_HERO,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=[HERO_DE, HERO_PARA]
        ),
        **kw,
    )


def campo(**kw) -> ft.TextField:
    """Campo de texto no visual do Oria. O que o chamador passa vence os padrões."""
    padrao = dict(
        border_radius=R_CAMPO,
        filled=True,
        fill_color=COR_REALCE,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=COR_MARCA,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=16),
        label_style=ft.TextStyle(color=COR_SUAVE),
        text_size=16,
    )
    return ft.TextField(**{**padrao, **kw})


def lista_suspensa(**kw) -> ft.Dropdown:
    padrao = dict(
        border_radius=R_CAMPO,
        filled=True,
        fill_color=COR_REALCE,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=COR_MARCA,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
        text_size=16,
    )
    return ft.Dropdown(**{**padrao, **kw})


def estilo_botao(**kw) -> ft.ButtonStyle:
    padrao = dict(
        shape=ft.RoundedRectangleBorder(radius=R_BOTAO),
        text_style=ft.TextStyle(size=15, weight=ft.FontWeight.W_600),
        padding=ft.padding.symmetric(horizontal=20, vertical=14),
    )
    return ft.ButtonStyle(**{**padrao, **kw})


def tratar_erros(metodo):
    """Mostra ao usuário os erros esperados (validação e banco) em vez de quebrar."""

    @functools.wraps(metodo)
    def interno(self, *args, **kwargs):
        try:
            return metodo(self, *args, **kwargs)
        except logic.ERROS_ESPERADOS as exc:
            getattr(self, "app", self).notificar(str(exc), erro=True)

    return interno


class TextoMoeda(ft.Text):
    """Texto de valor em reais que sabe se esconder (modo privacidade).

    Atualizar o valor ou a privacidade mexe só neste texto; quem o contém
    decide quando chamar update().
    """

    def __init__(self, app, valor=0.0, prefixo="", tamanho=15, peso=600, cor=COR_TEXTO,
                 espacamento=None, autoajuste=False, **kw):
        estilo = ft.TextStyle(letter_spacing=espacamento) if espacamento is not None else None
        super().__init__(size=tamanho, weight=_PESOS[peso], color=cor, style=estilo, no_wrap=True, **kw)
        self._app = app
        self._valor = valor
        self._prefixo = prefixo
        self._tamanho_base = tamanho
        self._autoajuste = autoajuste
        self.redesenhar()

    def definir(self, valor: float) -> None:
        self._valor = valor
        self.redesenhar()

    def redesenhar(self) -> None:
        self.value = f"{self._prefixo}{self._app.formatar_moeda(self._valor)}"
        if self._autoajuste:  # valores muito grandes encolhem em vez de estourar o card
            self.size = round(self._tamanho_base * min(1.0, 12 / max(len(self.value), 1)), 1)


class Pilula(ft.Container):
    """Botão de filtro em formato de pílula."""

    def __init__(self, rotulo: str, filtro: Optional[str], ao_clicar: Callable):
        super().__init__(
            content=txt(rotulo, 14, 600, COR_SUAVE),
            padding=ft.padding.symmetric(horizontal=16, vertical=9),
            border_radius=20,
            ink=True,
            on_click=lambda e: ao_clicar(self),
        )
        self.filtro = filtro
        self.definir_ativa(False)

    def definir_ativa(self, ativa: bool) -> None:
        self.bgcolor = ft.Colors.PRIMARY_CONTAINER if ativa else COR_REALCE
        self.content.color = ft.Colors.ON_PRIMARY_CONTAINER if ativa else COR_SUAVE


class SeletorMes(ft.Container):
    """‹ Novembro de 2026 ›  (navega pelos meses que têm lançamentos)."""

    def __init__(self, app: "OriaApp"):
        super().__init__(padding=ft.padding.symmetric(horizontal=8, vertical=0))
        self.app = app
        self.btn_anterior = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT_ROUNDED, tooltip="Mês anterior",
            on_click=lambda e: app.mudar_periodo(-1),
        )
        self.btn_proximo = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT_ROUNDED, tooltip="Próximo mês",
            on_click=lambda e: app.mudar_periodo(1),
        )
        self.rotulo = txt("", 17, 700, text_align=ft.TextAlign.CENTER)
        self.content = ft.Row(
            [self.btn_anterior,
             ft.Container(self.rotulo, width=200, alignment=ft.alignment.center),
             self.btn_proximo],
            alignment=ft.MainAxisAlignment.CENTER, spacing=0,
        )
        self.atualizar()

    def atualizar(self) -> None:
        app = self.app
        periodos = app.periodos
        chave = (app.ano, app.mes)
        posicao = periodos.index(chave) if chave in periodos else -1
        self.btn_anterior.disabled = posicao <= 0
        self.btn_proximo.disabled = posicao < 0 or posicao >= len(periodos) - 1
        self.rotulo.value = logic.obter_nome_mes_ano(app.mes, app.ano)
        if self.page:
            self.update()


# ===========================================================================
# Abas
# ===========================================================================

class ViewOria(ft.Column):
    """Base das abas: construída uma vez, rolável, centralizada e com largura limitada."""

    def __init__(self, app: "OriaApp"):
        super().__init__(
            expand=True, spacing=0, visible=False,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.app = app
        self.desatualizada = True
        self._privacidade_aplicada: Optional[bool] = None
        self._moedas_fixas: list[TextoMoeda] = []
        self._moedas_dinamicas: list[TextoMoeda] = []
        self.pagina = ft.Container(
            width=app.largura_pagina,
            padding=ft.padding.only(left=16, right=16, top=8, bottom=28),
        )
        self.controls = [self.pagina]

    # -- ciclo de vida -------------------------------------------------------
    def carregar(self) -> None:
        """Lê os dados e preenche os controles existentes. Não faz update."""
        raise NotImplementedError

    def ao_exibir(self) -> None:
        """Deixa a aba pronta para aparecer: relê os dados só se mudaram e só
        reaplica a privacidade se ela mudou. Não faz update; quem chama atualiza."""
        if self.desatualizada:
            self.carregar()
            self.desatualizada = False
            self._privacidade_aplicada = self.app.privacidade
        elif self._privacidade_aplicada != self.app.privacidade:
            self.reaplicar_privacidade()

    def recarregar(self) -> None:
        """Mantém a aba visível em dia: relê e atualiza só ela."""
        self.desatualizada = True
        self.ao_exibir()
        if self.page:
            self.update()

    def reaplicar_privacidade(self) -> None:
        for moeda in self._moedas_fixas + self._moedas_dinamicas:
            moeda.redesenhar()
        self._privacidade_aplicada = self.app.privacidade

    def definir_largura(self, largura: float) -> None:
        self.pagina.width = largura

    # -- utilidades ------------------------------------------------------------
    def criar_moeda(self, valor=0.0, dinamica=False, **estilo) -> TextoMoeda:
        moeda = TextoMoeda(self.app, valor, **estilo)
        (self._moedas_dinamicas if dinamica else self._moedas_fixas).append(moeda)
        return moeda

    def construir_linha(self, item: logic.ItemExtrato, mostrar_dia=False,
                        ao_excluir=None, ao_editar=None) -> ft.Control:
        """Uma linha de lançamento. Usada pelo Início (agendadas) e pelo Extrato."""
        if item.categoria == "Entrada":
            cor, icone, prefixo, cor_valor = COR_ENTRADA, ft.Icons.ARROW_UPWARD_ROUNDED, "+ ", COR_ENTRADA
        elif item.categoria == "Gasto":
            cor, icone, prefixo, cor_valor = COR_GASTO, ft.Icons.ARROW_DOWNWARD_ROUNDED, "− ", COR_TEXTO
        else:
            cor, icone, prefixo, cor_valor = COR_COFRE, ft.Icons.SAVINGS_OUTLINED, "", COR_COFRE

        detalhe = item.local or item.categoria
        if mostrar_dia:
            detalhe += f" · {logic.rotulo_do_dia(item.data_iso)}"
        elif not item.efetivada:
            detalhe += " · agendada"

        direita = [self.criar_moeda(item.valor, dinamica=True, prefixo=prefixo, tamanho=15, peso=700, cor=cor_valor)]
        if ao_editar:
            direita.append(ft.IconButton(
                icon=ft.Icons.EDIT_OUTLINED, icon_size=20, icon_color=COR_SUAVE,
                tooltip="Editar lançamento", on_click=lambda e: ao_editar(item),
            ))
        if ao_excluir:
            direita.append(ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE_ROUNDED, icon_size=20, icon_color=COR_SUAVE,
                tooltip="Excluir lançamento", on_click=lambda e: ao_excluir(item),
            ))

        return ft.Container(
            padding=ft.padding.symmetric(vertical=10),
            content=ft.Row(
                [
                    ft.Container(
                        width=40, height=40, border_radius=20, alignment=ft.alignment.center,
                        bgcolor=ft.Colors.with_opacity(0.12, cor),
                        content=ft.Icon(icone, color=cor, size=20),
                    ),
                    ft.Column(
                        [txt(item.descricao, 15, 600, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                         txt(detalhe, 13, 400, COR_SUAVE, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)],
                        spacing=2, expand=True,
                    ),
                    ft.Row(direita, spacing=0, tight=True),
                ],
                spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )


class InicioView(ViewOria):
    def __init__(self, app):
        super().__init__(app)
        self.valor_saldo = self.criar_moeda(
            tamanho=38, peso=700, cor=BRANCO, espacamento=-1, autoajuste=True)
        self.explicacao = txt("", 13, 400, BRANCO_SUAVE)
        self.m_entradas = self.criar_moeda(tamanho=15, peso=600, cor=BRANCO)
        self.m_gastos = self.criar_moeda(tamanho=15, peso=600, cor=BRANCO)
        self.m_investido = self.criar_moeda(tamanho=15, peso=600, cor=BRANCO)

        def linha_resumo(rotulo, cor_ponto, valor):
            return ft.Row(
                [ft.Container(width=10, height=10, border_radius=5, bgcolor=cor_ponto),
                 txt(rotulo, 15, 500, BRANCO_SUAVE, expand=True), valor],
                spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

        hero = criar_hero(
            ft.Column(
                [
                    txt("Saldo livre", 14, 500, BRANCO_SUAVE),
                    self.valor_saldo,
                    self.explicacao,
                    ft.Divider(height=28, thickness=1, color=BRANCO_LINHA),
                    linha_resumo("Entradas", PONTO_ENTRADA, self.m_entradas),
                    ft.Container(height=2),
                    linha_resumo("Gastos", PONTO_GASTO, self.m_gastos),
                    ft.Container(height=2),
                    linha_resumo("Investido", PONTO_COFRE, self.m_investido),
                ],
                spacing=4,
            ),
            col={"xs": 12, "lg": 7},
        )

        self.contagem = txt("", 13, 600, ft.Colors.ON_PRIMARY_CONTAINER)
        self.selo_contagem = ft.Container(
            content=self.contagem, bgcolor=ft.Colors.PRIMARY_CONTAINER, border_radius=12,
            padding=ft.padding.symmetric(horizontal=10, vertical=3),
        )
        self.lista_agendadas = ft.Column(spacing=0)
        agendadas = superficie(
            ft.Column(
                [
                    ft.Row([txt("Agendadas", 18, 700), self.selo_contagem],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    txt("Entram no saldo quando a data chega.", 13, 400, COR_SUAVE),
                    ft.Container(height=6),
                    self.lista_agendadas,
                ],
                spacing=2,
            ),
            col={"xs": 12, "lg": 5},
        )
        self.pagina.content = ft.ResponsiveRow([hero, agendadas], spacing=16, run_spacing=16)

    def carregar(self) -> None:
        app = self.app
        resumo = logic.calcular_resumo_mes(app.mes, app.ano)
        nome_mes = logic.MESES_PT_BR[app.mes].lower()
        self.valor_saldo.definir(resumo.saldo_livre)
        self.explicacao.value = (
            f"Gastos e investimentos passaram das entradas de {nome_mes}."
            if resumo.saldo_livre < 0
            else f"Entradas menos gastos e investimentos de {nome_mes}."
        )
        self.m_entradas.definir(resumo.entradas)
        self.m_gastos.definir(resumo.gastos)
        self.m_investido.definir(resumo.investido)

        agendadas = logic.listar_agendadas(app.mes, app.ano)
        self._moedas_dinamicas = []
        linhas: list[ft.Control] = []
        for posicao, item in enumerate(agendadas):
            if posicao:
                linhas.append(ft.Divider(height=1, thickness=1, color=COR_LINHA))
            linhas.append(self.construir_linha(item, mostrar_dia=True))
        if not linhas:
            linhas.append(ft.Container(
                padding=ft.padding.symmetric(vertical=18),
                content=txt(f"Nada agendado em {nome_mes}.", 14, 400, COR_SUAVE),
            ))
        self.lista_agendadas.controls = linhas
        self.contagem.value = str(len(agendadas))
        self.selo_contagem.visible = bool(agendadas)


class RegistrarView(ViewOria):
    def __init__(self, app):
        super().__init__(app)
        self.categoria = "Entrada"
        self.data_escolhida = date.today()
        self.locais: list[logic.LocalDisponivel] = []
        self.locais_por_chave: dict[str, logic.LocalDisponivel] = {}
        self._local_preferido: tuple[str, str] | None = None
        self._id_editando: Optional[int] = None

        self.seletor_tipo = ft.SegmentedButton(
            selected={"Entrada"},
            allow_multiple_selection=False,
            allow_empty_selection=False,
            show_selected_icon=False,
            on_change=self._ao_mudar_tipo,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=R_CAMPO),
                text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_600),
            ),
            segments=[ft.Segment(value=c, label=ft.Text(c)) for c in logic.CATEGORIAS],
        )
        self.tf_valor = campo(
            label="Valor", prefix_text="R$ ", text_size=26,
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.InputFilter(regex_string=r"^[0-9.,]*$"),
        )
        self.tf_descricao = campo(label="Descrição", max_length=60)

        self.texto_data = txt("", 16, 600)
        self.campo_data = ft.Container(
            bgcolor=COR_REALCE, border_radius=R_CAMPO, ink=True,
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            on_click=self._abrir_calendario,
            content=ft.Row(
                [ft.Icon(ft.Icons.CALENDAR_MONTH_ROUNDED, color=COR_SUAVE),
                 ft.Column([txt("Data", 12, 500, COR_SUAVE), self.texto_data], spacing=2, expand=True)],
                spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        self.dica_data = txt("", 13, 400, COR_SUAVE)
        self.seletor_data = ft.DatePicker(
            first_date=datetime(2020, 1, 1), last_date=datetime(2035, 12, 31),
            on_change=self._ao_escolher_data,
        )

        # Só aparece para "Investimento": onde o dinheiro vai ser guardado.
        self.dd_local = lista_suspensa(label="Onde guardar", on_change=self._ao_mudar_local)
        self.tf_instituicao = campo(label="Instituição", hint_text="Ex.: Nubank, XP, Inter", max_length=40)
        self.dd_tipo = lista_suspensa(
            label="Tipo de investimento",
            options=[ft.dropdown.Option(t) for t in logic.TIPOS_INVESTIMENTO],
        )
        self.bloco_novo_local = ft.Column([self.tf_instituicao, self.dd_tipo], spacing=12,
                                          horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        self.bloco_investimento = ft.Column(
            [self.dd_local, self.bloco_novo_local], spacing=12, visible=False,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        self.botao_salvar = ft.FilledButton(
            text="Salvar lançamento", on_click=self.salvar, height=56, style=estilo_botao())
        self.btn_cancelar_edicao = ft.TextButton(
            "Cancelar edição", visible=False,
            on_click=lambda e: self.cancelar_edicao(),
        )
        self.titulo_form = txt("Novo lançamento", 24, 700, espacamento=-0.3)

        self.pagina.content = ft.ResponsiveRow(
            [ft.Container(
                col={"xs": 12, "md": 10, "lg": 8},
                content=ft.Column(
                    [
                        self.titulo_form,
                        ft.Container(height=4),
                        self.seletor_tipo,
                        self.tf_valor,
                        self.tf_descricao,
                        ft.Column([self.campo_data, self.dica_data], spacing=8),
                        self.bloco_investimento,
                        ft.Container(height=4),
                        self.botao_salvar,
                        ft.Row([self.btn_cancelar_edicao],
                               alignment=ft.MainAxisAlignment.CENTER),
                    ],
                    spacing=14, horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
            )],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self._aplicar_tipo()
        self._atualizar_data()

    # -- estado visual -----------------------------------------------------------
    def _aplicar_tipo(self) -> None:
        exemplos = {"Entrada": "Ex.: Salário, freelance", "Gasto": "Ex.: Mercado, aluguel",
                    "Investimento": "Ex.: Aporte do mês"}
        self.tf_descricao.hint_text = exemplos[self.categoria]
        self.bloco_investimento.visible = self.categoria == "Investimento"
        self._atualizar_locais_visiveis()
        self._atualizar_dica()

    def _atualizar_locais_visiveis(self) -> None:
        self.dd_local.visible = bool(self.locais)
        self.bloco_novo_local.visible = (not self.locais) or self.dd_local.value == _NOVO_LOCAL

    def _atualizar_dica(self) -> None:
        acao = {"Entrada": "entra no saldo", "Gasto": "sai do saldo",
                "Investimento": "sai do saldo e vai para o Cofre"}[self.categoria]
        if self.data_escolhida <= date.today():
            self.dica_data.value = f"{acao.capitalize()} agora."
        else:
            self.dica_data.value = f"Fica agendado: {acao} em {self.data_escolhida:%d/%m/%Y}."

    def _atualizar_data(self) -> None:
        iso = self.data_escolhida.isoformat()
        rotulo = logic.rotulo_do_dia(iso)
        data_br = logic.formatar_data_br(iso)
        self.texto_data.value = f"{rotulo}, {data_br}" if rotulo in ("Hoje", "Ontem", "Amanhã") else data_br
        self._atualizar_dica()

    def carregar(self) -> None:
        """Atualiza só as opções de local (um aporte novo cria um local); o que o
        usuário já digitou no formulário não é tocado."""
        self.locais = logic.listar_locais_disponiveis()
        self.locais_por_chave = {l.rotulo: l for l in self.locais}
        opcoes = [ft.dropdown.Option(key=l.rotulo, text=l.rotulo) for l in self.locais]
        opcoes.append(ft.dropdown.Option(key=_NOVO_LOCAL, text="+ Novo local"))
        self.dd_local.options = opcoes
        chaves_validas = {o.key for o in opcoes}

        if self._local_preferido is not None:
            inst, tipo = self._local_preferido
            self._local_preferido = None
            chave = next(
                (k for k, l in self.locais_por_chave.items()
                 if l.instituicao.casefold() == inst.casefold()
                 and l.tipo.casefold() == tipo.casefold()),
                None,
            )
            self.dd_local.value = chave or (next(iter(self.locais_por_chave), None) or _NOVO_LOCAL)
        elif self.dd_local.value not in chaves_validas:
            self.dd_local.value = next(iter(self.locais_por_chave), None) or _NOVO_LOCAL

        self._atualizar_locais_visiveis()

    def preselecionar(self, categoria: str) -> None:
        """Usado pelo Cofre vazio: abre o formulário já em 'Investimento'."""
        self.categoria = categoria
        self.seletor_tipo.selected = {categoria}
        self._aplicar_tipo()

    # -- eventos -------------------------------------------------------------------
    def _ao_mudar_tipo(self, e) -> None:
        escolhido = e.control.selected
        if escolhido:
            self.categoria = next(iter(escolhido))
            self._aplicar_tipo()
            self.update()

    def _ao_mudar_local(self, e) -> None:
        self._atualizar_locais_visiveis()
        self.bloco_novo_local.update()

    def _abrir_calendario(self, e) -> None:
        d = self.data_escolhida
        self.seletor_data.value = datetime(d.year, d.month, d.day)
        self.app.page.open(self.seletor_data)

    def _ao_escolher_data(self, e) -> None:
        if e.control.value:
            self.data_escolhida = e.control.value.date()
            self._atualizar_data()
            self.campo_data.update()
            self.dica_data.update()

    def _local_escolhido(self) -> tuple[str, str]:
        if self.locais_por_chave and self.dd_local.value not in (None, _NOVO_LOCAL):
            local = self.locais_por_chave[self.dd_local.value]
            return local.instituicao, local.tipo
        return self.tf_instituicao.value or "", self.dd_tipo.value or ""

    @tratar_erros
    def salvar(self, e=None) -> None:
        if self.categoria == "Investimento":
            instituicao, tipo = self._local_escolhido()
            if instituicao:  # preserva o local recém-usado para a próxima carga
                self._local_preferido = (instituicao, tipo)
        else:
            instituicao, tipo = "", ""
        data_lancamento = self.data_escolhida

        if self._id_editando is not None:
            efetivada = logic.editar_transacao(
                self._id_editando, self.tf_descricao.value, self.tf_valor.value,
                self.categoria, data_lancamento, instituicao, tipo,
            )
            aviso = "Lançamento atualizado." if efetivada else f"Lançamento agendado para {data_lancamento:%d/%m/%Y}."
            self._limpar_modo_edicao()
        else:
            efetivada = logic.registrar_transacao(
                self.tf_descricao.value, self.tf_valor.value, self.categoria,
                data_lancamento, instituicao, tipo,
            )
            if not efetivada:
                aviso = f"Lançamento agendado para {data_lancamento:%d/%m/%Y}."
            elif (data_lancamento.year, data_lancamento.month) != (self.app.ano, self.app.mes):
                aviso = f"Lançamento salvo em {logic.obter_nome_mes_ano(data_lancamento.month, data_lancamento.year)}."
            else:
                aviso = "Lançamento salvo."

        self.tf_valor.value = ""
        self.tf_descricao.value = ""
        self.tf_instituicao.value = ""
        self.data_escolhida = date.today()
        self._atualizar_data()

        self.app.notificar(aviso)
        self.app.dados_alterados()  # atualiza as outras abas e relê os locais deste formulário

    def _limpar_modo_edicao(self) -> None:
        self._id_editando = None
        self.titulo_form.value = "Novo lançamento"
        self.botao_salvar.text = "Salvar lançamento"
        self.btn_cancelar_edicao.visible = False

    def cancelar_edicao(self) -> None:
        self._limpar_modo_edicao()
        self.tf_valor.value = ""
        self.tf_descricao.value = ""
        self.tf_instituicao.value = ""
        self.data_escolhida = date.today()
        self.categoria = "Entrada"
        self.seletor_tipo.selected = {"Entrada"}
        self._aplicar_tipo()
        self._atualizar_data()
        self.update()

    def editar(self, item: logic.ItemExtrato) -> None:
        """Preenche o formulário com os dados do item e entra no modo de edição."""
        self._id_editando = item.id
        self.categoria = item.categoria
        self.seletor_tipo.selected = {item.categoria}
        self.tf_descricao.value = item.descricao
        # Converte float para formato BR que converter_valor() aceita
        self.tf_valor.value = f"{item.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        self.data_escolhida = date.fromisoformat(item.data_iso)
        if item.categoria == "Investimento" and item.instituicao:
            self._local_preferido = (item.instituicao, item.tipo_investimento or "")
        self.titulo_form.value = "Editar lançamento"
        self.botao_salvar.text = "Atualizar lançamento"
        self.btn_cancelar_edicao.visible = True
        self._aplicar_tipo()
        self._atualizar_data()


class ExtratoView(ViewOria):
    def __init__(self, app):
        super().__init__(app)
        self.filtro: Optional[str] = None
        self.itens: list[logic.ItemExtrato] = []
        self.pilulas = [
            Pilula("Tudo", None, self._ao_filtrar),
            Pilula("Entradas", "Entrada", self._ao_filtrar),
            Pilula("Gastos", "Gasto", self._ao_filtrar),
            Pilula("Investimentos", "Investimento", self._ao_filtrar),
        ]
        self.pilulas[0].definir_ativa(True)
        self.linha_pilulas = ft.Row(self.pilulas, wrap=True, spacing=8, run_spacing=8)
        self.lista = ft.Column(spacing=0)
        self.pagina.content = ft.ResponsiveRow(
            [ft.Container(
                col={"xs": 12, "lg": 10, "xl": 9},
                content=ft.Column(
                    [txt("Extrato", 24, 700, espacamento=-0.3), self.linha_pilulas,
                     superficie(self.lista, padding=ft.padding.symmetric(horizontal=20, vertical=12))],
                    spacing=14,
                ),
            )],
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def carregar(self) -> None:
        self.itens = logic.listar_extrato(self.app.mes, self.app.ano)
        self._montar_lista()

    def _montar_lista(self) -> None:
        """Reconstrói só a lista (não a tela) a partir dos dados já lidos."""
        visiveis = [i for i in self.itens if self.filtro is None or i.categoria == self.filtro]
        self._moedas_dinamicas = []
        controles: list[ft.Control] = []

        dia_atual = None
        for item in visiveis:
            if item.data_iso != dia_atual:
                dia_atual = item.data_iso
                controles.append(ft.Container(
                    padding=ft.padding.only(top=14 if controles else 4, bottom=2),
                    content=txt(logic.rotulo_do_dia(item.data_iso), 13, 600, COR_SUAVE),
                ))
            elif controles:
                controles.append(ft.Divider(height=1, thickness=1, color=COR_LINHA))
            controles.append(self.construir_linha(
                item, ao_editar=self._pedir_edicao, ao_excluir=self._pedir_exclusao))

        if not controles:
            nome = logic.obter_nome_mes_ano(self.app.mes, self.app.ano)
            controles.append(ft.Container(
                padding=ft.padding.symmetric(vertical=28),
                alignment=ft.alignment.center,
                content=ft.Column(
                    [ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=40, color=COR_SUAVE),
                     txt(f"Nenhum lançamento em {nome}.", 16, 600, text_align=ft.TextAlign.CENTER),
                     txt("Use a aba Registrar para adicionar o primeiro.", 14, 400, COR_SUAVE,
                         text_align=ft.TextAlign.CENTER)],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8,
                ),
            ))
        self.lista.controls = controles

    def _ao_filtrar(self, pilula: Pilula) -> None:
        self.filtro = pilula.filtro
        for p in self.pilulas:
            p.definir_ativa(p is pilula)
        self._montar_lista()
        self.linha_pilulas.update()
        self.lista.update()

    @tratar_erros
    def _pedir_edicao(self, item: logic.ItemExtrato) -> None:
        self.app.ir_para_editar(item)

    @tratar_erros
    def _pedir_exclusao(self, item: logic.ItemExtrato) -> None:
        aviso = " O valor volta a sair do Cofre." if item.categoria == "Investimento" and item.efetivada else ""
        self.app.confirmar(
            "Excluir lançamento?",
            f"“{item.descricao}” ({self.app.formatar_moeda(item.valor)}) será removido.{aviso}",
            "Excluir", lambda: self._excluir(item.id), destrutivo=True,
        )

    @tratar_erros
    def _excluir(self, id_transacao: int) -> None:
        logic.excluir_transacao(id_transacao)
        self.app.notificar("Lançamento excluído.")
        self.app.dados_alterados()


class CofreView(ViewOria):
    def __init__(self, app):
        super().__init__(app)
        self.total = self.criar_moeda(tamanho=38, peso=700, cor=BRANCO, espacamento=-1, autoajuste=True)
        self.legenda_total = txt("", 13, 400, BRANCO_SUAVE)
        hero = criar_hero(
            ft.Column(
                [
                    ft.Row(
                        [ft.Container(
                            width=36, height=36, border_radius=18, alignment=ft.alignment.center,
                            bgcolor=ft.Colors.with_opacity(0.18, PONTO_COFRE),
                            content=ft.Icon(ft.Icons.SAVINGS_OUTLINED, color=PONTO_COFRE, size=20)),
                         txt("Patrimônio total guardado", 14, 500, BRANCO_SUAVE)],
                        spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=6),
                    self.total,
                    self.legenda_total,
                ],
                spacing=4,
            ),
            col={"xs": 12},
        )
        self.grade = ft.ResponsiveRow(spacing=12, run_spacing=12)
        self.vazio = superficie(
            ft.Column(
                [ft.Icon(ft.Icons.SAVINGS_OUTLINED, size=40, color=COR_COFRE),
                 txt("Seu Cofre ainda está vazio.", 17, 700, text_align=ft.TextAlign.CENTER),
                 txt("Registre um lançamento do tipo Investimento e ele aparece aqui, por instituição.",
                     14, 400, COR_SUAVE, text_align=ft.TextAlign.CENTER),
                 ft.Container(height=4),
                 ft.FilledTonalButton(text="Registrar investimento", icon=ft.Icons.ADD_ROUNDED,
                                      style=estilo_botao(),
                                      on_click=lambda e: app.ir_para_registrar("Investimento"))],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8,
            ),
            padding=28, col={"xs": 12}, visible=False,
        )
        self.titulo_locais = txt("Onde está guardado", 18, 700)
        self.pagina.content = ft.Column(
            [txt("Cofre", 24, 700, espacamento=-0.3),
             ft.ResponsiveRow([hero]),
             ft.Container(height=4),
             self.titulo_locais,
             self.grade,
             ft.ResponsiveRow([self.vazio])],
            spacing=14,
        )

    def carregar(self) -> None:
        cofre = logic.resumo_cofre()
        self.total.definir(cofre.total)
        quantidade = len(cofre.locais)
        self.legenda_total.value = (
            "Nenhum investimento registrado ainda." if not quantidade
            else "Distribuído em 1 local." if quantidade == 1
            else f"Distribuído em {quantidade} locais."
        )
        self._moedas_dinamicas = []
        cartoes = []
        for local in cofre.locais:
            valor = self.criar_moeda(local.valor, dinamica=True, tamanho=22, peso=700)
            parte = "menos de 1%" if 0 < local.percentual < 0.01 else f"{local.percentual * 100:.0f}%"
            cartoes.append(superficie(
                ft.Column(
                    [
                        ft.Row(
                            [txt(local.instituicao, 16, 700, expand=True, max_lines=1,
                                 overflow=ft.TextOverflow.ELLIPSIS),
                             ft.Container(
                                 content=txt(local.tipo, 12, 600, ft.Colors.ON_TERTIARY_CONTAINER),
                                 bgcolor=ft.Colors.TERTIARY_CONTAINER, border_radius=10,
                                 padding=ft.padding.symmetric(horizontal=10, vertical=3))],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=8,
                        ),
                        valor,
                        ft.ProgressBar(value=local.percentual, color=COR_COFRE, bgcolor=COR_REALCE,
                                       bar_height=8, border_radius=4),
                        txt(f"{parte} do Cofre", 13, 400, COR_SUAVE),
                    ],
                    spacing=10,
                ),
                col={"xs": 12, "md": 6},
            ))
        self.grade.controls = cartoes
        self.grade.visible = self.titulo_locais.visible = bool(cartoes)
        self.vazio.visible = not cartoes


class AjustesView(ViewOria):
    def __init__(self, app):
        super().__init__(app)
        self.chave_tema = ft.Switch(on_change=self._ao_mudar_tema)
        self.status_pin = txt("", 13, 400, COR_SUAVE)
        self.btn_pin = ft.FilledTonalButton(text="Cadastrar PIN", icon=ft.Icons.PIN_OUTLINED,
                                            style=estilo_botao(), on_click=self._abrir_dialogo_pin)
        self.btn_remover_pin = ft.TextButton(
            text="Remover PIN", visible=False, on_click=self._abrir_dialogo_remover_pin,
            style=estilo_botao(color=ft.Colors.ERROR))

        aparencia = superficie(ft.Row(
            [ft.Icon(ft.Icons.DARK_MODE_OUTLINED, color=COR_MARCA),
             ft.Column([txt("Tema escuro", 16, 600), txt("Cores escuras para usar à noite.", 13, 400, COR_SUAVE)],
                       spacing=2, expand=True),
             self.chave_tema],
            spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ), col={"xs": 12, "md": 6})

        seguranca = superficie(ft.Column(
            [txt("PIN de acesso", 16, 600), self.status_pin, ft.Container(height=4),
             ft.Row([self.btn_pin, self.btn_remover_pin], wrap=True, spacing=8, run_spacing=8)],
            spacing=2,
        ), col={"xs": 12, "md": 6})

        backup = superficie(ft.Column(
            [txt("Backup dos dados", 16, 600),
             txt("O arquivo reúne seus lançamentos, o Cofre e o PIN. Guarde-o em um lugar seguro.",
                 13, 400, COR_SUAVE),
             ft.Container(height=4),
             ft.Row(
                 [ft.FilledTonalButton(text="Exportar dados", icon=ft.Icons.FILE_UPLOAD_OUTLINED,
                                       style=estilo_botao(), on_click=lambda e: app.exportar_dados()),
                  ft.OutlinedButton(text="Importar dados", icon=ft.Icons.FILE_DOWNLOAD_OUTLINED,
                                    style=estilo_botao(), on_click=lambda e: app.importar_dados())],
                 wrap=True, spacing=8, run_spacing=8),
             ],
            spacing=2,
        ), col={"xs": 12, "md": 6})

        self.pagina.content = ft.ResponsiveRow(
            [ft.Container(
                col={"xs": 12, "lg": 11},
                content=ft.Column(
                    [txt("Configurações", 24, 700, espacamento=-0.3),
                     ft.ResponsiveRow([aparencia, seguranca, backup], spacing=14, run_spacing=14),
                     ft.Container(height=4),
                     txt("O Oria guarda tudo somente neste aparelho.", 13, 400, COR_SUAVE)],
                    spacing=14,
                ),
            )],
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def carregar(self) -> None:
        self.chave_tema.value = self.app.tema == "escuro"
        tamanho = logic.tamanho_do_pin()
        if tamanho:
            self.status_pin.value = f"PIN ativo, com {tamanho} dígitos. O Oria pede o PIN ao abrir."
            self.btn_pin.text = "Alterar PIN"
        else:
            self.status_pin.value = "Sem PIN, o Oria abre direto."
            self.btn_pin.text = "Cadastrar PIN"
        self.btn_remover_pin.visible = bool(tamanho)

    @tratar_erros
    def _ao_mudar_tema(self, e) -> None:
        self.app.definir_tema("escuro" if e.control.value else "claro")

    # -- diálogos de PIN -----------------------------------------------------------
    @staticmethod
    def _campo_pin(rotulo: str) -> ft.TextField:
        return campo(
            label=rotulo, password=True, can_reveal_password=True, max_length=logic.PIN_MAX,
            keyboard_type=ft.KeyboardType.NUMBER, input_filter=ft.NumbersOnlyInputFilter(),
        )

    def _abrir_dialogo_pin(self, e=None) -> None:
        app = self.app
        tem_pin = logic.pin_configurado()
        tf_atual = self._campo_pin("PIN atual") if tem_pin else None
        tf_novo = self._campo_pin(f"Novo PIN ({logic.PIN_MIN} a {logic.PIN_MAX} números)")
        tf_confirmacao = self._campo_pin("Confirmar novo PIN")
        erro = txt("", 13, 500, ft.Colors.ERROR)

        def salvar(_):
            try:
                logic.definir_pin(tf_novo.value, tf_confirmacao.value, tf_atual.value if tf_atual else None)
            except logic.ERROS_ESPERADOS as exc:
                erro.value = str(exc)
                erro.update()
                return
            app.page.close(dialogo)
            app.notificar("PIN salvo.")
            app.seguranca_alterada()

        campos = [c for c in (tf_atual, tf_novo, tf_confirmacao) if c is not None]
        dialogo = app.criar_dialogo(
            "Alterar PIN" if tem_pin else "Cadastrar PIN",
            ft.Column([*campos, erro], tight=True, spacing=12, width=320),
            [ft.TextButton("Cancelar", on_click=lambda _: app.page.close(dialogo)),
             ft.FilledButton("Salvar PIN", on_click=salvar, style=estilo_botao())],
        )
        app.page.open(dialogo)

    def _abrir_dialogo_remover_pin(self, e=None) -> None:
        app = self.app
        tf_atual = self._campo_pin("PIN atual")
        erro = txt("", 13, 500, ft.Colors.ERROR)

        def remover(_):
            try:
                logic.remover_pin(tf_atual.value)
            except logic.ERROS_ESPERADOS as exc:
                erro.value = str(exc)
                erro.update()
                return
            app.page.close(dialogo)
            app.notificar("PIN removido.")
            app.seguranca_alterada()

        dialogo = app.criar_dialogo(
            "Remover PIN",
            ft.Column([txt("Depois disso o Oria abre sem pedir senha.", 14, 400, COR_SUAVE), tf_atual, erro],
                      tight=True, spacing=12, width=320),
            [ft.TextButton("Cancelar", on_click=lambda _: app.page.close(dialogo)),
             ft.FilledButton("Remover PIN", on_click=remover,
                             style=estilo_botao(bgcolor=ft.Colors.ERROR, color=ft.Colors.ON_ERROR))],
        )
        app.page.open(dialogo)


# ===========================================================================
# Tela de bloqueio
# ===========================================================================

class TelaBloqueio(ft.Container):
    def __init__(self, app: "OriaApp"):
        super().__init__(
            expand=True, visible=False, padding=24,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center, end=ft.alignment.bottom_center, colors=[HERO_DE, HERO_PARA]),
        )
        self.app = app
        self.digitos = ""
        self.tamanho = 4
        self._validando = False
        self.pontos = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=16)
        self.mensagem = txt("", 14, 500, BRANCO_SUAVE, text_align=ft.TextAlign.CENTER)

        def tecla(rotulo: Optional[str] = None, icone=None, ao_clicar=None) -> ft.Container:
            if rotulo is None and icone is None:
                return ft.Container(width=76, height=76)
            conteudo = txt(rotulo, 28, 500, BRANCO) if rotulo else ft.Icon(icone, color=BRANCO, size=26)
            return ft.Container(
                width=76, height=76, border_radius=38, alignment=ft.alignment.center, ink=True,
                bgcolor=ft.Colors.with_opacity(0.14, ft.Colors.WHITE), content=conteudo,
                on_click=ao_clicar if ao_clicar else (lambda e, d=rotulo: self.digitar(d)),
            )

        linhas = [[tecla(str(n)) for n in range(inicio, inicio + 3)] for inicio in (1, 4, 7)]
        linhas.append([tecla(), tecla("0"), tecla(icone=ft.Icons.BACKSPACE_OUTLINED, ao_clicar=lambda e: self.apagar())])
        teclado = ft.Column(
            [ft.Row(l, alignment=ft.MainAxisAlignment.CENTER, spacing=16) for l in linhas],
            spacing=16, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.content = ft.Column(
            [txt("Oria", 34, 800, BRANCO, espacamento=-1),
             txt("Digite seu PIN", 17, 600, BRANCO),
             ft.Container(height=4), self.pontos, self.mensagem, ft.Container(height=8), teclado],
            alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12, expand=True, scroll=ft.ScrollMode.AUTO,
        )
        self.preparar()

    def preparar(self) -> None:
        """Zera a digitação e redesenha os pontos para o tamanho do PIN atual (sem update)."""
        self.tamanho = logic.tamanho_do_pin() or 4
        self.digitos = ""
        self.mensagem.value = ""
        self.pontos.controls = [
            ft.Container(width=14, height=14, border_radius=7) for _ in range(self.tamanho)]
        self._pintar_pontos()

    def _pintar_pontos(self) -> None:
        for posicao, ponto in enumerate(self.pontos.controls):
            ponto.bgcolor = BRANCO if posicao < len(self.digitos) else ft.Colors.with_opacity(0.28, ft.Colors.WHITE)

    def digitar(self, digito: str) -> None:
        if self._validando or len(self.digitos) >= self.tamanho:
            return
        self.digitos += digito
        self.mensagem.value = ""
        self._pintar_pontos()
        self.pontos.update()
        self.mensagem.update()
        if len(self.digitos) == self.tamanho:
            self._validar()

    def apagar(self) -> None:
        if self._validando or not self.digitos:
            return
        self.digitos = self.digitos[:-1]
        self._pintar_pontos()
        self.pontos.update()

    def _validar(self) -> None:
        self._validando = True
        try:
            correto = logic.validar_pin(self.digitos)
        except logic.ERROS_ESPERADOS as exc:
            correto = False
            self.mensagem.value = str(exc)
        finally:
            self._validando = False
        self.digitos = ""
        if correto:
            self.app.liberar()
            return
        if not self.mensagem.value:
            self.mensagem.value = "PIN incorreto. Tente de novo."
        self._pintar_pontos()
        self.pontos.update()
        self.mensagem.update()


# ===========================================================================
# Aplicativo
# ===========================================================================

class OriaApp:
    """Dono do estado da interface e das ações que atravessam várias abas."""

    # Ordem fixa: índice 0=Início, 1=Registrar, 2=Extrato, 3=Cofre, 4=Ajustes
    _CLASSES_VIEWS = [InicioView, RegistrarView, ExtratoView, CofreView, AjustesView]

    # -- propriedades de acesso nomeado (acionam lazy loading automaticamente) ---------
    @property
    def inicio(self) -> "InicioView":
        """Sempre pré-carregada (índice 0)."""
        return self._cache_views[0]

    @property
    def registrar(self) -> "RegistrarView":
        return self._obter_aba(1)

    @property
    def extrato(self) -> "ExtratoView":
        return self._obter_aba(2)

    @property
    def cofre(self) -> "CofreView":
        return self._obter_aba(3)

    @property
    def ajustes(self) -> "AjustesView":
        return self._obter_aba(4)

    def __init__(self, page: ft.Page):
        self.page = page
        hoje = date.today()
        self.mes, self.ano = hoje.month, hoje.year
        self.privacidade = False
        self.tema = "claro"
        self.periodos: list[tuple[int, int]] = []
        self.indice_atual = 0
        self.bloqueado = False
        self.largura_pagina = LARGURA_MAXIMA_CONTEUDO
        self._layout_aplicado: Optional[tuple[bool, int]] = None
        self._acao_arquivo: Optional[str] = None
        self._historico: list[int] = []       # pilha de índices de abas visitadas
        self._navegando_back: bool = False    # flag: evita duplo push ao voltar
        self._cache_views: list = [None] * 5  # None = view ainda não instanciada

    # -- inicialização ---------------------------------------------------------------
    def iniciar(self) -> None:
        page = self.page
        logic.inicializar()  # cria o banco e efetiva o que já venceu (gatilho por tempo)
        self.tema = logic.obter_tema()
        self._sincronizar_periodos()

        page.title = "Oria"
        page.padding = 0
        page.window.width = 400
        page.window.height = 700
        page.window.min_width = 340
        page.window.min_height = 560
        page.theme = criar_tema(escuro=False)
        page.dark_theme = criar_tema(escuro=True)
        page.locale_configuration = ft.LocaleConfiguration(
            supported_locales=[ft.Locale("pt", "BR")], current_locale=ft.Locale("pt", "BR"))
        self._aplicar_tema()

        self._montar_interface()
        self._ajustar_layout(atualizar=False)

        if logic.pin_configurado():
            self.bloqueado = True
            self.conteudo.visible = False
            self.tela_bloqueio.preparar()
            self.tela_bloqueio.visible = True
        else:
            self.mostrar_aba(0, atualizar=False)

        page.on_resized = lambda e: self._ajustar_layout()
        page.on_keyboard_event = self._ao_tecla
        page.on_route_change = self._ao_mudar_rota
        page.on_view_pop = self._ao_voltar
        page.views.clear()
        page.views.append(self._visao_principal)
        page.update()

    def _montar_interface(self) -> None:
        self.seletor_arquivos = ft.FilePicker(on_result=self._ao_resultado_arquivo)
        self.page.overlay.append(self.seletor_arquivos)

        inicio = InicioView(self)              # única view construída no cold start
        inicio.visible = True
        self._cache_views[0] = inicio

        rotulos = [
            ("Início", ft.Icons.HOME_OUTLINED, ft.Icons.HOME_ROUNDED),
            ("Registrar", ft.Icons.ADD_CIRCLE_OUTLINE, ft.Icons.ADD_CIRCLE),
            ("Extrato", ft.Icons.RECEIPT_LONG_OUTLINED, ft.Icons.RECEIPT_LONG_ROUNDED),
            ("Cofre", ft.Icons.SAVINGS_OUTLINED, ft.Icons.SAVINGS_ROUNDED),
            ("Ajustes", ft.Icons.SETTINGS_OUTLINED, ft.Icons.SETTINGS_ROUNDED),
        ]
        self.barra = ft.NavigationBar(
            selected_index=0, bgcolor=COR_CARTAO, elevation=0, height=72,
            indicator_color=ft.Colors.SECONDARY_CONTAINER,
            label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
            on_change=lambda e: self.mostrar_aba(e.control.selected_index),
            destinations=[ft.NavigationBarDestination(icon=i, selected_icon=s, label=r) for r, i, s in rotulos],
        )
        self.menu_lateral = ft.NavigationRail(
            selected_index=0, visible=False, min_width=LARGURA_DO_MENU,
            bgcolor=ft.Colors.TRANSPARENT, group_alignment=-1.0,
            indicator_color=ft.Colors.SECONDARY_CONTAINER,
            label_type=ft.NavigationRailLabelType.ALL,
            on_change=lambda e: self.mostrar_aba(e.control.selected_index),
            destinations=[ft.NavigationRailDestination(icon=i, selected_icon=s, label=r) for r, i, s in rotulos],
        )

        self.btn_bloquear = ft.IconButton(
            icon=ft.Icons.LOCK_OUTLINE_ROUNDED, tooltip="Bloquear agora",
            visible=logic.pin_configurado(), on_click=lambda e: self.bloquear())
        self.btn_privacidade = ft.IconButton(
            icon=ft.Icons.VISIBILITY_OUTLINED, tooltip="Ocultar valores",
            on_click=lambda e: self.alternar_privacidade())
        cabecalho = ft.Container(
            padding=ft.padding.only(left=20, right=8, top=12, bottom=0),
            content=ft.Row(
                [txt("Oria", 26, 800, COR_MARCA, espacamento=-0.8),
                 ft.Row([self.btn_bloquear, self.btn_privacidade], spacing=0)],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        self.seletor_mes = SeletorMes(self)
        self.pilha_views = ft.Column(controls=[self._cache_views[0]], expand=True, spacing=0)
        coluna = ft.Column([cabecalho, self.seletor_mes, self.pilha_views, self.barra], expand=True, spacing=0)
        self.conteudo = ft.Row([self.menu_lateral, ft.Container(coluna, expand=True)], expand=True, spacing=0)
        self.tela_bloqueio = TelaBloqueio(self)
        self.raiz = ft.SafeArea(
            expand=True, content=ft.Column([self.conteudo, self.tela_bloqueio], expand=True, spacing=0))
        self._visao_principal = ft.View(
            route="/", controls=[self.raiz],
            bgcolor=FUNDO_DA_PAGINA[self.tema], padding=0,
        )

    def _obter_aba(self, indice: int):
        """Retorna a view do índice, construindo-a sob demanda na primeira visita.

        Regras:
        • Se já está no cache → devolve diretamente (zero custo).
        • Se é a primeira visita → instancia, configura a largura atual, insere
          na pilha invisível e atualiza o widget se a UI já estiver montada.
        """
        if self._cache_views[indice] is None:
            view = self._CLASSES_VIEWS[indice](self)
            view.visible = False
            view.definir_largura(self.largura_pagina)
            self._cache_views[indice] = view
            self.pilha_views.controls.append(view)
            if self.pilha_views.page:          # UI já montada → sincroniza o Column
                self.pilha_views.update()
        return self._cache_views[indice]

    # -- tema, privacidade e layout ----------------------------------------------------
    def _aplicar_tema(self) -> None:
        self.page.theme_mode = ft.ThemeMode.DARK if self.tema == "escuro" else ft.ThemeMode.LIGHT
        self.page.bgcolor = FUNDO_DA_PAGINA[self.tema]
        if hasattr(self, "_visao_principal"):
            self._visao_principal.bgcolor = FUNDO_DA_PAGINA[self.tema]

    @tratar_erros
    def definir_tema(self, tema: str) -> None:
        logic.definir_tema(tema)
        self.tema = tema
        self._aplicar_tema()
        self.page.update()

    def formatar_moeda(self, valor: float) -> str:
        return "R$ ••••••" if self.privacidade else logic.formatar_moeda(valor)

    def alternar_privacidade(self) -> None:
        self.privacidade = not self.privacidade
        self.btn_privacidade.icon = (
            ft.Icons.VISIBILITY_OFF_OUTLINED if self.privacidade else ft.Icons.VISIBILITY_OUTLINED)
        self.btn_privacidade.tooltip = "Mostrar valores" if self.privacidade else "Ocultar valores"
        self.btn_privacidade.update()
        aba = self._cache_views[self.indice_atual]
        aba.ao_exibir()  # só redesenha os textos de valor da aba visível
        aba.update()

    def _ajustar_layout(self, atualizar: bool = True) -> None:
        """Escolhe entre barra inferior (celular) e menu lateral (tela larga) e limita
        a largura do conteúdo. Só mexe na tela quando algo realmente mudou."""
        largura = self.page.width or 400
        largo = largura >= LARGURA_MENU_LATERAL
        disponivel = largura - (LARGURA_DO_MENU if largo else 0)
        self.largura_pagina = int(min(LARGURA_MAXIMA_CONTEUDO, disponivel))
        chave = (largo, self.largura_pagina)
        if chave == self._layout_aplicado:
            return
        self._layout_aplicado = chave
        self.menu_lateral.visible = largo
        self.barra.visible = not largo
        for aba in self._cache_views:
            if aba is not None:
                aba.definir_largura(self.largura_pagina)
        if atualizar and self.conteudo.page:
            self.conteudo.update()

    # -- navegação e dados -------------------------------------------------------------
    @tratar_erros
    def mostrar_aba(self, indice: int, atualizar: bool = True) -> None:
        # Registra a aba atual no histórico antes de sair dela,
        # mas só quando a troca é iniciada pelo usuário (não pelo botão Voltar).
        if indice != self.indice_atual and not self._navegando_back:
            self._historico.append(self.indice_atual)
            if len(self._historico) > 15:   # limite razoável de memória
                self._historico.pop(0)
        self.indice_atual = indice
        aba_alvo = self._obter_aba(indice)          # cria sob demanda se for 1ª visita
        for aba in self._cache_views:               # esconde todas as views já carregadas
            if aba is not None:
                aba.visible = False
        aba_alvo.visible = True
        self.barra.selected_index = indice
        self.menu_lateral.selected_index = indice
        self.seletor_mes.visible = indice in (0, 2)  # só Início e Extrato dependem do mês
        if hasattr(self, "_visao_principal"):
            self._visao_principal.route = self._ROTAS[indice]
        try:
            if logic.efetivar_vencidas() > 0:  # o dia virou com o app aberto
                for aba in self._cache_views:
                    if aba is not None:
                        aba.desatualizada = True
            aba_alvo.ao_exibir()
        finally:
            if atualizar and self.conteudo.page:
                self.seletor_mes.update()
                self.pilha_views.update()
                self.barra.update()
                self.menu_lateral.update()

    _ROTAS = ["/", "/registrar", "/extrato", "/cofre", "/ajustes"]

    def ir_para_registrar(self, categoria: str) -> None:
        self.registrar.preselecionar(categoria)
        self.mostrar_aba(1)

    def ir_para_editar(self, item: logic.ItemExtrato) -> None:
        self.registrar.editar(item)
        self.mostrar_aba(1)

    def _sincronizar_periodos(self) -> None:
        self.periodos = logic.obter_meses_disponiveis()
        if (self.ano, self.mes) not in self.periodos:
            hoje = date.today()
            self.ano, self.mes = hoje.year, hoje.month

    @tratar_erros
    def mudar_periodo(self, deslocamento: int) -> None:
        chave = (self.ano, self.mes)
        if chave not in self.periodos:
            return
        atual = self.periodos.index(chave)
        novo = max(0, min(len(self.periodos) - 1, atual + deslocamento))
        if novo == atual:
            return
        self.ano, self.mes = self.periodos[novo]
        self._cache_views[0].desatualizada = True           # início: sempre carregada
        if self._cache_views[2] is not None:                # extrato: só se já foi aberta
            self._cache_views[2].desatualizada = True
        self.seletor_mes.atualizar()
        self._cache_views[self.indice_atual].recarregar()

    @tratar_erros
    def dados_alterados(self) -> None:
        """Chamado depois de salvar/excluir: marca todas as abas como desatualizadas e
        relê agora só a que está na tela; as outras releem quando forem abertas."""
        self._sincronizar_periodos()
        for aba in self._cache_views:               # só abas já carregadas recebem a flag
            if aba is not None:
                aba.desatualizada = True
        self.seletor_mes.atualizar()
        self._cache_views[self.indice_atual].recarregar()

    # -- PIN e bloqueio ----------------------------------------------------------------
    def seguranca_alterada(self) -> None:
        self.btn_bloquear.visible = logic.pin_configurado()
        self.btn_bloquear.update()
        if self._cache_views[4] is not None:        # AjustesView: só atualiza se já foi aberta
            self._cache_views[4].recarregar()

    def bloquear(self) -> None:
        if not logic.pin_configurado():
            return
        self.bloqueado = True
        self.tela_bloqueio.preparar()
        self.conteudo.visible = False
        self.tela_bloqueio.visible = True
        self.raiz.update()

    def liberar(self) -> None:
        self.bloqueado = False
        self.tela_bloqueio.visible = False
        self.conteudo.visible = True
        self.mostrar_aba(self.indice_atual, atualizar=False)
        self.raiz.update()

    def _ao_tecla(self, e: ft.KeyboardEvent) -> None:
        """No desktop, deixa digitar o PIN pelo teclado."""
        if not self.bloqueado:
            return
        tecla = e.key.replace("Numpad ", "")
        if len(tecla) == 1 and tecla in "0123456789":
            self.tela_bloqueio.digitar(tecla)
        elif e.key == "Backspace":
            self.tela_bloqueio.apagar()

    def _ao_mudar_rota(self, e) -> None:
        """Sincroniza a aba ao navegar por URL externa (deep links, etc.)."""
        rota = e.route if hasattr(e, "route") else self.page.route
        if rota in self._ROTAS:
            self.mostrar_aba(self._ROTAS.index(rota))

    def _ao_voltar(self, e) -> None:
        """Trata o botão Voltar do Android.

        O Flet já removeu a visão antes de chamar este handler, portanto
        page.views está temporariamente vazio. Duas situações possíveis:

        • Há histórico → reinsere a visão (o bgcolor igual ao da página torna
          o único frame "vazio" imperceptível) e navega para a aba anterior.
        • Histórico vazio → não reinsere nada; a pilha fica vazia e o Android
          fecha o app naturalmente.
        """
        if not self._historico:
            return  # deixa o Android encerrar o app

        # Reinsere a visão antes de qualquer update (evita flash: same bgcolor)
        self.page.views.append(self._visao_principal)

        # Navega para a aba anterior sem registrar no histórico
        indice_anterior = self._historico.pop()
        self._navegando_back = True
        try:
            self.mostrar_aba(indice_anterior)
        finally:
            self._navegando_back = False

        self.page.update()

    # -- avisos e diálogos ---------------------------------------------------------------
    def notificar(self, mensagem: str, erro: bool = False) -> None:
        cor_texto = ft.Colors.ON_ERROR_CONTAINER if erro else ft.Colors.ON_INVERSE_SURFACE
        largura = 380 if (self.page.width or 0) > 440 else None
        self.page.open(ft.SnackBar(
            content=txt(mensagem, 14, 500, cor_texto),
            bgcolor=ft.Colors.ERROR_CONTAINER if erro else ft.Colors.INVERSE_SURFACE,
            behavior=ft.SnackBarBehavior.FLOATING, width=largura,
            shape=ft.RoundedRectangleBorder(radius=14), duration=2000 if erro else 1000
        ))

    def criar_dialogo(self, titulo: str, conteudo: ft.Control, acoes: list[ft.Control]) -> ft.AlertDialog:
        return ft.AlertDialog(
            modal=True, title=txt(titulo, 20, 700), content=conteudo, actions=acoes,
            actions_alignment=ft.MainAxisAlignment.END, bgcolor=COR_CARTAO,
            shape=ft.RoundedRectangleBorder(radius=R_HERO),
        )

    def confirmar(self, titulo: str, mensagem: str, acao: str, ao_confirmar: Callable[[], None],
                  destrutivo: bool = False) -> None:
        def confirmado(_):
            self.page.close(dialogo)
            ao_confirmar()

        estilo = (estilo_botao(bgcolor=ft.Colors.ERROR, color=ft.Colors.ON_ERROR)
                  if destrutivo else estilo_botao())
        dialogo = self.criar_dialogo(
            titulo,
            ft.Column([txt(mensagem, 15, 400, COR_SUAVE)], tight=True, width=320),
            [ft.TextButton("Cancelar", on_click=lambda _: self.page.close(dialogo)),
             ft.FilledButton(acao, on_click=confirmado, style=estilo)],
        )
        self.page.open(dialogo)

    # -- backup e restauração ---------------------------------------------------------------
    def _eh_mobile(self) -> bool:
        return self.page.platform in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS)

    def exportar_dados(self) -> None:
        self._acao_arquivo = "exportar"
        if self._eh_mobile():
            # No celular o seletor devolve uma pasta; o nome do arquivo é gerado pelo Oria.
            self.seletor_arquivos.get_directory_path(dialog_title="Escolha a pasta do backup")
        else:
            self.seletor_arquivos.save_file(
                dialog_title="Salvar backup do Oria", file_name=logic.nome_sugerido_backup(),
                file_type=ft.FilePickerFileType.CUSTOM, allowed_extensions=["db"])

    def importar_dados(self) -> None:
        def escolher():
            self._acao_arquivo = "importar"
            mobile = self._eh_mobile()  # no Android, filtrar por extensão ".db" esconde os arquivos
            self.seletor_arquivos.pick_files(
                dialog_title="Escolher backup do Oria", allow_multiple=False,
                file_type=ft.FilePickerFileType.ANY if mobile else ft.FilePickerFileType.CUSTOM,
                allowed_extensions=None if mobile else ["db"])

        self.confirmar(
            "Importar dados?",
            "Os dados atuais serão substituídos pelos do arquivo. Uma cópia do banco atual fica "
            "guardada como oria.db.bak. Se o backup tiver PIN, ele passa a valer.",
            "Escolher arquivo", escolher)

    @tratar_erros
    def _ao_resultado_arquivo(self, e: ft.FilePickerResultEvent) -> None:
        acao, self._acao_arquivo = self._acao_arquivo, None
        if acao == "exportar" and e.path:
            self.notificar(f"Backup salvo em {logic.exportar_backup(e.path)}")
        elif acao == "importar" and e.files:
            logic.importar_backup(e.files[0].path)
            self._recarregar_apos_importacao()

    def _recarregar_apos_importacao(self) -> None:
        self.tema = logic.obter_tema()
        self._aplicar_tema()
        self._sincronizar_periodos()
        self.seletor_mes.atualizar()
        self.btn_bloquear.visible = logic.pin_configurado()
        for aba in self._cache_views:
            if aba is not None:
                aba.desatualizada = True
        if logic.pin_configurado():
            self.bloquear()
        else:
            self.mostrar_aba(self.indice_atual)
        self.page.update()
        self.notificar("Dados importados.")


def main(page: ft.Page) -> None:
    app = OriaApp(page)
    try:
        app.iniciar()
    except logic.ERROS_ESPERADOS as exc:
        logging.getLogger("oria").exception("Falha ao iniciar")
        page.clean()
        page.add(ft.SafeArea(ft.Container(
            padding=32,
            content=ft.Column(
                [txt("Não foi possível abrir o Oria", 22, 700),
                 txt(str(exc), 15, 400, COR_SUAVE),
                 txt("Feche o aplicativo e abra de novo. Se o erro continuar, seus dados "
                     "continuam no arquivo oria.db.", 14, 400, COR_SUAVE)],
                spacing=12),
        )))


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(asctime)s - Oria - %(levelname)s - %(message)s")
    ft.app(target=main)
