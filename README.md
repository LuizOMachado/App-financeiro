# Controle Financeiro Pessoal

Aplicativo de controle financeiro pessoal desenvolvido em Python utilizando o framework Flet para interface gráfica e SQLite para persistência local dos dados. O sistema foi desenhado com foco em arquitetura limpa, isolamento temporal de dados e suporte multiplataforma (Desktop e Android).

---

## Funcionalidades Principais

* **Dashboard Inteligente:** Resumo financeiro mensal contendo Saldo Livre, Entradas Efetivadas, Total de Gastos e Meta a Guardar.
* **Regra do "Pague-se Primeiro":** O cálculo do saldo livre desconta automaticamente a meta de economia global definida pelo usuário.
* **Isolamento Temporal:** Visualização de dados segmentada por mês e ano específicos, garantindo que lançamentos de um período não interfiram em outro.
* **Gestão de Pendências:** Acompanhamento e efetivação de entradas futuras diretamente pelo painel principal.
* **Registro Completo de Transações:** Suporte a quatro categorias principais: Entrada Efetivada, Entrada Futura, Gasto Fixo e Gasto Variável.
* **Modo de Privacidade:** Ocultação instantânea de valores monetários na interface para proteção de dados sensíveis em locais públicos.
* **Extrato Detalhado:** Listagem separada por entradas e gastos com opção de exclusão individual de registros.

---

## Estrutura do Projeto

O código está dividido em módulos para isolar responsabilidades:

* `database.py`: Camada de acesso a dados (DAO), gerenciamento da conexão SQLite com suporte a caminhos seguros e rotinas de criação de tabelas e operações CRUD.
* `logic.py`: Concentra as regras de negócio, cálculos matemáticos, formatação de moedas e datas, e geradores de períodos em formato textual.
* `main.py`: Contém a interface gráfica completa implementada em Flet, gerenciamento de estados e navegação entre abas.
* `requirements.txt`: Lista de dependências e versões compatíveis do projeto.

---

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
   
