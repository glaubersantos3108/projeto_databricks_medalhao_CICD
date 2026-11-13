projeto_databricks_medalhao_CICD

Um pipeline de dados em arquitetura medalhão (bronze, silver e gold) no Azure Databricks, com deploy automatizado de dev para produção usando Databricks Asset Bundles e GitHub Actions.

É um projeto de estudo. O foco principal é o caminho do código até a produção (ambientes separados, identidades por ambiente, governança com Unity Catalog e aprovação manual antes do prod). A parte de modelagem e qualidade de dados é mais simples, e as limitações estão listadas com franqueza mais abaixo.

O que ele faz

Arquivos CSV de uma base de exemplo (marcas, categorias, clientes, itens de pedido, pedidos, produtos, funcionários, estoques e lojas) ficam em um volume externo do Unity Catalog, apontando para um container do ADLS Gen2. Um job do Databricks lê esses arquivos e os leva pelas três camadas:

ADLS Gen2 (CSV)
   │  volume externo do Unity Catalog
   ▼
BRONZE  ──  9 tabelas, uma por arquivo (ingestão em paralelo)
   │        └─ validate_camada_bronze
   ▼
SILVER  ──  clientes, pedidos e produtos
   │        └─ validate_camada_silver
   ▼
GOLD    ──  orders_gold
Cada camada só começa quando a validação da anterior termina com sucesso.
O job roda em compute serverless e avisa por e-mail se alguma task falhar.
O catálogo é recebido como parâmetro pelos notebooks, então o mesmo código roda em dev e em prod sem alteração.
Estrutura do repositório
databricks.yml                     definição do bundle, variáveis e targets (dev e prod)
resources/projeto_completo.job.yml o job: tasks, dependências e parâmetros
src/notebooks/bronze|silver|gold   notebooks de cada camada
.github/workflows/ci-cd.yml        validação, deploy em dev e deploy em prod
tests/, fixtures/, setup.py        sobras do template, sem uso hoje
Ambientes
	dev	prod
Workspace	Azure Databricks de dev	Azure Databricks de prod (outro workspace)
Catálogo	lugus_databricks_dev	lugus_databricks_prod
Modo do bundle	development	production
Identidade do deploy no CI	service principal de dev	service principal de prod
Pasta do bundle	pasta do usuário que fez o deploy	pasta do service principal de prod

A estrutura é a mesma nos dois (schemas bronze, silver e gold, volume default.resources, pasta bronze/ com os CSVs). Só o catálogo muda. Os dados de cada ambiente são independentes: o que está no dev não é copiado para o prod.

CI/CD

O workflow .github/workflows/ci-cd.yml faz o seguinte:

validate: databricks bundle validate -t dev, em todo pull request e push na main.
deploy-dev: databricks bundle deploy -t dev, a cada push na main.
deploy-prod: databricks bundle deploy -t prod, depois do dev e somente após aprovação manual (Required reviewers no environment de prod).

A autenticação usa um service principal do Microsoft Entra ID por ambiente, guardado como secret nos environments do GitHub. O deploy só publica o job. Ele não executa o pipeline.

Como reproduzir

Uma vez, fora do repositório (feito à mão):

Storage account com namespace hierárquico (ADLS Gen2) e um container para os CSVs.
Access Connector for Azure Databricks, com a role Storage Blob Data Contributor no storage.
No Unity Catalog: storage credential, external location (URL no formato abfss://<container>@<conta>.dfs.core.windows.net/), catálogo, schemas bronze, silver e gold, e volume externo default.resources.
CSVs na pasta bronze/ do volume, com nome igual ao esperado pelos notebooks (por exemplo, brands.csv).
App registration no Entra ID para cada ambiente, adicionado ao workspace correspondente, com GRANT no catálogo e no volume.
No GitHub: environments Databricks_DEV e Databricks_PROD, com os secrets ARM_CLIENT_ID e ARM_CLIENT_SECRET de cada um, e o secret ARM_TENANT_ID no repositório.

Rodando localmente (Databricks CLI autenticado no workspace):

databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run pipeline_medalhao_job -t dev
Decisões que valem registrar
Só serverless. Os workspaces usados só aceitam compute serverless, então o job não define cluster e usa tasks de notebook.
Sem wheel. O template original empacotava o código como wheel. Troquei por notebooks, que combinam melhor com o formato do projeto.
Um service principal por ambiente. Eu não tenho permissão de admin da conta Databricks, e um mesmo service principal não pôde ser atribuído aos dois workspaces. Separar acabou sendo também uma boa prática: se o segredo de dev vazar, o prod continua protegido.
Pasta do bundle no prod. Fica na pasta do próprio service principal, e não em /Workspace/Shared, que daria permissão de escrita a todos os usuários do workspace.
Limitações conhecidas

Dados e modelagem

A base é de exemplo e o escopo é pequeno. A gold tem uma tabela só (orders_gold), sem modelo dimensional nem métricas de negócio.
Não há tratamento sério de qualidade de dados além das validações entre camadas.

Bronze

Lê um arquivo fixo por tabela e grava com overwrite. Não é incremental e não guarda histórico.
Usa inferSchema e não registra data de ingestão nem arquivo de origem.
São 9 notebooks muito parecidos. Uma ingestão parametrizada (uma lista de tabelas) evitaria a duplicação.

CI/CD

O workflow valida e implanta, mas não roda testes e não executa o job em dev antes de liberar o prod.
A pasta tests/ e o setup.py são restos do template e não testam nada deste projeto.
A autenticação usa client secret, que expira e precisa ser renovado. A recomendação da Databricks é federação de identidade (OIDC), que dispensa o segredo.
Deploys locais e deploys pelo CI usam identidades diferentes, então o dev pode ficar com duas cópias do job.

Infraestrutura

Catálogos, schemas, volumes e external locations são criados à mão em cada ambiente, e não por código. Com o tempo, dev e prod podem divergir.
O job não tem agendamento: roda sob demanda.
Próximos passos
Ingestão da bronze incremental (Auto Loader ou COPY INTO), com colunas de rastreio.
Silver com MERGE e tratamento de duplicados.
Gold com métricas de negócio e modelo dimensional.
Testes de transformação com pytest e um smoke test (rodar o job em dev) no CI antes do prod.
Trocar o client secret por OIDC.
Criar a infraestrutura (catálogos, schemas, volumes) por código.
