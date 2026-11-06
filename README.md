# Oria - Controle Financeiro Pessoal

Aplicativo de controle financeiro pessoal desenvolvido em Python utilizando o framework Flet para interface gráfica e SQLite para persistência local dos dados. O sistema foi desenhado com foco em arquitetura limpa, orientação a objetos, isolamento temporal de dados, segurança avançada e suporte multiplataforma (Desktop e Android).

## Funcionalidades Principais
- **Dashboard Inteligente:** Resumo financeiro mensal contendo Saldo Livre, Entradas Efetivadas, Total de Gastos e Valor Investido.
- **Módulo Cofre / Investimentos:** Acompanhamento detalhado do património acumulado por instituição e tipo de investimento.
- **Processamento Temporal Automático:** Efetivação automática de transações agendadas baseada na data local do utilizador.
- **Navegação com Rotas Nativas:** Arquitetura baseada em rotas do Flet (`page.views`), garantindo total compatibilidade com o botão físico de voltar do Android.
- **Segurança com PIN:** Tela de bloqueio integrada com proteção por hash criptográfico (`pbkdf2_hmac`) e suporte a alteração ou remoção de senha.
- **Tema Claro e Escuro:** Alternância dinâmica entre paletas de cores otimizadas para diferentes ambientes de uso.
- **Gestão Completa de Lançamentos:** Suporte a inclusão, edição e exclusão de transações nas categorias Entrada, Gasto e Investimento.
- **Modo de Privacidade:** Ocultação instantânea de valores monetários na interface para proteção de dados sensíveis em locais públicos.
- **Extrato Detalhado:** Listagem organizada cronologicamente com filtros por categoria e gerenciamento de registos.
- **Backup e Restauração:** Ferramentas integradas para exportar e importar dados via arquivos de backup (`.db`) com validação de integridade.

## Estrutura do Projeto
O código está dividido em módulos para isolar responsabilidades:
- **`database.py`:** Camada de acesso a dados (DAO), gerenciamento da conexão SQLite com suporte a caminhos seguros, migração de dados legados, rotinas de backup e operações CRUD.
- **`logic.py`:** Concentra as regras de negócio, validações, hash criptográfico de PIN, cálculos matemáticos, formatação de moedas e datas, e geradores de períodos.
- **`main.py`:** Contém a interface gráfica completa orientada a objetos (classe `OriaApp`), roteamento nativo, gerenciamento de estados, tela de bloqueio e componentes visuais.
- **`requirements.txt`:** Lista de dependências e versões compatíveis do projeto.
