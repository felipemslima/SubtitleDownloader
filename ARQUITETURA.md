# Arquitetura do Projeto

Este documento descreve a estrutura do WellRAMS para servir como referencia ao criar outro web app usando uma organizacao parecida.

O projeto e dividido em dois blocos principais:

- `backend/`: API em Flask, responsavel por expor endpoints, aplicar regras de aplicacao, acessar dados externos/arquivos e transformar entidades de dominio.
- `frontend/`: app React com Vite, responsavel por rotas, telas, componentes visuais, chamadas HTTP, cache de dados e adaptacao dos dados da API para a UI.

Na raiz tambem ficam arquivos de orquestracao e documentacao, como `docker-compose.yml`, `README.md` e `CONTRIBUTING.md`.

## Visao Geral

```text
WellRAMS/
|-- backend/
|   |-- api/
|   |-- application/
|   |-- domain/
|   |-- infrastructure/
|   |-- static/
|   |-- tests/
|   |-- app.py
|   `-- requirements.txt
|
|-- frontend/
|   |-- public/
|   |-- src/
|   |   |-- app/
|   |   |-- assets/
|   |   |-- components/
|   |   |-- lib/
|   |   |-- routes/
|   |   |-- styles/
|   |   `-- types/
|   |-- package.json
|   |-- vite.config.js
|   `-- tsconfig.json
|
|-- docker-compose.yml
|-- README.md
`-- CONTRIBUTING.md
```

## Backend

O backend segue uma separacao por camadas. A ideia principal e manter as rotas HTTP finas, deixando regras e transformacoes fora dos arquivos de rota.

```text
backend/
|-- api/routes/          # Endpoints Flask e Blueprints
|-- application/         # Casos de uso e servicos de aplicacao
|-- domain/entities/     # Entidades e regras puras de dominio
|-- infrastructure/      # Banco, storage, cache e APIs externas
|-- static/              # Arquivos estaticos, Swagger e build servido
|-- tests/               # Testes unitarios, integracao e fixtures
|-- app.py               # Application factory e registro das rotas
`-- requirements.txt     # Dependencias Python
```

### `app.py`

Arquivo de entrada do Flask. Ele cria a aplicacao, configura CORS, registra handlers globais e adiciona todos os Blueprints.

Exemplo de responsabilidades:

- criar a instancia `Flask`;
- registrar guards e handlers de erro;
- configurar CORS;
- registrar blueprints como `healthBp`, `wellsBp`, `graphsBp`, `reliawellBp`;
- executar a aplicacao localmente na porta `5000`.

### `api/routes`

Contem as rotas HTTP. Cada arquivo representa um grupo de endpoints por assunto.

Exemplos:

- `healthRoutes.py`: endpoints de saude da API;
- `hierarchyProviderRoutes.py`: endpoint `/assets/hierarchy`;
- `graphProviderRoutes.py`: endpoints relacionados a grafos;
- `reliaWellProviderRoutes.py`: endpoints de simulacao/ReliaWell;
- `errorHandlers.py`: tratamento global de erros e guards.

Padrao esperado:

```python
from flask import Blueprint, jsonify
from application.algumCasoDeUso import executarCasoDeUso

featureBp = Blueprint("featureBp", __name__)

@featureBp.route("/feature", methods=["GET"])
def getFeature():
    result = executarCasoDeUso()
    return jsonify(result), 200
```

Ou seja: a rota recebe a requisicao, chama a camada de aplicacao e retorna a resposta HTTP.

### `application`

Camada de casos de uso. Ela coordena o que precisa acontecer para atender uma funcionalidade.

Exemplo real:

```text
api/routes/hierarchyProviderRoutes.py
    chama application/hierarchyProvider.py
        chama infrastructure/databases/hierarchyCache.py
        chama domain/entities/hierarchyProvider.py
