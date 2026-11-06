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

## Pré-requisitos

Para executar este projeto em sua máquina local, você precisará ter instalado:

* Python (versão 3.11 ou superior recomendada)
* Git

---
## Como Executar o Projeto Localmente

Siga os passos abaixo para configurar o ambiente e rodar a aplicação no seu computador:

1. Clone este repositório ou baixe os arquivos para uma pasta local:
   
   git clone https://github.com/LuizOMachado/App-financeiro.git
 
   cd App-financeiro
2. Instale as dependências listadas no projeto:
   
   pip install -r requirements.txt

3. Execute o aplicativo

   flet run main.py

## Baixar e Instalar no Celular (Android)
O arquivo instalador (.apk) do aplicativo encontra-se disponível diretamente na seção Releases deste repositório no GitHub.

Para utilizar a aplicação no seu telemóvel, basta seguir os passos abaixo:

Aceda à página principal do repositório no GitHub e localize a aba Releases

Descarregue o arquivo .apk 

Transfira o arquivo para o seu smartphone Android.

Toque no arquivo descarregado para iniciar a instalação.

Caso o sistema operacional exiba um aviso de segurança por se tratar de um aplicativo externo à loja oficial, selecione a opção para permitir a instalação de fontes desconhecidas ou clique em "Instalar mesmo assim".
   

