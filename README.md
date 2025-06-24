# Consult CNPJ CNAE

Uma aplicação web Flask para consulta de CNAEs (Classificação Nacional de Atividades Econômicas) através de CNPJ, com funcionalidades para verificação de dispensa de licenciamento e inscrição estadual.

## 📋 Descrição

Esta aplicação permite consultar informações de empresas através do CNPJ e verificar:

- **Dispensa de Licenciamento**: Verifica se uma empresa está dispensada de licenciamento ambiental baseado nos CNAEs
- **Dispensa de Inscrição Estadual**: Verifica se uma empresa está dispensada de inscrição estadual
- **Consulta de CNAEs**: Busca informações detalhadas sobre CNAEs específicos

A aplicação utiliza APIs públicas para obter dados de empresas e um banco de dados PostgreSQL para armazenar informações sobre CNAEs e suas classificações.

## 🚀 Funcionalidades

- **Consulta por CNPJ**: Busca automática de CNAEs através do CNPJ da empresa
- **Verificação de Dispensa**: Análise automática de dispensa de licenciamento e inscrição estadual
- **Interface Responsiva**: Design moderno com Tailwind CSS
- **APIs Integradas**:
  - Receita Federal (receitaws.com.br)
  - Dados.gov.br para informações de CNAEs
  - CNPJ.ws para dados adicionais

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python Flask
- **Frontend**: HTML, CSS (Tailwind CSS), JavaScript
- **Banco de Dados**: PostgreSQL
- **APIs**: Receita Federal, Dados.gov.br, CNPJ.ws
- **Deploy**: Heroku (configurado)

## 📦 Instalação

### Pré-requisitos

- Python 3.7+
- PostgreSQL
- Node.js (para Tailwind CSS)

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd consult-cnpj-cnae
```

### 2. Instale as dependências Python

```bash
pip install -r requirements.txt
```

### 3. Instale as dependências Node.js

```bash
npm install
```

### 4. Configure o banco de dados

Crie um banco PostgreSQL e configure a variável de ambiente `DATABASE_URL` ou modifique a string de conexão no arquivo `app.py`.

### 5. Configure o Tailwind CSS

```bash
npm run tailwind
```

### 6. Execute a aplicação

```bash
python app.py
```

A aplicação estará disponível em `http://localhost:5000`

## 🔧 Configuração

### Variáveis de Ambiente

Configure as seguintes variáveis de ambiente:

```bash
DATABASE_URL=postgresql://usuario:senha@host:porta/banco
```

### Banco de Dados

A aplicação utiliza as seguintes tabelas:

- `app_controledispensacnaes`: Armazena informações sobre CNAEs, grau de risco, dispensa de licenciamento e inscrição estadual

## 📖 Como Usar

### 1. Consulta por CNPJ

1. Acesse a página inicial
2. Digite o CNPJ da empresa (com ou sem formatação)
3. Selecione o tipo de consulta desejada
4. Clique em consultar

### 2. Tipos de Consulta Disponíveis

- **Verificação de dispensa de Licenciamento**: Verifica se a empresa está dispensada de licenciamento ambiental
- **Verificação de dispensa de inscrição estadual**: Verifica se a empresa está dispensada de inscrição estadual

### 3. Resultados

Os resultados são exibidos em tabelas organizadas com:

- CNAEs da empresa
- Descrição das atividades
- Status de dispensa
- Informações adicionais

## 🏗️ Estrutura do Projeto

```
consult-cnpj-cnae/
├── app.py                 # Aplicação principal Flask
├── requirements.txt       # Dependências Python
├── package.json          # Dependências Node.js
├── tailwind.config.js    # Configuração Tailwind CSS
├── Procfile             # Configuração Heroku
├── runtime.txt          # Versão Python para Heroku
├── static/              # Arquivos estáticos
│   ├── output.css       # CSS compilado
│   ├── input.css        # CSS fonte
│   ├── script.js        # JavaScript
│   └── *.png           # Imagens
├── templates/           # Templates HTML
│   ├── index.html      # Página principal
│   ├── resultados.html # Página de resultados
│   └── error.html      # Página de erro
└── README.md           # Este arquivo
```

## 🔌 APIs Utilizadas

### Receita Federal

- **URL**: `https://www.receitaws.com.br/v1/cnpj/{cnpj}`
- **Função**: Obter dados básicos da empresa e CNAEs

### Dados.gov.br

- **URL**: `https://compras.dados.gov.br/fornecedores/doc/cnae/{cnae}.json`
- **Função**: Obter descrição detalhada de CNAEs

### CNPJ.ws

- **URL**: `https://publica.cnpj.ws/cnpj/{cnpj}`
- **Função**: Dados adicionais de empresas

## 🚀 Deploy

### Heroku

A aplicação está configurada para deploy no Heroku:

1. Crie uma conta no Heroku
2. Instale o Heroku CLI
3. Execute os comandos:

```bash
heroku create
git add .
git commit -m "Initial commit"
git push heroku main
```

### Configuração do Banco

Configure a variável de ambiente `DATABASE_URL` no Heroku:

```bash
heroku config:set DATABASE_URL=postgresql://...
```

## 📝 Licença

Este projeto está sob a licença ISC.

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Suporte

Para suporte, entre em contato através do site [Consult Contábil](https://consultcontabil.com/).

## 📄 Legislação

Esta aplicação utiliza como base a **PORTARIA ME Nº 7.163, DE 21 DE JUNHO DE 2021**. Para mais informações, acesse a [legislação completa](https://www.in.gov.br/en/web/dou/-/portaria-me-n-7.163-de-21-de-junho-de-2021-327649097).