```

Essa camada pode:

- buscar dados em storage, banco ou API externa;
- chamar entidades/funcoes de dominio;
- montar o resultado que sera enviado para a rota;
- centralizar regras de aplicacao.

### `domain/entities`

Camada de dominio. Deve concentrar logicas mais puras, independentes de Flask, HTTP ou banco.

Exemplos:

- montagem de hierarquia;
- entidades de grafo;
- conversao de dados brutos de pocos;
- distribuicoes de probabilidade.

Essa camada deve ser mais facil de testar, porque idealmente recebe dados e devolve dados, sem depender diretamente de infraestrutura.

### `infrastructure`

Camada de acesso a recursos externos ou persistencia.

Exemplos:

- `infrastructure/databases/storage.py`: acesso ao storage;
- `infrastructure/databases/hierarchyCache.py`: cache para dados de hierarquia;
- `infrastructure/databases/graphStorage.py`: acesso a grafos;
- `infrastructure/apis/reliaWellApi.py`: integracao com API externa.

Quando outro app for criado, use essa pasta para tudo que conversa com "o mundo de fora": banco, arquivos, cache, APIs externas, filas, clientes HTTP etc.

### `tests`

Os testes ficam dentro de `backend/tests`.

Organizacao:

- `unit/`: testes unitarios, seguros para CI;
- `integration/`: testes que podem depender de VPN, servicos externos ou dados reais;
- `fixtures/`: massas de dados usadas pelos testes;
- `testConfig.py`: configuracoes auxiliares para testes.

Comandos principais:

```bash
cd backend
pytest tests/unit/ -v
pytest tests/integration/ -v
```

## Frontend

O frontend usa React, Vite, TypeScript, React Router, React Query, Axios, Tailwind, MUI e Recharts.

A estrutura separa telas, componentes, rotas, tipos, servicos, camada de dados e camada de dominio.

```text
frontend/src/
|-- app/                 # Ponto de entrada, layout e paginas principais
|-- assets/              # Assets importados pelo codigo
|-- components/          # Componentes reutilizaveis e componentes por modulo
|-- lib/
|   |-- constants/       # Constantes de rotas, menu, charts etc.
|   |-- data/            # Datasources, models e mappers da API
|   |-- domain/          # Hooks/casos de uso consumidos pelas telas
|   |-- services/        # Cliente HTTP e helpers de request
|   `-- utils/           # Funcoes utilitarias e env
|-- routes/              # Declaracao das rotas publicas, privadas e guardas
|-- styles/              # CSS global
`-- types/               # Tipos compartilhados pela aplicacao
```

### `app`

Contem a entrada da aplicacao e as paginas principais.

Arquivos importantes:

- `main.tsx`: renderiza o React, configura `BrowserRouter` e `QueryClientProvider`;
- `main-layout.tsx`: layout das rotas privadas, com `Header` e `Outlet`;
- `Auth/Login/login.tsx`: pagina de login;
- `Automatic/automatic.tsx`: pagina do fluxo automatico;
- `Simulation/simulation.tsx`: pagina de simulacao.

### `routes`

Centraliza a configuracao de rotas.

Arquivos:

- `app.routes.tsx`: compoe as rotas publicas, privadas e rota 404;
- `public.routes.tsx`: lista de rotas publicas;
- `private.routes.tsx`: lista de rotas privadas;
- `protected.route.tsx`: guarda de autenticacao;
- `types/route.ts`: tipo usado para declarar uma rota.

Fluxo:

```text
main.tsx
  -> BrowserRouter
    -> AppRoutes
      -> publicRoutes
      -> ProtectedRoute
        -> MainLayout
          -> privateRoutes
```

### `components`

Contem componentes visuais reutilizaveis e componentes especificos de dominio.

Organizacao atual:

- `components/ui/`: componentes genericos de interface, como `Button`, `Header`, `LeftBar`, `Loading`, `ErrorMessage`, `Select`, `DataTable`, `Charts`;
- `components/auth/`: componentes do login;
- `components/automatic/`: componentes do fluxo automatico;
- `components/simulation/`: componentes da simulacao, parametros e resultados.

Regra pratica:

- se o componente e generico e pode ser usado em varias telas, coloque em `components/ui`;
- se o componente pertence a uma funcionalidade especifica, coloque em `components/<modulo>`.

### `lib/services`

Camada base de comunicacao com a API.

Arquivos principais:

- `api.ts`: instancia Axios com `baseURL` e interceptors;
- `api-request.ts`: helper para padronizar requests e erros;
- `api-model.ts`: modelos compartilhados de API;
- `index.ts`: exports da pasta.

O `baseURL` vem de `ENV.VITE_API_LOCAL_BASE_URL`, definido via variavel de ambiente do Vite.

### `lib/data`

Camada de dados. Ela conhece o formato da API e transforma a resposta para um formato mais conveniente para o frontend.

Cada dominio costuma ter:

- `get-*.datasource.ts`: chamada HTTP;
- `*.datasource.model.ts`: tipos/modelos da resposta da API;
- `*.map.ts`: conversao da resposta da API para tipos usados pela UI;
- `index.ts`: exports publicos do modulo.

Exemplo:

```text
lib/data/Hierarchy/
|-- get-hierarchy.datasource.ts
|-- hierarchy-datasource.model.ts
|-- hierarchy.map.ts
`-- index.ts
```

