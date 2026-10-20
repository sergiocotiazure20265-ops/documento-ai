# DocumentAI

API corporativa planejada em ASP.NET Core para análise inteligente de documentos textuais utilizando OpenAI.

## Estado atual

O repositório contém a solution `DocumentoAI.sln`, a documentação de desenvolvimento orientado a especificações (SDD), as instruções para agentes e três Agent Skills locais. Os cinco projetos .NET ainda não foram criados; não há API executável nem testes automatizados implementados.

O workflow inicial é demonstrativo: Build, Test e Deploy apenas exibem mensagens. Uma execução verde desse workflow não comprova compilação, testes ou publicação da aplicação.

A implementação da API continua aguardando autorização. A preparação do repositório e do workflow não representa aprovação das decisões arquiteturais pendentes.

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

Não é necessário configurar credenciais para este workflow demonstrativo. A API futura validará as opções na inicialização. Modelo, versão do SDK, limites, retries e ambiente Azure ainda dependem das decisões do SDD.

## Pipeline inicial

O arquivo [pipeline.yml](.github/workflows/pipeline.yml) executa em push para `main`, pull requests destinados a `main` e acionamento manual.

1. **Build:** exibe uma mensagem de teste.
2. **Test:** aguarda Build e exibe uma mensagem de teste.
3. **Deploy:** aguarda Test e exibe uma mensagem de teste.

Nenhum job compila, executa testes da aplicação, autentica no Azure ou publica recursos. O token tem somente permissão de leitura do conteúdo. A evolução para publicação real deverá incluir validação do pacote, autenticação federada OIDC, configuração do ambiente e autorização de deploy conforme o SDD e as skills.

## Desenvolvimento futuro

Após autorização, seguir [tasks.md](docs/tasks.md). A solution pode ser aberta no Visual Studio; atualmente possui itens de documentação e não oferece uma aplicação para iniciar.

Quando os projetos forem implementados, o fluxo de verificação previsto será restauração, build, `dotnet test` e geração do pacote. Testes rotineiros não deverão depender de rede externa ou da OpenAI real; a homologação real será separada e executada com configuração aprovada.

O `.gitignore` exclui estado local do Visual Studio, saídas de compilação/testes e formatos comuns de credenciais. Documentos e `.agents/skills/` são versionados.
