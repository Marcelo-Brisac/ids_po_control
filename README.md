# IDS PO Control

Sistema de gerenciamento de Purchase Orders (POs) desenvolvido em Django.

## Funcionalidades

- **CRUD completo de POs**: Criar, listar, editar, visualizar e excluir Purchase Orders
- **Geração de PDF**: Exportar POs em formato PDF profissional
- **Gestão de Issuers e Suppliers**: Cadastro completo com múltiplos emails e contas bancárias
- **Itens e Termos de Pagamento**: Adicionar múltiplos itens e condições de pagamento por PO
- **Admin Interface**: Interface administrativa para gestão de dados mestres

## Instalação Rápida com Docker (Recomendado)

A maneira mais fácil de rodar o sistema é usando Docker Compose:

```bash
git clone https://github.com/Marcelo-Brisac/ids_po_control.git
cd ids_po_control
docker-compose up -d
```

Acesse:
- Portal: http://localhost:8000
- Admin: http://localhost:8000/admin
- Login: `admin` / `admin123`

Veja [DOCKER_README.md](DOCKER_README.md) para instruções completas sobre Docker.

## Instalação Manual (sem Docker)

### Requisitos

- Python 3.13+
- SQLite (padrão) ou PostgreSQL

### Passos

1. Clone o repositório:
```bash
git clone https://github.com/Marcelo-Brisac/ids_po_control.git
cd ids_po_control
```

2. Crie um ambiente virtual e ative:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Execute as migrações do banco de dados:
```bash
python manage.py migrate
```

5. Crie um superusuário para acessar o admin:
```bash
python manage.py createsuperuser
```

6. Inicie o servidor de desenvolvimento:
```bash
python manage.py runserver
```

7. Acesse:
   - Portal: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/

## Estrutura do Banco de Dados

### Issuer (Emitente)
- Nome, endereço, tax_id (opcional)
- Múltiplos emails
- Múltiplas contas bancárias

### Supplier (Fornecedor)
- Nome, endereço, tax_id (opcional)
- Contas bancárias com endereço específico

### Purchase Order (PO)
- Número da PO, número do contrato
- Data de emissão
- Lead time solicitado
- Garantia
- Issuer e Supplier vinculados

### PO Items
- Nome do modelo comercial
- Descrição
- Quantidade e preço unitário
- Moeda

### PO Payment Terms
- Nome do evento
- Percentual devido
- Data esperada

## Requisitos

- Python 3.13+
- Django 6.0+
- WeasyPrint (para geração de PDF)

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/Marcelo-Brisac/ids_po_control.git
cd ids_po_control
```

2. Crie um ambiente virtual e ative:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install django weasyprint
```

4. Execute as migrações do banco de dados:
```bash
python manage.py migrate
```

5. Crie um superusuário para acessar o admin:
```bash
python manage.py createsuperuser
```

6. Inicie o servidor de desenvolvimento:
```bash
python manage.py runserver
```

7. Acesse:
   - Portal: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/

## Uso

### Admin Django
Acesse `/admin/` para gerenciar:
- Issuers (com emails e contas bancárias)
- Suppliers (com contas bancárias)

### Portal de POs
Acesse `/` para:
- Listar todas as POs
- Criar novas POs com itens e termos de pagamento
- Editar POs existentes
- Visualizar detalhes completos
- Gerar PDFs

## Credenciais de Teste

O banco de dados inicial inclui:
- Usuário admin: `admin` / `admin123`
- Issuer de exemplo: Acme Corporation
- Supplier de exemplo: Global Supplies Ltd.
- PO de exemplo: PO-2026-001

## Estrutura do Projeto

```
ids_po_control/
├── manage.py
├── portal/              # Configurações do Django
│   ├── settings.py
│   ├── urls.py
│   └── middleware.py
├── procurement/         # App principal
│   ├── models.py        # Modelos do banco
│   ├── views.py         # Views e lógica
│   ├── admin.py         # Configuração do admin
│   ├── urls.py          # URLs da app
│   ├── templates/       # Templates HTML
│   └── static/          # CSS e arquivos estáticos
└── README.md
```

## Licença

Este projeto está em desenvolvimento ativo.