Essa separacao e importante porque evita que componentes React dependam diretamente do formato bruto retornado pelo backend.

### `lib/domain`

Camada de casos de uso do frontend. Normalmente contem hooks que usam `@tanstack/react-query` e chamam a camada `lib/data`.

Exemplo real:

```text
lib/domain/Hierarchy/get-hierarchy.use-case.ts
    chama lib/data/Hierarchy/get-hierarchy.datasource.ts
        chama lib/services/api.ts
```

Responsabilidades:

- definir `queryKey`;
- controlar cache (`staleTime`, invalidacoes etc.);
- expor hooks prontos para as telas;
- encapsular mutacoes e queries;
- esconder detalhes da API dos componentes.

### `types`

Contem tipos compartilhados por telas, componentes, mappers e hooks.

Exemplos:

- `hierarchy.ts`;
- `reliawell.ts`;
- `parameters.ts`;
- `tables.ts`;
- `well.ts`;
- `route.ts`.

Regra pratica:

- tipos usados apenas por um datasource podem ficar junto do datasource;
- tipos compartilhados pela UI ou por varias camadas devem ficar em `src/types`.

## Fluxo de Dados Ponta a Ponta

Exemplo usando a hierarquia de ativos:

```text
Usuario abre tela de simulacao
  -> SimulationPage usa useGetHierarchyTree()
    -> lib/domain/Hierarchy/get-hierarchy.use-case.ts
      -> lib/data/Hierarchy/get-hierarchy.datasource.ts
        -> GET /assets/hierarchy via Axios
          -> backend/api/routes/hierarchyProviderRoutes.py
            -> backend/application/hierarchyProvider.py
              -> backend/infrastructure/databases/hierarchyCache.py
              -> backend/domain/entities/hierarchyProvider.py
        <- resposta JSON da API
      <- mapper adapta nomes e estrutura
    <- React Query entrega data/loading/error
  -> componente renderiza arvore, loading ou erro
```

Esse e o padrao mais importante da arquitetura: a tela nao fala direto com endpoint cru, e a rota Flask nao concentra regra de dominio.

## Como Adicionar uma Nova Feature

Use este checklist quando for criar uma funcionalidade parecida em outro app.

### Backend

1. Criar ou atualizar entidade/regra em `backend/domain/entities`.
2. Criar o caso de uso em `backend/application`.
3. Criar acesso externo em `backend/infrastructure`, se precisar.
4. Criar rota em `backend/api/routes`.
5. Registrar o Blueprint em `backend/app.py`.
6. Adicionar testes em `backend/tests/unit`.
7. Adicionar fixtures em `backend/tests/fixtures`, se necessario.

### Frontend

1. Criar tipos compartilhados em `frontend/src/types`, se necessario.
2. Criar datasource em `frontend/src/lib/data/<Feature>`.
3. Criar model da API em `*.datasource.model.ts`.
4. Criar mapper em `*.map.ts`.
5. Criar hook/caso de uso em `frontend/src/lib/domain/<Feature>`.
6. Criar componentes especificos em `frontend/src/components/<feature>`.
7. Criar ou atualizar pagina em `frontend/src/app/<Feature>`.
8. Registrar rota em `frontend/src/lib/constants/routes.ts` e `frontend/src/routes/private.routes.tsx` ou `public.routes.tsx`.

## Guidelines para Documentacao Swagger

O backend ja possui uma documentacao OpenAPI/Swagger servida pela propria aplicacao Flask.

Arquivos principais:

