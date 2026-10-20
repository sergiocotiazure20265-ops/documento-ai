# DocumentAI — Plano de implementação

## 1. Status e documentos de referência

**Implementação parcial autorizada em 20/10/2026.** O usuário autorizou somente a estrutura dos cinco projetos .NET 10, suas referências, API baseada em Controllers, projeto xUnit e documentação web Scalar em Development e Production. Domínio, casos de uso, endpoints de negócio, integração OpenAI e deploy continuam fora desta autorização.

Fontes do plano:

- [requirements.md](requirements.md): requisitos RF-01 a RF-09 e RNF-01 a RNF-07.
- [architecture.md](architecture.md): camadas, referências, serviços, integração, erros e decisões DA-01 a DA-09.
- [specifications.md](specifications.md): contrato público vigente, critérios CA-01 a CA-11 e cenários CT-01 a CT-28.

Para rotas e campos públicos, prevalece a especificação: `POST /api/documentos/analisar`, com `titulo` e `conteudo`, e resposta com `tipoDocumento`, `resumo`, `nivelRisco`, `palavrasChave` e `pontosAtencao`. O único outro endpoint previsto é `GET /health`.

A solution `DocumentoAI.sln` foi preservada e agora contém os cinco projetos previstos, com prefixo `DocumentAI`, além dos itens de documentação existentes.

DA-01 foi aprovada para a estrutura solicitada. As decisões restantes da integração, limites e operação não são aprovadas por esta entrega. A autorização para Scalar em ambos os ambientes está registrada em T08A.

## 2. Regras de execução e conclusão

As tarefas estão em ordem recomendada. A coluna de dependências contém pré-requisitos diretos; dependências transitivas também devem estar concluídas. Cada caixa representa a conclusão da tarefa inteira, não apenas seu início.

Uma tarefa será concluída quando sua entrega existir, os critérios indicados tiverem sido verificados e a evidência estiver registrada. Compilação não substitui teste de comportamento, e testes com integração controlada não substituem homologação real. As tarefas concluídas abaixo se limitam à autorização desta etapa.

As decisões da arquitetura serão resolvidas antes das tarefas afetadas, sem presumir aprovação pela existência deste plano. A autorização para iniciar e a aprovação de escolhas específicas devem ser registradas separadamente, respeitando o alcance da manifestação do usuário.

## 3. Preparação e decisões

| Status | ID | Tarefa pequena | Dependências | Critérios de conclusão |
| --- | --- | --- | --- | --- |
| [x] | T01 | Registrar a autorização para implementar. | Nenhuma. | Autorização parcial recebida em 20/10/2026: estrutura, referências e Scalar; demais funcionalidades e deploy não autorizados nesta etapa. |
| [x] | T02 | Confirmar organização e contrato da implementação. | T01. | DA-01 resolvida para `src/`, `tests/`, cinco projetos e referências da arquitetura. Contrato português preservado como planejado; nenhuma rota de negócio foi criada. |
| [ ] | T03 | Resolver as escolhas da integração. | T02. | DA-02 a DA-05 resolvidas: superfície da API OpenAI, versão compatível do SDK, modelo, timeout finito, retries e tratamento de recusa/truncamento definidos. Registrar compatibilidade com Structured Outputs, custo e critérios da escolha do modelo. O orçamento total único inclui tentativas e esperas e não é reiniciado por tentativa. |
| [ ] | T04 | Definir limites operacionais e de entrada. | T02. | DA-06 resolvida: limites de título, conteúdo e corpo, orçamento de saída, concorrência, metas de latência e comportamento de excesso especificados; sem truncamento silencioso. |
| [ ] | T05 | Aprovar regras de avaliação e conjunto de referência. | T02. | DA-09 resolvida; contagem de palavras aprovada; documentos e resultados esperados definidos para três riscos, múltiplos tipos, `INDETERMINADO`, ausência de pontos de atenção e instruções adversárias. |

