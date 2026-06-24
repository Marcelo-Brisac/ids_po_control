# Docker Setup - IDS PO Control

Este guia explica como rodar o IDS PO Control usando Docker e Docker Compose.

## Arquitetura

O sistema utiliza 2 containers:

1. **ids_po_web**: Aplicação Django + Gunicorn (porta 8000)
2. **ids_po_db**: PostgreSQL 16 (porta 5432)

## Pré-requisitos

- Docker Desktop (ou Docker Engine)
- Docker Compose v2+

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/Marcelo-Brisac/ids_po_control.git
cd ids_po_control
```

### 2. Configure as variáveis de ambiente (opcional)

Crie um arquivo `.env` baseado no `.env.example`:

```bash
cp .env.example .env
```

Edite o `.env` se precisar alterar configurações (senhas, hosts, etc).

### 3. Inicie os containers

```bash
docker-compose up -d
```

Este comando irá:
- Baixar as imagens necessárias (PostgreSQL 16, Python 3.13)
- Construir a imagem da aplicação Django
- Criar os volumes para persistência de dados
- Aplicar migrações do banco automaticamente
- Criar um superusuário padrão

### 4. Acesse a aplicação

- **Portal**: http://localhost:8000
- **Admin**: http://localhost:8000/admin

### 5. Login inicial

- Usuário: `admin`
- Senha: `admin123`

## Comandos úteis

### Ver logs

```bash
# Todos os containers
docker-compose logs -f

# Apenas aplicação
docker-compose logs -f web

# Apenas banco
docker-compose logs -f db
```

### Parar containers

```bash
docker-compose down
```

### Parar e remover volumes (cuidado: apaga dados!)

```bash
docker-compose down -v
```

### Reconstruir imagem

```bash
docker-compose build
```

### Entrar no container da aplicação

```bash
docker-compose exec web bash
```

### Executar comandos Django

```bash
# Criar migrações
docker-compose exec web python manage.py makemigrations

# Aplicar migrações
docker-compose exec web python manage.py migrate

# Criar superusuário
docker-compose exec web python manage.py createsuperuser

# Shell Django
docker-compose exec web python manage.py shell
```

## Backup do banco

### Fazer backup

```bash
docker-compose exec db pg_dump -U ids_po_user ids_po_control > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restaurar backup

```bash
cat backup.sql | docker-compose exec -T db psql -U ids_po_user ids_po_control
```

## Configuração para produção

Para usar em produção, ajuste as seguintes configurações no `.env`:

```env
DEBUG=False
SECRET_KEY=<gere-uma-chave-longa-e-aleatória>
ALLOWED_HOSTS=seudominio.com,www.seudominio.com

# Cookie settings (obrigatório com HTTPS)
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
CSRF_TRUSTED_ORIGINS=https://seudominio.com,https://www.seudominio.com
```

Gere uma SECRET_KEY segura:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

## Troubleshooting

### Container não inicia

Verifique os logs:
```bash
docker-compose logs
```

### Banco não conecta

Aguarde o healthcheck do PostgreSQL (pode levar 10-15 segundos na primeira vez).

### Porta já em uso

Se a porta 8000 ou 5432 estiver em uso, altere no `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Porta externa diferente
```

### Erro de permissão no volume

```bash
docker-compose down
sudo rm -rf postgres_data
docker-compose up -d
```

## Estrutura dos volumes

- `postgres_data`: Dados persistentes do PostgreSQL
- `static_volume`: Arquivos estáticos coletados do Django