```text
backend/static/dist/
|-- wellRAMS.yaml          # Arquivo OpenAPI principal
|-- index.html             # Swagger UI
|-- paths/                 # Documentacao dos endpoints por modulo
|   |-- healthRoutes.yaml
|   |-- graphProvider.yaml
|   |-- hierarchyProvider.yaml
|   |-- reliawellProvider.yaml
|   |-- uepProvider.yaml
|   |-- uepWellsProvider.yaml
|   |-- uoProvider.yaml
|   |-- uoUepsProvider.yaml
|   `-- wellProvider.yaml
```

Rotas de documentacao:

- `GET /docs`: abre a interface Swagger UI;
- `GET /wellRAMS.yaml`: retorna o arquivo OpenAPI principal.

### Padrao Atual

O arquivo `wellRAMS.yaml` deve funcionar como indice da API. Ele declara os metadados gerais, os servidores e os caminhos principais.

Cada endpoint deve apontar para um arquivo menor dentro de `backend/static/dist/paths`.

Exemplo:

```yaml
paths:
  /assets/hierarchy:
    $ref: './static/dist/paths/hierarchyProvider.yaml#/hierarchy'
```

No arquivo especifico:

```yaml
hierarchy:
  get:
    summary: Retorna a hierarquia completa de ativos
    description: >-
      Busca no storage o arquivo de hierarquia oficial e processa os dados para
      gerar uma arvore aninhada completa.
    responses:
      '200':
        description: Arvore hierarquica completa retornada com sucesso.
```

### Checklist para Documentar um Endpoint

Sempre que criar ou alterar uma rota em `backend/api/routes`, atualize tambem a documentacao Swagger.

Para cada endpoint, documente:

- metodo HTTP: `get`, `post`, `put`, `delete` etc.;
- `summary`: frase curta dizendo o que o endpoint faz;
- `description`: explicacao objetiva do fluxo, origem dos dados e regras importantes;
- parametros de path, query ou header, quando existirem;
- corpo da requisicao (`requestBody`) em endpoints `POST`, `PUT` ou `PATCH`;
- respostas de sucesso, principalmente `200`, `201` ou `204`;
- respostas de erro esperadas, como `400`, `401`, `404`, `422` e `500`;
- schema JSON de entrada e saida;
- exemplos realistas, sem credenciais, tokens, nomes sensiveis ou dados privados.

### Como Nomear e Organizar

Use um arquivo por grupo de rotas/modulo:

```text
backend/api/routes/graphProviderRoutes.py
backend/static/dist/paths/graphProvider.yaml
```

O nome interno usado no `$ref` deve ser curto e estavel:

```yaml
/getGraphs:
  $ref: './static/dist/paths/graphProvider.yaml#/getGraphs'
```

```yaml
getGraphs:
  post:
    summary: Retorna grafos dos pocos informados
```

Evite misturar endpoints de dominios diferentes no mesmo arquivo YAML. Isso facilita manutencao e revisao.

### Parametros

Documente parametros de query quando o endpoint receber valores pela URL.

Exemplo:

```yaml
parameters:
  - name: uepId
    in: query
    required: true
    description: Identificador da UEP/plataforma.
    schema:
      type: string
      example: "PLT0001"
```

Para parametros de path:

```yaml
parameters:
  - name: id
    in: path
    required: true
    description: Identificador do recurso.
    schema:
      type: string
```

### Request Body

Endpoints que recebem JSON devem declarar `requestBody`.

Exemplo:

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        required:
          - wellIDs
        properties:
          wellIDs:
            type: array
            description: Lista de IDs dos pocos.
            items:
              type: string
            example: ["121542", "121543"]
```

### Responses

Toda resposta deve ter `description`. Quando retornar JSON, inclua `content`, `schema` e exemplos.

Exemplo:

```yaml
responses:
  '200':
    description: Dados retornados com sucesso.
    content:
      application/json:
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                type: object
  '400':
    description: Requisicao invalida.
    content:
      application/json:
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Missing required parameter: wellIDs"
  '500':
    description: Erro interno inesperado.
```

### Schemas e Tipos

Prefira schemas explicitos. Evite `additionalProperties: true` quando a estrutura for conhecida.

Use:

- `type: string` para textos e IDs;
- `type: number` para numeros decimais;
- `type: integer` para contagens e IDs numericos;
- `type: boolean` para flags;
- `type: array` com `items`;
- `type: object` com `properties`;
- `nullable: true` quando o campo puder ser `null`.

Quando uma resposta for recursiva ou muito grande, documente pelo menos os campos principais e explique a estrutura na `description`.

### Erros

Mantenha um formato de erro previsivel na documentacao.

Exemplo recomendado:

```yaml
type: object
properties:
  error:
    type: string
    example: "Resource not found."
  message:
    type: string
    example: "The requested graph file was not found in storage."
```

Se a API retornar apenas `error`, documente apenas `error`. O importante e a documentacao refletir o comportamento real da rota.