## 4. Solução, projetos e referências

| Status | ID | Tarefa pequena | Dependências | Critérios de conclusão |
| --- | --- | --- | --- | --- |
| [x] | T06 | Preparar os projetos de produção na solution existente. | T02. | Quatro projetos de produção em `net10.0`, API com `AddControllers`/`MapControllers` e pasta Controllers. WeatherForecast e classes vazias dos templates removidos. Solution preservada; build aprovado. |
| [x] | T07 | Preparar o projeto xUnit. | T06. | `DocumentAI.Tests` em `net10.0`, com xUnit e host de teste. Teste vazio removido; dois casos reais verificam documentação e ausência de endpoints não implementados em Development e Production. |
| [x] | T08 | Configurar as referências entre camadas. | T07. | Domain sem referência de projeto; Application → Domain; Infrastructure → Application e Domain; API → Application e Infrastructure; Tests → quatro projetos de produção. Referências conferidas; build aprovado. |
| [x] | T08A | Configurar OpenAPI e Scalar em DEV e PROD. | T06, T07, T08. | `/scalar/v1` e `/openapi/v1.json` disponíveis nos dois ambientes; guia detalhado incluído no pacote e renderizado na web; dois testes xUnit aprovados. Operações futuras descritas como planejadas, sem rotas fictícias; sem OpenAI ou deploy. |

## 5. Domínio e aplicação

| Status | ID | Tarefa pequena | Dependências | Critérios de conclusão |
| --- | --- | --- | --- | --- |
| [ ] | T09 | Criar os modelos e a política de domínio. | T08. | Documento textual, resultado de análise e nível de risco representados; riscos restritos a `BAIXO`, `MEDIO`, `ALTO`; Domain designado como proprietário único das invariantes e da rubrica. Sem HTTP, prompts, schema, SDK, persistência ou DI no Domain. |
| [ ] | T10 | Definir os contratos e interfaces da Application. | T09. | Entradas e saídas próprias da Application; `IDocumentAnalysisService` e `IDocumentAnalysisProvider` assíncronos e com cancelamento; falhas conhecidas independentes de HTTP/SDK definidas. |
| [ ] | T11 | Implementar o serviço de análise e validação de entrada. | T10, T04. | Caso de uso rejeita entrada inválida antes de chamar o provedor, aplica limites aprovados e orquestra a análise por interface. Cancelamento propagado; sem bloqueio síncrono. |
| [ ] | T12 | Centralizar as invariantes e aplicá-las ao resultado. | T11, T05. | Domain implementa as regras de texto, resumo até 150 palavras, 1 a 10 palavras-chave únicas e pontos válidos obrigatórios para `MEDIO`/`ALTO`. Application reutiliza as regras, sem duplicação, e traduz violações conforme a origem: entrada inválida ou resultado externo inválido. Sem reparação silenciosa. |
| [ ] | T13 | Testar domínio e aplicação. | T12. | Testes xUnit passam para entrada inválida sem chamada ao provedor, três riscos, `INDETERMINADO`, pontos vazios permitidos, limites de 150/151 palavras, 0/1/10/11 palavras-chave, duplicidades e cancelamento. Utilizar fake controlado; cobrir as regras aplicáveis de CT-06 a CT-13, CT-17 e CT-26, incluindo as categorias distintas de falha. |

## 6. Integração OpenAI e composição

