# DocumentAI

API corporativa planejada em ASP.NET Core para análise inteligente de documentos textuais utilizando OpenAI.

## Estado atual

O repositório contém a solution `DocumentoAI.sln`, cinco projetos .NET 10 com referências configuradas, a documentação SDD, instruções para agentes e três Agent Skills locais. O host API já executa a documentação web OpenAPI/Scalar. Dois testes xUnit verificam essa documentação em Development e Production.

O workflow executa build e testes reais em Release com .NET 10. A etapa de Deploy foi removida por solicitação do usuário; a pipeline não publica a aplicação.

A estrutura e a documentação web foram autorizadas. Endpoints de análise e Health Check, modelos de domínio, serviços e integração OpenAI ainda não foram implementados. A documentação os identifica como contratos planejados. As demais decisões arquiteturais permanecem pendentes.

## Executar a documentação web

Requer SDK .NET 10. Na raiz da solução:

```powershell
dotnet restore DocumentoAI.sln
dotnet build DocumentoAI.sln --no-restore
dotnet test DocumentoAI.sln --no-build --no-restore
dotnet run --project src/DocumentAI.API --launch-profile http
```

Abrir [Scalar local](http://localhost:5249/scalar/v1) ou [OpenAPI JSON](http://localhost:5249/openapi/v1.json). O perfil `https` utiliza `https://localhost:7115/scalar/v1` e exige certificado local confiável.

Para executar em Production localmente, sem utilizar o perfil Development:

```powershell
$env:ASPNETCORE_ENVIRONMENT = 'Production'
dotnet run --project src/DocumentAI.API --no-launch-profile --urls http://localhost:5249
```

No domínio de produção futuro, as mesmas rotas estarão disponíveis por HTTPS. OpenAPI e Scalar são mapeados em ambos os ambientes; o guia [api-reference.md](docs/api-reference.md) é incluído no pacote da API. Nesta fase, não há operações de negócio no cliente interativo, e `/api/documentos/analisar` e `/health` retornam `404`. Nenhuma chave OpenAI é necessária para iniciar a documentação.

## Objetivo e funcionalidades previstas

- Receber título e conteúdo textual de um documento por HTTP POST.
- Validar os campos obrigatórios antes de chamar a IA.
- Identificar o tipo do documento, produzir um resumo objetivo e extrair palavras-chave.
- Classificar o risco como `BAIXO`, `MEDIO` ou `ALTO` e identificar pontos de atenção.
- Retornar JSON estruturado e disponibilizar Health Check local.

Upload de arquivos, OCR, persistência, histórico e interface gráfica não fazem parte do escopo atual. Controles de acesso e políticas para uso corporativo permanecem sujeitos às decisões documentadas.

## Stack e arquitetura planejadas

.NET 10, ASP.NET Core com Controllers, Dependency Injection, interfaces, operações assíncronas com cancelamento, SDK oficial OpenAI, Structured Outputs e xUnit. Publicação futura no Azure App Service por GitHub Actions.

| Projeto planejado | Responsabilidade |
| --- | --- |
| `DocumentAI.API` | Controllers, contratos HTTP, configuração, DI, erros e Health Check. |
| `DocumentAI.Application` | Casos de uso, interfaces e orquestração das regras e integrações. |
| `DocumentAI.Domain` | Modelos, invariantes e política de análise, sem dependências externas. |
| `DocumentAI.Infrastructure` | Adaptador OpenAI, tradução da política para prompt/schema e falhas técnicas. |
| `DocumentAI.Tests` | Testes xUnit de domínio, aplicação, integração controlada, HTTP e arquitetura. |

Application referencia Domain; Infrastructure referencia Application e Domain; API referencia Application e Infrastructure, esta última somente para composição. Tests pode referenciar os quatro projetos de produção. As regras completas estão em [architecture.md](docs/architecture.md).

## Contrato HTTP previsto

Os endpoints abaixo são especificações futuras, ainda não disponíveis para consumo.

| Método | Endpoint | Descrição |
| --- | --- | --- |
| `POST` | `/api/documentos/analisar` | Analisar um documento textual. |
| `GET` | `/health` | Verificar disponibilidade local, sem chamada à OpenAI. |

Exemplo de entrada do POST:

```json
{
  "titulo": "Comunicado interno",
  "conteudo": "A reunião de apresentação da equipe ocorrerá na segunda-feira às 10h."
}
```

Exemplo ilustrativo de análise:

```json
{
  "tipoDocumento": "COMUNICADO",
  "resumo": "A reunião de apresentação da equipe está marcada para segunda-feira às 10h.",
  "nivelRisco": "BAIXO",
  "palavrasChave": ["reunião", "apresentação da equipe"],
  "pontosAtencao": []
}
```

O POST prevê `200` para sucesso, `400` para entrada inválida, `415` para tipo de conteúdo não suportado, `502` para falha de integração/saída incompatível, `504` para timeout e `500` para erro interno inesperado. Recusa e truncamento seguem a decisão pendente DA-05. Erros da aplicação utilizarão Problem Details com correlação, sem revelar dados internos.

Health Check saudável: HTTP `200` com `{"status":"Healthy"}`. Se a verificação local indicar indisponibilidade e o processo ainda responder: HTTP `503` com `{"status":"Unhealthy"}`. Isso não atesta disponibilidade da OpenAI.

Validações e cenários completos estão em [specifications.md](docs/specifications.md).

## Documentação SDD

| Documento | Conteúdo |
| --- | --- |
| [requirements.md](docs/requirements.md) | Requisitos funcionais, não funcionais e critérios de aceite. |
| [architecture.md](docs/architecture.md) | Camadas, referências permitidas, fluxo, credenciais, erros, testes e decisões pendentes. |
| [specifications.md](docs/specifications.md) | Endpoints, contratos JSON, validações e cenários de teste. |
| [tasks.md](docs/tasks.md) | Tarefas ordenadas, dependências e critérios de conclusão. |

## Instruções para agentes e skills

Leia [AGENTS.md](AGENTS.md) e os documentos de SDD antes de implementar. Implemente somente requisitos aprovados e execute build e testes quando houver projetos implementados. Não armazene chaves no código e não publique no Azure sem autorização.

| Skill | Uso |
| --- | --- |
| [dotnet-architecture](.agents/skills/dotnet-architecture/SKILL.md) | Implementar e revisar separação de camadas, DI, interfaces, assincronia e dependências. |
| [dotnet-testing](.agents/skills/dotnet-testing/SKILL.md) | Criar testes xUnit reproduzíveis, com serviços externos controlados e cenários positivos e negativos. |
| [azure-deployment](.agents/skills/azure-deployment/SKILL.md) | Preparar publicação autorizada, com Build, Test e Deploy separados, OIDC e proteção de segredos. |

## Configuração futura

| Variável prevista | Finalidade |
| --- | --- |
| `OPENAI_API_KEY` | Credencial OpenAI fornecida pelo ambiente, nunca versionada. |
| `OpenAI__Model` | Modelo compatível com Structured Outputs, a aprovar. |
| `OpenAI__TimeoutSeconds` | Orçamento total finito da integração, a aprovar. |

Não é necessário configurar credenciais para o workflow de build e testes. A API futura validará as opções de integração na inicialização. Modelo, versão do SDK OpenAI, limites, retries e ambiente Azure ainda dependem das decisões do SDD.

## Pipeline inicial

O arquivo [pipeline.yml](.github/workflows/pipeline.yml) executa em push para `main`, pull requests destinados a `main` e acionamento manual.

1. **Build:** checkout, instalação do SDK .NET 10, `dotnet restore DocumentoAI.sln` e `dotnet build DocumentoAI.sln --configuration Release --no-restore`.
2. **Tests:** aguarda Build, prepara um runner independente, restaura as dependências e executa `dotnet test DocumentoAI.sln --configuration Release --no-restore`, com compilação dos testes e logs detalhados.

Os jobs utilizam Ubuntu 24.04, SDK `10.0.x` e token com permissão somente de leitura do conteúdo. Não há job de Deploy, autenticação no Azure ou publicação de recursos. A evolução para publicação real dependerá de autorização e incluirá validação do pacote, autenticação federada OIDC e configuração do ambiente conforme o SDD e as skills.

## Desenvolvimento futuro

Seguir o escopo autorizado e o estado em [tasks.md](docs/tasks.md). A solution pode ser aberta no Visual Studio; selecionar `DocumentAI.API` como projeto de inicialização. A pasta Controllers está preparada, com os serviços de Controllers registrados; nenhum Controller de negócio foi criado nesta etapa.

O fluxo de verificação é restauração, build e `dotnet test`. Um pacote local pode ser gerado com `dotnet publish src/DocumentAI.API -c Release -o artifacts/publish`; a geração não realiza deploy. Os testes atuais não dependem de rede externa ou da OpenAI real; a homologação real será separada e executada com configuração aprovada.

O `.gitignore` exclui estado local do Visual Studio, saídas de compilação/testes e formatos comuns de credenciais. Documentos e `.agents/skills/` são versionados.
