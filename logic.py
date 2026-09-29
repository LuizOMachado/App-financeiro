import database
from datetime import datetime


MESES_PT_BR = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

def formatar_data_br(data_iso):
    
    try:
        ano, mes, dia = data_iso.split('-')
        return f"{dia}/{mes}/{ano}"
    except ValueError:
        return data_iso

def obter_nome_mes_ano(mes, ano):
  
    try:
        mes_int = int(mes)
        nome_mes = MESES_PT_BR.get(mes_int, "Mês Inválido")
        return f"{nome_mes} de {ano}"
    except (ValueError, TypeError):
        return f"Período Inválido ({mes}/{ano})"

def obter_meses_disponiveis():
    
    
    agora = datetime.now()
    meses_set = {(agora.year, agora.month)}
    
    
    try:
        with database._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT data FROM transacoes")
            registros = cursor.fetchall()
            
            for reg in registros:
                data_iso = reg['data']
                if data_iso and len(data_iso) >= 7:
                    partes = data_iso.split('-')
                    if len(partes) >= 2:
                        ano = int(partes[0])
                        mes = int(partes[1])
                        meses_set.add((ano, mes))
    except Exception:
        pass  
        
    
    return sorted(list(meses_set))

def calcular_resumo_mes(mes, ano):
    
    transacoes = database.get_transacoes_por_mes_ano(mes, ano)
    meta_guardar = database.get_meta_guardar()
    
    entradas_efetivadas = 0.0
    gastos_fixos = 0.0
    gastos_variaveis = 0.0
    
    for t in transacoes:
        categoria = t['categoria']
        valor = t['valor']
        efetivada = t['efetivada']
        
        if categoria == 'Entrada Efetivada' or (categoria == 'Entrada Futura' and efetivada == 1):
            entradas_efetivadas += valor
        elif categoria == 'Gasto Fixo':
            gastos_fixos += valor
        elif categoria == 'Gasto Variável':
            gastos_variaveis += valor
            
    saldo_livre = entradas_efetivadas - meta_guardar - (gastos_fixos + gastos_variaveis)
    
    return {
        'entradas_efetivadas': round(entradas_efetivadas, 2),
        'gastos_fixos': round(gastos_fixos, 2),
        'gastos_variaveis': round(gastos_variaveis, 2),
        'meta_guardar': round(meta_guardar, 2),
        'saldo_livre': round(saldo_livre, 2)
    }

def obter_pendencias_mes(mes, ano):
   
    transacoes = database.get_transacoes_por_mes_ano(mes, ano)
    pendencias = []
    
    for t in transacoes:
        if t['categoria'] == 'Entrada Futura' and t['efetivada'] == 0:
            pendencias.append(t)
            
    return pendencias