| Status | ID | Tarefa pequena | Dependências | Critérios de conclusão |
| --- | --- | --- | --- | --- |
| [ ] | T14 | Configurar opções e credenciais da integração. | T10, T03. | `OPENAI_API_KEY`, modelo e timeout obtidos do ambiente/opções conforme decisão aprovada; validação na inicialização; chave ausente impede início sem expor segredo; nenhuma credencial versionada. |
| [ ] | T15 | Traduzir a política interna em prompt e schema. | T12, T03, T05. | Application fornece ao provedor a política definida pelo Domain; Infrastructure traduz a rubrica e as restrições em template versionado e schema, sem uma segunda política independente. Documento tratado como dados; schema estrito com cinco campos, tipos, risco enumerado e propriedades extras desabilitadas. Mapeamento para o contrato português documentado. |
| [ ] | T16 | Implementar o adaptador assíncrono OpenAI. | T14, T15. | SDK oficial restrito à Infrastructure; título e conteúdo enviados; Structured Outputs habilitado; conclusão verificada antes da desserialização; resultado convertido sem expor tipos do SDK. |
| [ ] | T17 | Tratar falhas, timeout e cancelamento no adaptador. | T16. | Erros técnicos convertidos em falhas conhecidas; recusa, truncamento e saída inválida identificados; timeout distinto de desconexão; retries respeitam decisão e orçamento total; sem sucesso parcial ou vazamento de dados. |
| [ ] | T18 | Registrar dependências no host. | T11, T17. | API compõe serviços da Application e Infrastructure por DI; ciclos de vida e concorrência revisados; Controllers não resolvem serviços manualmente; provedor pode ser substituído em testes sem mudar produção. |
| [ ] | T19 | Testar o adaptador e a configuração sem rede. | T17, T18. | Transporte controlado exercita envio, tradução da política, schema, leitura da resposta e falhas, sem chamada real. CT-10, CT-14 a CT-17, CT-21, CT-27 e CT-28 cobertos na camada aplicável; orçamento total, configuração e ausência de segredos verificados; testes passam. |

## 7. Controllers, validações HTTP e erros

| Status | ID | Tarefa pequena | Dependências | Critérios de conclusão |
| --- | --- | --- | --- | --- |
| [ ] | T20 | Criar os contratos HTTP em português. | T10, T12. | Request com `titulo` e `conteudo`; response com exatamente os cinco campos definidos em specifications.md; tipos e nomes serializados corretos; mapeamento explícito para a Application, sem tipos SDK. |
| [ ] | T21 | Implementar o Controller de análise. | T18, T20. | Apenas `POST /api/documentos/analisar` para análise; serviço chamado por interface com cancelamento; sucesso retorna `200` e JSON; sem lógica de prompt no Controller ou alias em inglês. |
| [ ] | T22 | Adicionar validação de transporte e contrato de entrada. | T21, T04. | Campos ausentes, nulos, vazios, em branco ou de tipo incorreto e corpo inválido retornam `400`; conteúdo não suportado retorna `415`; nenhum desses casos chama a IA. Limites e tratamento de excesso seguem decisão documentada. |
| [ ] | T23 | Centralizar os erros e a correlação. | T22, T17, T03. | Problem Details com `type`, `title`, `status`, `traceId`; `errors` no `400` com chaves públicas ou `body`; falhas mapeadas para `500`, `502`, `504`; sem dados internos. Logs correlacionados e sem documento, prompt, chave ou resposta integral. |
| [ ] | T24 | Implementar o Health Check local. | T18. | Somente `GET /health`; `200` com estado JSON `Healthy`; estado local não saudável retorna `503` com `Unhealthy`; não chama OpenAI nem revela configuração. |
| [ ] | T25 | Criar os testes HTTP em host controlado. | T23, T24. | `WebApplicationFactory` com provedor substituído e configuração fictícia válida; CT-01 a CT-20 cobertos nas partes HTTP aplicáveis, incluindo respostas de erro e zero chamadas para entrada inválida/health. Testes passam sem rede e chave real. |

### Verificação automatizada das fronteiras

| Status | ID | Tarefa pequena | Dependências | Critérios de conclusão |
| --- | --- | --- | --- | --- |
| [ ] | T25A | Criar verificações automatizadas de arquitetura. | T08, T25. | CT-25 passa: referências de projeto permitidas, sem ciclos; SDK restrito à Infrastructure; Controllers sem uso de Domain, Infrastructure ou SDK; uso da Infrastructure na API limitado à composição. Executar junto de `dotnet test`, sem rede e sem exigir biblioteca adicional. Revisar responsabilidades que não possam ser comprovadas apenas por dependências. |