### Exemplos

Use exemplos que ajudem o consumidor da API.

Boas praticas:

- usar IDs ficticios ou fixtures publicas;
- manter exemplos pequenos;
- evitar payloads gigantes;
- nao expor dados sensiveis;
- usar valores coerentes com os fixtures do projeto quando possivel.

### Processo ao Criar uma Rota Nova

1. Criar a rota em `backend/api/routes/<modulo>Routes.py`.
2. Registrar o Blueprint em `backend/app.py`.
3. Criar ou atualizar `backend/static/dist/paths/<modulo>.yaml`.
4. Adicionar o `$ref` em `backend/static/dist/wellRAMS.yaml`.
5. Subir o backend com `python app.py`.
6. Abrir `http://localhost:5000/docs` ou `http://localhost:7001/docs`.
7. Conferir se o endpoint aparece no Swagger UI.
8. Testar se os exemplos, parametros e schemas batem com a resposta real.

### O que Evitar

- documentar endpoint que nao existe na rota Flask;
- mudar rota Flask e esquecer de atualizar `wellRAMS.yaml`;
- deixar `description` generica como "retorna dados";
- declarar campos obrigatorios que a API nao exige;
- esconder possiveis erros conhecidos;
- usar exemplos com dados reais sensiveis;
- criar schemas muito vagos quando a estrutura ja e conhecida;
- duplicar o mesmo endpoint em mais de um arquivo YAML.

## Template de Estrutura para Novo Web App

Uma estrutura inicial inspirada neste projeto:

```text
novo-projeto/
|-- backend/
|   |-- api/
|   |   `-- routes/
|   |-- application/
|   |-- domain/
|   |   `-- entities/
|   |-- infrastructure/
|   |   |-- apis/
|   |   `-- databases/
|   |-- tests/
|   |   |-- unit/
|   |   |-- integration/
|   |   `-- fixtures/
|   |-- app.py
|   |-- requirements.txt
|   `-- dockerfile
|
|-- frontend/
|   |-- public/
|   |-- src/
|   |   |-- app/
|   |   |-- assets/
|   |   |-- components/
|   |   |   `-- ui/
|   |   |-- lib/
|   |   |   |-- constants/
|   |   |   |-- data/
|   |   |   |-- domain/
|   |   |   |-- services/
|   |   |   `-- utils/
|   |   |-- routes/
|   |   |-- styles/
|   |   `-- types/
|   |-- package.json
|   |-- vite.config.js
|   |-- tsconfig.json
|   `-- dockerfile
|
|-- docker-compose.yml
|-- README.md
`-- CONTRIBUTING.md
```

## Convencoes Recomendadas

- Use nomes de modulos por dominio/feature: `Hierarchy`, `ReliaWell`, `Tables`, `Wells`.
- Mantenha rotas HTTP simples; a regra principal deve ficar em `application` e `domain`.
- Mantenha componentes React sem conhecimento do formato cru da API.
- Use mappers para adaptar `snake_case`, nomes legados ou estruturas externas para o formato que a UI espera.
- Use `React Query` para cache, loading, erro e sincronizacao de dados remotos.
- Use `Axios` centralizado em `lib/services/api.ts`.
- Use alias `@/` para imports a partir de `frontend/src`.
- Separe testes unitarios de testes de integracao.
- Mantenha fixtures versionadas quando elas nao tiverem dados sensiveis.

## Comandos Principais

Backend:

```bash
cd backend
pip install -r requirements.txt
python app.py
pytest tests/unit/ -v
```

Frontend:

```bash
cd frontend
npm install
npm run dev
npm run build
npm run lint
npm run type-check
```

Docker:

```bash
docker-compose up --build
```

No Docker Compose atual:

- backend: porta externa `7001`, apontando para Flask na porta `5000`;
- frontend: porta externa `7002`, apontando para Vite na porta `5173`;
- frontend usa `VITE_API_LOCAL_BASE_URL=http://localhost:7001`.

## Resumo Mental da Arquitetura

Pense no projeto como dois pipelines conectados por HTTP:

```text
Frontend
Tela -> Hook de dominio -> Datasource -> Axios -> API

Backend
Rota Flask -> Application -> Domain/Infrastructure -> Resposta JSON
```

Ao criar outro web app com a mesma estrutura, tente manter essa direcao de dependencias. Isso deixa o projeto mais facil de crescer, testar e reorganizar.
