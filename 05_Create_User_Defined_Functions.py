# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# DBTITLE 1,Criar UDF get_return_policy
# CELULA 1: Criar uma Função Definida pelo Usuário (UDF) no Unity Catalog
#
# Esta UDF (User Defined Function) é uma função SQL que:
#   - Recebe como entrada o NOME de uma política (ex: "Return Policy", "Refund Policy")
#   - Retorna uma TABELA com 3 colunas: policy, policy_details, last_updated
#   - Busca os dados na tabela agentic_catalog.agentic_schema.policies
#
# Por que usar uma UDF em vez de um SELECT direto?
#   - Reutilização: qualquer notebook, query ou Genie Agent pode chamar get_return_policy("...")
#   - Encapsulamento: a lógica de filtro fica centralizada em um só lugar
#   - Governança: a função fica registrada no Unity Catalog com permissões controláveis
#
# Sintaxe CREATE OR REPLACE FUNCTION:
#   - CREATE OR REPLACE: se a função já existir, substitui; senão, cria nova
#   - RETURNS TABLE (...): define o formato da tabela de saída (schema fixo)
#   - LANGUAGE SQL: a função é escrita em SQL (também suporta Python/Scala/Java)
#   - RETURN (SELECT ...): o corpo da função é uma query que retorna os dados

spark.sql(f"""
-- Create a function to retrieve company policy details
CREATE OR REPLACE FUNCTION agentic_catalog.agentic_schema.get_return_policy(
    policy_name STRING COMMENT 'Policy name to return. Example policies: Account Cancellation Policy, Exchange Policy, Refund Policy, Warranty Policy, Privacy Policy, Return Policy'
    )
    RETURNS TABLE (
    policy           STRING,
    policy_details   STRING,
    last_updated     DATE
    )
    COMMENT 'Returns the details of the Return Policy'
    LANGUAGE SQL
    RETURN (
    SELECT
    policy,
    policy_details,
    last_updated
    FROM agentic_catalog.agentic_schema.policies
    WHERE policy = policy_name
    LIMIT 1
    );
    """)
####################################################################################

# COMMAND ----------

# DBTITLE 1,Preview: tabela policies
# MAGIC %sql
# MAGIC -- CELULA 2: Visualizar todos os dados da tabela policies
# MAGIC -- Esta query mostra o conteúdo bruto da tabela para confirmar que os dados existem
# MAGIC -- antes de testarmos a UDF criada na célula anterior.
# MAGIC
# MAGIC select * from agentic_catalog.agentic_schema.policies

# COMMAND ----------

# DBTITLE 1,Testar UDF get_return_policy
# MAGIC %sql
# MAGIC -- CELULA 3: Testar a UDF get_return_policy
# MAGIC -- Aqui chamamos a função criada na Célula 1, passando "Return Policy" como argumento.
# MAGIC -- O resultado deve ser uma tabela com 1 linha contendo os detalhes da política de retorno.
# MAGIC --
# MAGIC -- Sintaxe: select * from <catalog>.<schema>.<nome_da_funcao>(argumento)
# MAGIC -- A função se comporta como uma tabela virtual que só retorna linhas que correspondem ao filtro interno.
# MAGIC
# MAGIC select * from agentic_catalog.agentic_schema.get_return_policy("Return Policy")

# COMMAND ----------

# DBTITLE 1,Criar UDF get_service_history
# CELULA 4: Criar uma segunda UDF no Unity Catalog — get_service_history
#
# Esta UDF:
#   - Recebe como entrada o EMAIL de um cliente (ex: "nicolas.pelaez@example.com")
#   - Retorna uma TABELA com 3 colunas:
#       * returns_last_12_months: quantas ocorrências de serviço/atendimento aquele cliente teve
#       * issue_category: a categoria do problema (ex: produto defeituoso, atraso na entrega)
#       * todays_date: a data atual (gerada com now())
#   - Busca na tabela agentic_catalog.agentic_schema.cust_service_data
#   - Agrupa por issue_category, contando quantas ocorrências de cada categoria o cliente teve
#
# Detalhes da query interna:
#   - count(*) conta as linhas (ocorrências) por categoria
#   - GROUP BY issue_category agrupa as ocorrências por tipo de problema
#   - now() retorna o timestamp atual — convertido automaticamente para DATE no retorno
#
# Esta função será usada posteriormente no curso, possivelmente por um agente Genie
# ou por outro notebook que precise do histórico de atendimento de um cliente.

####################################################################################
# Create two functions we will use later in the course
spark.sql(f"""
-- Create a function to get service history by user
CREATE OR REPLACE FUNCTION agentic_catalog.agentic_schema.get_service_history(
    user_email STRING COMMENT 'User email to retrieve order history'
    )
    RETURNS TABLE (
    returns_last_12_months INT,
    issue_category STRING, 
    todays_date DATE
    )
    COMMENT 'This takes the user_name of a customer as an input and returns the number of returns and the issue category'
    LANGUAGE SQL
    RETURN(
    SELECT count(*) as returns_last_12_months, issue_category, now() as todays_date
    FROM agentic_catalog.agentic_schema.cust_service_data 
    WHERE email = user_email
    GROUP BY issue_category
    );""")

# COMMAND ----------

# DBTITLE 1,Preview: tabela cust_service_data
# MAGIC %sql
# MAGIC -- CELULA 5: Visualizar todos os dados da tabela cust_service_data
# MAGIC -- Assim como na Célula 2, aqui inspecionamos a tabela fonte para confirmar
# MAGIC -- que os dados existem e ver quais emails e categorias de problema estão disponíveis.
# MAGIC
# MAGIC select * from agentic_catalog.agentic_schema.cust_service_data

# COMMAND ----------

# DBTITLE 1,Testar UDF get_service_history
# MAGIC %sql
# MAGIC -- CELULA 6: Testar a UDF get_service_history
# MAGIC -- Chamamos a função criada na Célula 4 passando o email de um cliente específico.
# MAGIC -- O resultado mostra quantas ocorrências de atendimento ele teve por categoria de problema.
# MAGIC --
# MAGIC -- Exemplo de uso em um agente Genie:
# MAGIC --   O Genie pode chamar esta UDF quando um usuário pergunta:
# MAGIC --   "Qual é o histórico de problemas do cliente nicolas.pelaez@example.com?"
# MAGIC
# MAGIC select * from agentic_catalog.agentic_schema.get_service_history("nicolas.pelaez@example.com")