## 8. Publicação e validação final

| Status | ID | Tarefa pequena | Dependências | Critérios de conclusão |
| --- | --- | --- | --- | --- |
| [ ] | T26 | Resolver acesso, dados e ambiente de publicação. | T03, T04. | DA-07 e DA-08 resolvidas: público/restrições de acesso, documentos permitidos, política de dados aplicável, plano/região, sistema operacional, modalidade de publicação e retenção/destino de logs definidos. Eventual mudança de escopo refletida no SDD antes de implementação adicional. |
| [ ] | T27 | Configurar o pacote e o procedimento de publicação. | T25, T26. | Publicação da API compatível com .NET 10; artefato gerável sem Tests e sem segredos; configurações de ambiente e Health Check documentadas; procedimento de publicação e retorno à versão anterior descrito. Esta tarefa prepara a publicação, sem presumir que o ambiente já foi atualizado. |
| [ ] | T28 | Validar a aplicação localmente. | T13, T19, T25, T25A, T27. | Restauração, compilação, `dotnet test`, verificações automatizadas de arquitetura e geração do pacote passam; suíte rotineira não usa rede externa; revisão confirma regras centralizadas no Domain, assincronia, DI e somente os dois endpoints previstos. CA-01 a CA-07, CA-10 e CA-11 verificados no alcance local. |
| [ ] | T29 | Publicar a versão validada no ambiente aprovado. | T28, T26. | Escopo de autorização contempla a publicação; pacote validado implantado no App Service definido; variáveis configuradas pelo ambiente, HTTPS disponível e ausência de segredos no artefato confirmada. |
| [ ] | T30 | Homologar a integração real e a qualidade da análise. | T29, T05. | CT-22 a CT-24 executados com modelo/configuração aprovados e documentos permitidos; Health Check `200`, entrada inválida `400` e análise real `200` em português; conjunto semântico atende tipos, fatos, riscos e pontos esperados. Evidências não incluem conteúdo sensível ou credenciais. |
| [ ] | T31 | Consolidar o aceite e a documentação final. | T30. | Cada RF, RNF, CA e CT possui evidência e resultado; todos os critérios obrigatórios passam; pendências resolvidas ou mudanças de escopo explicitamente aprovadas; documentos refletem o comportamento entregue. Somente então marcar a implementação como concluída. |

## 9. Marcos e rastreabilidade

| Marco | Tarefas | Evidência principal |
| --- | --- | --- |
| Início autorizado e escolhas documentadas | T01 a T05. | Autorização e decisões aprovadas, sem presumir consentimento. |
| Estrutura compilável | T06 a T08. | Cinco projetos .NET 10 na solution e referências corretas. |
| Regras e caso de uso verificáveis | T09 a T13. | RF-02 a RF-08 no domínio/aplicação; testes unitários. |
| Integração isoladamente verificável | T14 a T19. | RF-03 a RF-08 e RNF-02 a RNF-05; testes do adaptador/configuração. |
| Contrato HTTP e fronteiras verificáveis | T20 a T25, T25A. | RF-01, RF-02, RF-08, RF-09, RNF-05 e CA-11; cenários HTTP e verificações de arquitetura. |
| Aplicação preparada e validada localmente | T26 a T28. | RNF-01, RNF-03, RNF-06 e preparação de RNF-07. |
| Aplicação publicada e aceita | T29 a T31. | RNF-07, CA-08 e CA-09; CT-22 a CT-24; matriz final de aceite. |

## 10. Registro de execução futuro

