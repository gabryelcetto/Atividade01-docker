# Controle de Equipamentos — UVV

> **Acesso:** com os containers no ar (`docker compose up -d`), a aplicação
> fica em **http://localhost:5000**. Não rode `app.py` direto (fora do
> Docker) — ele não alcança o banco (`db` só resolve dentro da rede Docker) e
> só serve pra confundir com um erro parecido.

Projeto da disciplina **DEVOPS Tools** (Prof. Renato Sousa Botacim) — Universidade
Vila Velha. Aplicação web conteinerizada com Docker: Flask + MySQL, cada um no seu
container, comunicando-se por uma rede Docker, com persistência de dados em volume.

Todos os dados (funcionários, equipamentos, ocorrências) são **fictícios**, criados
só para demonstração.

## 1. Qual é o objetivo da aplicação?

Controlar o inventário de equipamentos de TI de uma organização: cadastrar
notebooks, monitores, periféricos, fones e outros equipamentos, saber quem está
com cada um, em que sala/mesa, em que status (em uso, disponível, em manutenção,
emprestado, baixado), se é um bem da empresa ou particular, além de manter
histórico de movimentações (troca de responsável/local) e de ocorrências
(problemas relatados e sua resolução).

## 2. Quais tecnologias foram utilizadas?

- **Python 3.12 + Flask** — aplicação web (arquitetura em camadas:
  `routes/` → `services/` → `models/`, com `templates/` em Jinja2)
- **MySQL 8.0** — banco de dados relacional
- **Gunicorn** — servidor WSGI de produção (substitui o servidor de
  desenvolvimento do Flask dentro do container)
- **Docker + Docker Compose** — conteinerização e orquestração dos serviços
- **Three.js + GSAP** (via CDN) — animação decorativa da tela de entrada

## 3. Como executar o projeto?

Pré-requisito: Docker e Docker Compose instalados.

```bash
git clone <url-do-repositorio>
cd controle-equipamentos-docker

cp .env.example .env
# edite o .env se quiser trocar as senhas de exemplo

docker compose up --build
```

Na primeira subida, o MySQL cria o schema e já popula o banco com os dados
fictícios (ver pergunta 6). Isso só acontece uma vez — enquanto o volume
`db_data` existir, os dados persistem entre reinicializações.

## 4. Qual porta deve ser acessada?

`http://localhost:5000`

## 5. Quais containers são utilizados?

Dois serviços, definidos em `docker-compose.yml`:

- **`web`** — a aplicação Flask, construída a partir do `Dockerfile` (build
  multi-stage), servida por Gunicorn na porta 5000.
- **`db`** — banco de dados, imagem oficial `mysql:8.0`.

## 6. Qual banco de dados é utilizado?

**MySQL 8.0**. O schema (`db/schema.sql`) e os dados fictícios (`db/seed.sql`)
são carregados automaticamente pelo container `db` na primeira inicialização
(mecanismo `docker-entrypoint-initdb.d/` da imagem oficial do MySQL).

O banco vem com **40 equipamentos** cadastrados (30 de propriedade da empresa,
10 particulares), distribuídos entre notebooks, monitores, periféricos, fones
e outros, além de 12 funcionários fictícios e um pequeno histórico de
movimentações e ocorrências.

## 7. Qual volume foi criado?

Dois volumes nomeados (declarados em `docker-compose.yml`):

- **`db_data`** — persiste os arquivos de dados do MySQL
  (`/var/lib/mysql` dentro do container `db`). É o que garante que os dados
  sobrevivem a um `docker compose down` / `docker compose up` normal.
- **`uploads_data`** — persiste as fotos enviadas pelos equipamentos
  (`/app/static/uploads` dentro do container `web`).

## 8. Qual rede foi criada?

**`rede_equipamentos`** (driver `bridge`), também declarada em
`docker-compose.yml`. Os containers `web` e `db` conversam entre si por essa
rede — o `web` se conecta ao banco usando o nome do serviço (`db`) como host,
sem precisar de IP fixo.

## 9. Quais variáveis de ambiente são utilizadas?

Definidas em `.env` (a partir do `.env.example`):

| Variável              | Para quê serve                                         |
|------------------------|--------------------------------------------------------|
| `DB_HOST`              | Host do MySQL — `db` (nome do serviço no compose)      |
| `DB_PORT`              | Porta do MySQL (3306)                                   |
| `DB_NAME`              | Nome do banco                                           |
| `DB_USER` / `DB_PASSWORD` | Credenciais que a aplicação usa para conectar        |
| `MYSQL_ROOT_PASSWORD`  | Senha de root, usada só pela imagem do MySQL para inicializar o banco |
| `SECRET_KEY`           | Chave secreta do Flask (sessão/flash messages)          |
| `FLASK_DEBUG`          | Liga/desliga o modo debug do Flask (`0` em produção)    |
| `PASTA_UPLOADS`        | Subpasta de `static/` onde as fotos ficam salvas        |
| `S3_*` (opcionais)     | Se preenchidas, as fotos vão para um object storage compatível com S3 em vez do disco local — não usadas por padrão neste projeto |

## 10. Como parar o projeto?

```bash
docker compose down
```

Isso para e remove os containers, mas **mantém** os volumes (os dados do banco
e as fotos continuam lá para a próxima subida).

Para apagar tudo, incluindo os dados persistidos:

```bash
docker compose down -v
```

## Estrutura do projeto

```
app.py            # application factory — cria o Flask app e registra os blueprints
config.py         # configuração do Flask (secret key, upload)
banco.py          # pool de conexões MySQL + context managers cursor_leitura()/transacao()
models/           # consultas SQL
services/         # regra de negócio + transações
routes/           # blueprints Flask
templates/        # Jinja2
static/           # CSS e imagens
db/
  schema.sql      # schema completo do banco
  seed.sql        # dados fictícios de demonstração
Dockerfile        # build multi-stage da aplicação
docker-compose.yml
.dockerignore
.env.example
```
