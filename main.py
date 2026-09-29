import flet as ft
from datetime import datetime
import logic
import database


database.create_tables()


modo_privacidade = False
estado_app = {
    "mes": datetime.now().month,
    "ano": datetime.now().year
}

def main(page: ft.Page):
    
    page.window.width = 400
    page.window.height = 700
    page.theme_mode = ft.ThemeMode.LIGHT
    
    
    page.locale_configuration = ft.LocaleConfiguration(
        supported_locales=[ft.Locale("pt", "BR")],
        current_locale=ft.Locale("pt", "BR")
    )

    def formatar_moeda(valor):
        
        if modo_privacidade:
            return "R$ ••••••"
        valor_str = f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {valor_str}"

    def toggle_privacidade(e):
        
        global modo_privacidade
        modo_privacidade = not modo_privacidade
        btn_privacidade.icon = ft.icons.VISIBILITY_OFF if modo_privacidade else ft.icons.VISIBILITY
        page.update()
        renderizar_aba(page.navigation_bar.selected_index)

    btn_privacidade = ft.IconButton(
        icon=ft.icons.VISIBILITY,
        on_click=toggle_privacidade,
        tooltip="Ocultar/Mostrar Valores"
    )

    page.appbar = ft.AppBar(
        title=ft.Text("Controle Financeiro", weight=ft.FontWeight.BOLD),
        center_title=True,
        actions=[btn_privacidade],
        bgcolor=ft.colors.SURFACE_VARIANT
    )

    body = ft.Container(expand=True, padding=15)

    
    def gerar_opcoes_meses():
    
        opcoes = []
        periodos = logic.obter_meses_disponiveis()
        
        for ano, mes in periodos:
            valor = f"{ano}-{mes:02d}"
            texto = logic.obter_nome_mes_ano(mes, ano)
            opcoes.append(ft.dropdown.Option(key=valor, text=texto))
            
        return opcoes

    def on_dropdown_change(e):
        
        if e.control.value:
            selecao = e.control.value.split('-')
            estado_app["ano"] = int(selecao[0])
            estado_app["mes"] = int(selecao[1])
            renderizar_aba(page.navigation_bar.selected_index)

    def mostrar_alerta(mensagem, cor=ft.colors.RED):
        snack = ft.SnackBar(content=ft.Text(mensagem, color=ft.colors.WHITE), bgcolor=cor)
        page.open(snack)

   
    def build_inicio():
        valor_atual = f"{estado_app['ano']}-{estado_app['mes']:02d}"
        dropdown_mes = ft.Dropdown(
            options=gerar_opcoes_meses(),
            value=valor_atual,
            on_change=on_dropdown_change,
            width=250,
            label="Período"
        )

        resumo = logic.calcular_resumo_mes(estado_app["mes"], estado_app["ano"])
        total_gastos = resumo['gastos_fixos'] + resumo['gastos_variaveis']

        def criar_cartao(titulo, valor, cor_texto):
            return ft.Card(
                elevation=2,
                content=ft.Container(
                    padding=15,
                    width=170,
                    content=ft.Column([
                        ft.Text(titulo, size=12, weight=ft.FontWeight.W_500, color=ft.colors.GREY_700),
                        ft.Text(formatar_moeda(valor), size=18, weight=ft.FontWeight.BOLD, color=cor_texto)
                    ])
                )
            )

        grid_cartoes = ft.Row(
            wrap=True,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                criar_cartao("Saldo Livre", resumo['saldo_livre'], ft.colors.BLUE),
                criar_cartao("Entradas Efetivadas", resumo['entradas_efetivadas'], ft.colors.GREEN),
                criar_cartao("Total de Gastos", total_gastos, ft.colors.RED),
                criar_cartao("Meta a Guardar", resumo['meta_guardar'], ft.colors.PURPLE),
            ]
        )

        pendencias = logic.obter_pendencias_mes(estado_app["mes"], estado_app["ano"])
        lista_pendencias = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

        def on_efetivar(e, t_id):
            database.efetivar_transacao(t_id)
            mostrar_alerta("Transação efetivada com sucesso!", ft.colors.GREEN)
            renderizar_aba(page.navigation_bar.selected_index)

        if not pendencias:
            lista_pendencias.controls.append(ft.Text("Nenhuma pendência para este mês.", italic=True, color=ft.colors.GREY))
        else:
            for p in pendencias:
                lista_pendencias.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.PENDING_ACTIONS, color=ft.colors.ORANGE),
                        title=ft.Text(p['descricao']),
                        subtitle=ft.Text(f"Vencimento: {logic.formatar_data_br(p['data'])}"),
                        trailing=ft.Row([
                            ft.Text(formatar_moeda(p['valor']), weight=ft.FontWeight.BOLD),
                            ft.IconButton(
                                icon=ft.icons.CHECK_CIRCLE_OUTLINE,
                                icon_color=ft.colors.GREEN,
                                tooltip="Efetivar",
                                on_click=lambda e, t_id=p['id']: on_efetivar(e, t_id)
                            )
                        ], tight=True)
                    )
                )

        return ft.Column([
            ft.Row([dropdown_mes], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            grid_cartoes,
            ft.Divider(),
            ft.Text("Pendências do Mês", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(content=lista_pendencias, expand=True)
        ], expand=True)


    def build_registrar():
        data_selecionada = {"valor": datetime.now()}

        tf_desc = ft.TextField(label="Descrição", prefix_icon=ft.icons.DESCRIPTION)
        tf_valor = ft.TextField(label="Valor (R$)", prefix_icon=ft.icons.ATTACH_MONEY, keyboard_type=ft.KeyboardType.NUMBER)
        dd_cat = ft.Dropdown(
            label="Categoria",
            options=[
                ft.dropdown.Option("Entrada Efetivada"),
                ft.dropdown.Option("Entrada Futura"),
                ft.dropdown.Option("Gasto Fixo"),
                ft.dropdown.Option("Gasto Variável")
            ]
        )
        lbl_data = ft.Text(f"Data: {data_selecionada['valor'].strftime('%d/%m/%Y')}", weight=ft.FontWeight.BOLD)

        def on_date_change(e):
            if e.control.value:
                data_selecionada["valor"] = e.control.value
                lbl_data.value = f"Data: {data_selecionada['valor'].strftime('%d/%m/%Y')}"
                page.update()

        date_picker = ft.DatePicker(
            first_date=datetime(2020, 1, 1),
            last_date=datetime(2030, 12, 31),
            on_change=on_date_change
        )

        def on_salvar_transacao(e):
            if not tf_desc.value or not tf_valor.value or not dd_cat.value:
                mostrar_alerta("Preencha todos os campos da transação!")
                return
            
            try:
                valor_float = float(tf_valor.value.replace(",", "."))
                data_iso = data_selecionada["valor"].strftime("%Y-%m-%d")
                efetivada = 0 if dd_cat.value == "Entrada Futura" else 1

                database.add_transacao(tf_desc.value, valor_float, dd_cat.value, data_iso, efetivada)
                
                tf_desc.value = ""
                tf_valor.value = ""
                dd_cat.value = None
                mostrar_alerta("Transação salva com sucesso!", ft.colors.GREEN)
                page.update()
            except ValueError:
                mostrar_alerta("O campo Valor deve ser numérico!")

        meta_atual = database.get_meta_guardar()
        tf_meta = ft.TextField(
            label="Nova Meta (R$)", 
            value=f"{meta_atual:.2f}",
            prefix_icon=ft.icons.SAVINGS, 
            keyboard_type=ft.KeyboardType.NUMBER
        )

        def on_salvar_meta(e):
            try:
                valor_meta = float(tf_meta.value.replace(",", "."))
                database.set_meta_guardar(valor_meta)
                mostrar_alerta("Meta atualizada com sucesso!", ft.colors.GREEN)
            except ValueError:
                mostrar_alerta("A Meta deve ser um valor numérico!")

        return ft.Column([
            ft.Text("Nova Transação", size=18, weight=ft.FontWeight.BOLD),
            tf_desc,
            tf_valor,
            dd_cat,
            ft.Row([
                ft.ElevatedButton(
                    "Escolher Data", 
                    icon=ft.icons.CALENDAR_MONTH, 
                    on_click=lambda e: page.open(date_picker)
                ),
                lbl_data
            ]),
            ft.ElevatedButton("Salvar Transação", on_click=on_salvar_transacao, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE, width=page.window.width),
            
            ft.Divider(height=30),
            
            ft.Text("Planejamento Global", size=18, weight=ft.FontWeight.BOLD),
            tf_meta,
            ft.ElevatedButton("Atualizar Meta a Guardar", on_click=on_salvar_meta, bgcolor=ft.colors.PURPLE, color=ft.colors.WHITE, width=page.window.width),
        ], scroll=ft.ScrollMode.AUTO, expand=True)


    
    def build_extrato():
        valor_atual = f"{estado_app['ano']}-{estado_app['mes']:02d}"
        dropdown_mes = ft.Dropdown(
            options=gerar_opcoes_meses(),
            value=valor_atual,
            on_change=on_dropdown_change,
            width=250,
            label="Período do Extrato"
        )

        transacoes = database.get_transacoes_por_mes_ano(estado_app["mes"], estado_app["ano"])
        
        lista_entradas = ft.Column()
        lista_gastos = ft.Column()

        def on_delete(e, t_id):
            database.delete_transacao(t_id)
            mostrar_alerta("Transação excluída!", ft.colors.RED)
            renderizar_aba(page.navigation_bar.selected_index)

        for t in transacoes:
            eh_entrada = "Entrada" in t['categoria']
            cor_texto = ft.colors.GREEN if eh_entrada else ft.colors.RED
            icone = ft.icons.ARROW_UPWARD if eh_entrada else ft.icons.ARROW_DOWNWARD

            item = ft.Card(
                elevation=1,
                content=ft.ListTile(
                    leading=ft.Icon(icone, color=cor_texto),
                    title=ft.Text(t['descricao'], weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(f"{t['categoria']} • {logic.formatar_data_br(t['data'])}"),
                    trailing=ft.Row([
                        ft.Text(formatar_moeda(t['valor']), color=cor_texto, weight=ft.FontWeight.BOLD),
                        ft.IconButton(
                            icon=ft.icons.DELETE_OUTLINE, 
                            icon_color=ft.colors.RED_400,
                            tooltip="Excluir",
                            on_click=lambda e, t_id=t['id']: on_delete(e, t_id)
                        )
                    ], tight=True)
                )
            )
            
            if eh_entrada:
                lista_entradas.controls.append(item)
            else:
                lista_gastos.controls.append(item)

        if not lista_entradas.controls:
            lista_entradas.controls.append(ft.Text("Nenhuma entrada no período.", color=ft.colors.GREY))
        if not lista_gastos.controls:
            lista_gastos.controls.append(ft.Text("Nenhum gasto no período.", color=ft.colors.GREY))

        return ft.Column([
            ft.Row([dropdown_mes], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            ft.Column([
                ft.Text("Entradas", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN),
                lista_entradas,
                ft.Container(height=10),
                ft.Text("Gastos", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.RED),
                lista_gastos,
            ], scroll=ft.ScrollMode.AUTO, expand=True)
        ], expand=True)


    
    def renderizar_aba(index):
        body.content = ft.Container()
        
        if index == 0:
            body.content = build_inicio()
        elif index == 1:
            body.content = build_registrar()
        elif index == 2:
            body.content = build_extrato()
            
        page.update()
        
    def on_nav_change(e):
        renderizar_aba(e.control.selected_index)

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_nav_change,
        destinations=[
            ft.NavigationBarDestination(icon=ft.icons.HOME_OUTLINED, selected_icon=ft.icons.HOME, label="Início"),
            ft.NavigationBarDestination(icon=ft.icons.ADD_CIRCLE_OUTLINE, selected_icon=ft.icons.ADD_CIRCLE, label="Registrar"),
            ft.NavigationBarDestination(icon=ft.icons.LIST_ALT_OUTLINED, selected_icon=ft.icons.LIST_ALT, label="Extrato"),
        ]
    )

    page.add(body)
    renderizar_aba(0)

if __name__ == "__main__":
   ft.app(target=main)