Ao concluir uma tarefa, marcar sua caixa e registrar: ID, entrega alterada, verificação realizada, resultado e pendências. Uma tarefa com dependência não atendida ou critério reprovado permanece aberta. Falhas encontradas na homologação retornam à tarefa responsável e exigem nova verificação do comportamento afetado.

### Entrega de 20/10/2026 — estrutura e documentação web

- T01, T02, T06, T07, T08 e T08A concluídas no escopo parcial autorizado.
- Projetos: `src/DocumentAI.API`, `src/DocumentAI.Application`, `src/DocumentAI.Domain`, `src/DocumentAI.Infrastructure` e `tests/DocumentAI.Tests`, todos `net10.0`.
- API registrada para Controllers, sem Controller de negócio ainda; camadas internas contêm somente seus projetos, sem modelos ou serviços antecipados.
- OpenAPI `Microsoft.AspNetCore.OpenApi` 10.0.9 e Scalar.AspNetCore 2.18.2; Microsoft.OpenApi fixado em 2.7.5 para corrigir o alerta transitivo NU1903 detectado no primeiro restore.
- `dotnet restore DocumentoAI.sln`: aprovado após liberação de acesso ao NuGet; dependências restauradas sem o alerta de vulnerabilidade inicial.
- `dotnet build DocumentoAI.sln --no-restore`: aprovado, zero avisos e zero erros.
- `dotnet test DocumentoAI.sln --no-restore`: 2 aprovados, 0 falhas. Verifica HTML/JavaScript Scalar e JSON OpenAPI em Development e Production; endpoints de análise, health e WeatherForecast retornam `404` nesta etapa.
- `dotnet publish src/DocumentAI.API/DocumentAI.API.csproj --configuration Release --no-restore --output artifacts/publish`: pacote local gerado; guia incluído e página Scalar renderizada no navegador pelo pacote em Production. Isso não corresponde a deploy e não conclui T27 ou T29.
- T03 a T05 e tarefas de domínio, serviços, integração, endpoints, erros e publicação permanecem abertas. T25/T25A não foram concluídas: os testes desta entrega cobrem somente a documentação e o escopo inicial.
- Nenhum `SKILL.md`, workflow demonstrativo ou recurso Azure alterado. Nenhuma credencial ou SDK OpenAI adicionado.

### Entrega de 20/10/2026 — CI e versionamento da estrutura

- Autorizados commit/push da implementação inicial e substituição das mensagens demonstrativas por build e testes reais no GitHub Actions.
- `.github/workflows/pipeline.yml`: dois jobs em Ubuntu 24.04, com SDK .NET 10 e configuração Release. Tests depende de Build e executa a suíte xUnit sem OpenAI real.
- Job de Deploy removido expressamente; não há autenticação, publicação ou alteração de recursos Azure. T27 e T29 permanecem abertas.
- README atualizado para refletir os comandos e o escopo atual da pipeline.

### Relatório de CI por e-mail — 20/10/2026

- Solicitado envio para `sergio.coti@gmail.com` em cada execução; remetente confirmado pelo usuário como a mesma conta Gmail.
- Etapa final em workflow de notificação separado, acionado na conclusão de Build e Tests por `workflow_run`, incluindo falhas e cancelamentos. Consulta os jobs da tentativa correta e lista cada passo, conclusão, duração, comandos e links dos logs.
- Código confiável da branch padrão, token somente de leitura de Actions/Contents e envio via Gmail SMTP TLS, sem dependência de actions de e-mail externas.
- Credencial necessária: Repository secret `SMTP_PASSWORD` com senha de app do Gmail. O envio real permanece dependente de seu cadastro e verificação; os testes não usam senha real nem enviam e-mails.
- Quatro testes Python locais aprovados: resultados de execução/passos, ausência de credencial, transporte SMTP simulado e paginação por tentativa. A suíte passou a ser executada também no job Tests.
- Deploy continua ausente e as tarefas de implementação da integração OpenAI permanecem abertas.
