# DocumentAI — Arquitetura

## 1. Objetivo e status

Proposta de arquitetura baseada em [requirements.md](requirements.md), para uma API corporativa em .NET 10 e ASP.NET Core. A solução utilizará Controllers, Dependency Injection, interfaces, serviços assíncronos, SDK oficial da OpenAI, Structured Outputs e xUnit.

Este documento descreve a estrutura futura. Não cria projetos, classes ou configurações executáveis. As escolhas explicitamente solicitadas e os requisitos existentes são premissas; as decisões adicionais da seção 11 são propostas pendentes de aprovação.

A solution existente mantém o nome `DocumentoAI.sln`. Os projetos usarão o prefixo `DocumentAI`, conforme solicitado. A aplicação será um único serviço implantável, organizado em camadas, sem banco de dados, filas ou processamento em segundo plano nesta etapa.

## 2. Organização da solução e responsabilidades

Organização proposta: projetos de produção em `src/`, projeto de testes em `tests/` e documentação em `docs/`. Todos os projetos terão como alvo `net10.0`.

| Projeto | Responsabilidades | Limites |
| --- | --- | --- |
| `DocumentAI.API` | Host ASP.NET Core; Controllers; contratos HTTP de entrada e saída; validação do transporte; serialização JSON; composição de DI; Health Check; conversão centralizada de falhas em respostas HTTP. | Não constrói prompts, não chama o SDK diretamente e não decide o risco do documento. |
| `DocumentAI.Application` | Orquestrar o caso de uso de análise; definir interfaces de entrada e integração; aplicar pré-condições do caso de uso; invocar invariantes e política do Domain; retornar resultados independentes de HTTP. | Não reimplementa invariantes do Domain nem referencia ASP.NET Core, SDK OpenAI ou detalhes de transporte do provedor. |
| `DocumentAI.Domain` | Representar o documento textual, o resultado de análise e o nível de risco; proteger invariantes de valores e coleções; manter conceitos de negócio independentes de infraestrutura. | Não possui dependências de outros projetos, DTOs HTTP, configuração, DI ou SDK. Não precisa de entidades persistidas ou repositórios neste escopo. |
| `DocumentAI.Infrastructure` | Implementar a interface de análise por IA; integrar o SDK; traduzir a política recebida em prompt e JSON Schema; validar protocolo e estrutura da saída; interpretar recusas e resultados incompletos; traduzir falhas técnicas; disponibilizar registros de DI e opções de integração. | Não define a rubrica de negócio, não conhece Controllers nem retorna status HTTP. Não expõe tipos do SDK nos contratos internos. |
| `DocumentAI.Tests` | Testes xUnit de domínio, aplicação, adaptação OpenAI e endpoints; fakes e respostas controladas; dados de referência; testes reais separados para homologação. | Não é referenciado por projetos de produção e não participa do pacote de publicação. |

Os nomes de componentes citados a seguir são contratos conceituais propostos, sem assinaturas ou implementação nesta etapa.

### Responsável por cada validação e política

| Responsável | Regras sob sua responsabilidade |
| --- | --- |
| API | Binding, tipos JSON, corpo e tipo de conteúdo; apresentação dos erros com os nomes públicos dos campos. Delega as invariantes textuais às regras internas, sem duplicar algoritmos de negócio. |
| Domain | Validade textual do documento e da análise; riscos permitidos; limite e contagem de palavras do resumo; quantidade e unicidade das palavras-chave; validade dos pontos de atenção e sua presença para `MEDIO`/`ALTO`; rubrica de risco e prevalência do maior risco sustentado. |
| Application | Pré-condições e limites aprovados do caso de uso; coordenação da criação dos objetos de domínio, fornecimento da política ao provedor e tradução de violações do Domain em falha de entrada ou de resultado, conforme a origem dos dados. |
| Infrastructure | Compatibilidade estrutural com o schema, desserialização, conclusão da resposta e falhas técnicas do provedor. Não decide limites ou critérios de classificação por conta própria. |

As invariantes terão uma única implementação no Domain, reutilizada pela Application. As restrições representadas no schema serão derivadas da política interna para orientar a geração, sem substituir a validação local. A suficiência semântica da classificação e das evidências será avaliada pelo conjunto de referência; exigir um ponto não vazio não comprova sua justificativa factual.

## 3. Referências permitidas entre projetos

| Projeto de origem | Referências diretas permitidas | Finalidade |
| --- | --- | --- |
| `DocumentAI.Domain` | Nenhuma. | Independência das regras de negócio. |
| `DocumentAI.Application` | `DocumentAI.Domain`. | Utilizar os conceitos e invariantes de negócio. |
| `DocumentAI.Infrastructure` | `DocumentAI.Application`, `DocumentAI.Domain`. | Implementar as portas de integração e mapear os resultados do provedor. |
| `DocumentAI.API` | `DocumentAI.Application`, `DocumentAI.Infrastructure`. | Executar casos de uso e compor as implementações no ponto de entrada. |
| `DocumentAI.Tests` | Todos os quatro projetos de produção. | Validar cada camada e o serviço integrado. |

A referência da API à Infrastructure serve à composição de DI na inicialização. Controllers devem depender apenas de contratos da Application. Os contratos de entrada e saída da Application serão próprios dessa camada, evitando que Controllers dependam diretamente de tipos do Domain ou do SDK.

São proibidas referências circulares, Application → Infrastructure, Domain → Application e qualquer camada de produção → Tests. O fluxo de execução chega à Infrastructure por uma interface definida na Application; isso não altera a direção das referências de compilação.

Testes automatizados de arquitetura deverão verificar as referências de projeto e os usos de tipos: ausência de ciclos, SDK limitado à Infrastructure e Controllers sem dependências do Domain, da Infrastructure ou do SDK. A referência da API à Infrastructure não autoriza seu uso fora da composição. Verificações de dependências complementam a revisão de responsabilidades e não comprovam, sozinhas, a ausência de regras de negócio em Controllers.

## 4. Interfaces, serviços e Dependency Injection

- `IDocumentAnalysisService`, na Application: porta do caso de uso consumida pelo Controller. Sua implementação, `DocumentAnalysisService`, orquestra validação, chamada de IA e verificação do resultado.
- `IDocumentAnalysisProvider`, na Application: porta para solicitar uma análise estruturada, sem tipos específicos da OpenAI. Sua implementação, `OpenAIDocumentAnalysisProvider`, pertence à Infrastructure.
- Objetos de transferência da Application: carregam título, conteúdo e resultado entre API e caso de uso. Os modelos de transporte do SDK ficam privados à Infrastructure.
- Política de análise: definida no Domain e fornecida pela Application ao provedor por contrato independente do SDK. Contém a rubrica e as restrições aprovadas; não contém prompts ou JSON Schema. A Infrastructure traduz essa política para o protocolo da OpenAI.
- Falhas tipadas na Application: representam entrada inválida, indisponibilidade do provedor, saída inválida e timeout, permitindo tradução uniforme na API sem acoplamento ao SDK.

O host da API será o ponto de composição. A Application e a Infrastructure poderão oferecer pontos de registro de seus serviços, chamados durante a inicialização. Não haverá resolução manual de serviços dentro de Controllers.

Proposta de ciclos de vida: serviço de aplicação e adaptador por requisição (`scoped`); cliente do SDK reutilizado (`singleton`), respeitando as garantias de concorrência da versão escolhida. Os serviços não guardarão documentos ou resultados em estado compartilhado. As opções serão validadas na inicialização.

As operações de integração serão assíncronas de ponta a ponta. O cancelamento HTTP será propagado pelo caso de uso até o SDK. Não serão utilizados `.Result`, `.Wait()` ou tarefas em segundo plano para envolver entrada e saída síncrona.

## 5. Fluxo de uma requisição

1. O cliente envia `POST /api/documentos/analisar`, com JSON contendo `titulo` e `conteudo`.
2. O pipeline atribui um identificador de correlação e estabelece o tratamento centralizado de exceções antes da execução do endpoint.
3. O Controller, com comportamento de API do ASP.NET Core, valida o formato, os tipos e os campos obrigatórios. Ausência, nulo, vazio e somente espaços são rejeitados. Entrada inválida não chega à OpenAI.
4. O Controller converte o contrato HTTP em entrada da Application e chama `IDocumentAnalysisService`, transmitindo o cancelamento da requisição.
5. A Application aplica as pré-condições do caso de uso e as invariantes de entrada do Domain, mantendo a proteção fora de HTTP. Em seguida, chama `IDocumentAnalysisProvider` com o documento e a política interna de análise.
6. A Infrastructure traduz a política recebida em instruções e esquema de saída, com título e conteúdo tratados como dados. Executa a operação assíncrona do SDK dentro do orçamento de tempo configurado.
7. A Infrastructure verifica conclusão, recusa e integridade da resposta antes de desserializar. Converte os dados válidos em um resultado independente do SDK; falhas são traduzidas para categorias conhecidas da Application.
8. A Application submete o resultado às invariantes do Domain e traduz sua rejeição em falha de resultado da integração. Resultado incompatível não é promovido a sucesso.
9. O Controller mapeia o resultado aprovado para o contrato público e retorna HTTP `200`, JSON com `tipoDocumento`, `resumo`, `nivelRisco`, `palavrasChave` e `pontosAtencao`.
10. Falhas percorrem o mecanismo centralizado e são convertidas conforme a seção 8. Os logs registram duração, categoria de falha e correlação, sem o documento ou a resposta integral da IA.

`GET /health` seguirá um caminho independente, utilizando o mecanismo de Health Checks do ASP.NET Core. Retornará HTTP `200`, `application/json` e corpo `{"status":"Healthy"}` quando a aplicação estiver apta a responder. Se a verificação local indicar indisponibilidade e o processo ainda responder, retornará HTTP `503`, `application/json` e corpo `{"status":"Unhealthy"}`. Não invocará o caso de uso nem a OpenAI e não verificará a disponibilidade do provedor. Falha na inicialização ou encerramento do processo não garante resposta HTTP. Não serão criados endpoints adicionais de saúde.

## 6. OpenAI SDK e Structured Outputs

O pacote oficial `OpenAI` para .NET ficará restrito à Infrastructure. A versão será fixada na implementação após verificação de compatibilidade. Como proposta, o adaptador utilizará a Responses API, sem streaming, por meio do SDK; o modelo será configurável e deverá suportar Structured Outputs.

Structured Outputs utilizará JSON Schema em modo estrito, com objeto raiz, os cinco campos obrigatórios, tipos explícitos, enumeração `BAIXO`, `MEDIO`, `ALTO` e propriedades adicionais desabilitadas. Deve-se respeitar o subconjunto de JSON Schema suportado pelo modelo e pela API selecionados. Recusas e respostas incompletas exigem tratamento específico antes da leitura do resultado. Essas características são descritas na [documentação oficial de Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

As regras de negócio continuam sendo verificadas localmente pelo Domain, acionado pela Application: strings não vazias, resumo com até 150 palavras, de 1 a 10 palavras-chave, unicidade sem diferenciar maiúsculas de minúsculas e pontos de atenção obrigatórios para risco `MEDIO` ou `ALTO`. A regra de contagem proposta nas especificações depende de DA-09 e terá uma única implementação no Domain, reutilizada nos testes. A fidelidade semântica será avaliada pelo conjunto de referência; um schema não comprova essa fidelidade.

O template de prompt será versionado na Infrastructure e traduzirá a rubrica pertencente ao Domain, fornecida pela Application, sem manter uma segunda definição independente dessa rubrica. Incluirá a categoria `INDETERMINADO` e a orientação de não inventar fatos. O conteúdo enviado será tratado como material a analisar, inclusive quando contiver comandos. A integração não habilitará ferramentas ou execução de instruções do documento.

Proposta inicial: uma análise por chamada, sem reparação automática do resultado. Saída inválida, recusa ou truncamento produz falha controlada, sem devolver análise parcial. Eventuais tentativas de transporte do SDK deverão ser configuradas explicitamente para evitar duplicação de políticas e custos inesperados.

DA-02 a DA-06 continuam pendentes quanto a modelo, versão, valores e políticas ainda não definidos. O orçamento de tempo será único para toda a operação remota, incluindo tentativas e intervalos de espera que venham a ser aprovados. Não será reiniciado a cada tentativa. Os limites de entrada e saída e o modelo compatível serão documentados antes da implementação afetada; esta revisão não fixa novos valores nem aprova retries.

## 7. Configuração e credenciais

| Variável proposta | Uso | Validação |
| --- | --- | --- |
| `OPENAI_API_KEY` | Credencial para a API da OpenAI. | Obrigatória e não vazia; ausência impede a inicialização com mensagem que identifica somente a variável. |
| `OpenAI__Model` | Identificador do modelo aprovado. | Obrigatório e não vazio; compatibilidade com Structured Outputs verificada na homologação. |
| `OpenAI__TimeoutSeconds` | Orçamento total da operação de integração. | Obrigatório, finito e positivo. Valor depende de aprovação. |

A Infrastructure receberá opções tipadas pelo sistema de configuração do host. O adaptador não lerá variáveis de ambiente a cada requisição. Configurações não sigilosas poderão ter valores documentados em arquivo, mas credenciais serão fornecidas exclusivamente pelo ambiente.

Em desenvolvimento, a chave será configurada no ambiente do processo, fora de arquivos versionados, inclusive fora de `launchSettings.json`. No Azure App Service, será fornecida pelas configurações da aplicação, expostas ao processo como variáveis de ambiente. Não será incluída no artefato de publicação, logs, mensagens de erro ou documentação.

A validação de inicialização confirma presença e formato básico da configuração, sem chamar a OpenAI. A validade real da chave, as permissões e a disponibilidade do modelo serão verificadas na homologação. Uma alteração de credencial exigirá atualização do ambiente e reinicialização do processo na proposta inicial.

Publicação no Azure App Service é uma decisão de hospedagem e não implica utilizar Azure OpenAI. O provedor desta proposta é a API da OpenAI; eventual troca exigirá revisão da configuração e do adaptador.

## 8. Tratamento centralizado de erros

A API utilizará o mecanismo de tratamento de exceções do ASP.NET Core, com `IExceptionHandler` e respostas Problem Details. Erros de validação e de binding, que podem ocorrer sem exceção, também deverão ser normalizados. O corpo terá status, título seguro e identificador de correlação; validação incluirá os nomes dos campos inválidos, sem repetir seu conteúdo.

| Condição | Resposta esperada | Origem da tradução |
| --- | --- | --- |
| JSON malformado, campo inválido ou pré-condição de entrada violada | HTTP `400`. | Pipeline de validação ou falha conhecida da Application. |
| Tipo de conteúdo não suportado | HTTP `415`. | Pipeline HTTP. |
| Falha de conexão, erro de autenticação do provedor, limite do provedor ou outra falha OpenAI | HTTP `502`. | Infrastructure traduz a causa; API define o status. |
| Saída inválida, recusa ou resposta incompleta da IA | HTTP `502`. | Falha de integração ou validação de resultado. |
| Esgotamento do orçamento de tempo da integração | HTTP `504`. | Timeout identificado pela Infrastructure. |
| Erro interno inesperado | HTTP `500`. | Tratamento central da API. |
| Cancelamento por desconexão do cliente | Interromper o trabalho e encerrar o fluxo; não garantir corpo HTTP para conexão encerrada. | Propagação do cancelamento em todas as camadas. |
| Configuração obrigatória ausente | Falha de inicialização; serviço não fica disponível. | Validação de opções no host. |

O timeout será distinguido do cancelamento originado pelo cliente. As classificações `502` e `504` preservam RNF-05, inclusive para respostas de limite de uso do provedor. Não haverá exposição direta do status ou da mensagem bruta da OpenAI.

Os logs terão metadados controlados: correlação, duração, categoria, modelo e, quando disponível e seguro, identificador de requisição do provedor. Diagnósticos internos também devem remover segredos; título, conteúdo, prompts e saída integral não serão registrados por padrão.

## 9. Estratégia de testes

Todos os testes ficarão em `DocumentAI.Tests`, organizados por camada e categoria. xUnit será o framework comum; os testes de HTTP utilizarão `WebApplicationFactory` e host de teste do ASP.NET Core. A suíte rotineira executará por `dotnet test`, sem rede externa e sem chave real.

| Grupo | Estratégia | Cobertura principal |
| --- | --- | --- |
| Domain | Testes unitários das regras centralizadas. | Riscos permitidos, resumo de 150/151 palavras, quantidade e unicidade das palavras-chave, validade textual e pontos de atenção; política consistente com a rubrica aprovada. |
| Application | Substituir `IDocumentAnalysisProvider` por fake controlado. | Entrada inválida sem chamada ao provedor, política encaminhada sem alterações, uso das invariantes do Domain, tradução de entrada inválida para `400` e de resultado inválido para `502` pela API, propagação de falhas/cancelamento. |
| Infrastructure | Exercitar o adaptador com transporte HTTP controlado do SDK, sem rede. | Envio de título/conteúdo e esquema estrito; desserialização; recusa; truncamento; JSON incompatível; falhas de transporte; timeout e cancelamento. Substituir somente a porta da Application não comprova o funcionamento deste adaptador. |
| API | Host de teste com provedor substituído via DI. | `200` e contrato JSON em português; `400` para todas as variações de entrada; `415`; `500`, `502`, `504`; Problem Details e correlação; `/health` com estados JSON `200 Healthy` e `503 Unhealthy`, sem chamada à OpenAI. |
| Configuração e dependências | Host com configurações controladas, testes automatizados de arquitetura e revisão de responsabilidades. | Falha na ausência de credencial; timeout positivo e único; substituição por DI; referências de projetos permitidas; ausência de ciclos e tipos SDK nas camadas internas; isolamento de Controllers e uso da Infrastructure somente na composição da API. |
| Homologação real | Execução separada, explicitamente habilitada, com segredo do ambiente. | Compatibilidade modelo/SDK/schema, qualidade semântica e chamada real no Azure App Service. |

O host de testes fornecerá configuração fictícia válida para passar pela validação de inicialização, mantendo o transporte externo desabilitado. Testes de cancelamento utilizarão sinais controlados e não dependerão de esperas longas ou chamadas reais.

O conjunto de referência seguirá a seção 6 dos requisitos: três níveis de risco, múltiplos tipos, `INDETERMINADO`, ausência de pontos de atenção e tentativa de alteração de instruções dentro do documento. A avaliação semântica verificará fatos e classificações esperadas, sem igualdade literal da redação. Testes com fakes comprovam contrato e fluxo; não comprovam qualidade da IA real.

Antes do aceite, o ambiente Azure deverá demonstrar por HTTPS: Health Check saudável, rejeição de entrada inválida e análise real conforme o contrato. A suíte isolada não dependerá desse ambiente.

## 10. Operação e rastreabilidade

A API será publicada como um serviço sem estado no Azure App Service. Somente o host API e suas dependências de produção comporão o artefato. O runtime ou pacote de publicação deverá suportar .NET 10. Não haverá armazenamento de documentos pela aplicação nesta etapa.

| Requisitos | Elementos que os atendem |
| --- | --- |
| RF-01, RF-02, RF-08 | Controller, contratos HTTP, validação, mapeamento de saída e testes de API. |
| RF-03 a RF-07 | Caso de uso, adaptador OpenAI, prompt, Structured Outputs, invariantes e conjunto de referência. |
| RF-09 | Health Check independente do provedor. |
| RNF-01 a RNF-03 | Projetos .NET 10, portas por interfaces, DI e propagação assíncrona de cancelamento. |
| RNF-04, RNF-05 | Configuração por ambiente, validação na inicialização, erros centralizados e logs controlados. |
| RNF-06, RNF-07 | xUnit, testes em host, homologação real e publicação no App Service. |

## 11. Decisões arquiteturais pendentes de aprovação

Os itens abaixo não são aprovações concedidas. São propostas e definições necessárias para orientar a implementação ou a publicação. Sua pendência não impede a revisão deste documento.

| ID | Decisão | Proposta ou definição necessária | Impacto e momento de aprovação |
| --- | --- | --- | --- |
| DA-01 | Organização e fronteiras internas | Aprovar `src/` e `tests/`, contratos da Application separados dos DTOs HTTP e referência API → Infrastructure limitada à composição. | Define a estrutura; aprovar antes de criar os projetos. |
| DA-02 | Superfície da integração OpenAI | Aprovar Responses API sem streaming, utilizando o SDK oficial e schema estrito; fixar versão do pacote após verificar suporte. | Define o adaptador e testes; aprovar antes de implementar a integração. |
| DA-03 | Modelo e orçamento | Selecionar modelo compatível com Structured Outputs após avaliação do conjunto de referência, custo e latência; não há modelo fixado neste documento. | Define qualidade e custo; aprovar antes de testes reais e homologação. |
| DA-04 | Timeout e novas tentativas | Definir valor do orçamento total único, incluindo tentativas e esperas, sem reinício por tentativa; proposta inicial sem retries automáticos, inclusive no SDK, e sem reparação de saída. | Afeta latência, disponibilidade e cobrança; aprovar antes de implementar resiliência. |
| DA-05 | Contrato de falhas do modelo | Aprovar recusa e resposta incompleta como `502`, com código público seguro e sem conteúdo bruto; manter `504` para timeout. | Detalha casos não individualizados nos requisitos; aprovar antes de fechar o contrato de erros. |
| DA-06 | Limites e capacidade | Definir tamanho máximo de título/conteúdo, orçamento de saída, concorrência e metas de latência; não truncar documentos silenciosamente. | Requisitos deixaram esses valores em aberto. Devem orientar proteção de custo e política para excesso de entrada antes de exposição corporativa. |
| DA-07 | Acesso e tratamento de dados | Definir controle de acesso e autorizar quais classes de documentos podem ser enviadas ao provedor, com política de dados e retenção aplicável. | Autenticação está fora do escopo atual; a publicação corporativa exige decidir o público e as restrições de acesso. Não implica adicionar autenticação nesta etapa. |
| DA-08 | Ambiente Azure e observabilidade | Escolher sistema operacional, modalidade de publicação, plano/região, destino e retenção dos logs; aprovar ausência de conteúdo documental nos logs. | Define operação e custo; aprovar antes de publicar. |
| DA-09 | Critério de homologação semântica | Aprovar documentos, resultados esperados e regra de contagem de palavras antes da avaliação; casos obrigatórios devem passar. | Define evidência de qualidade; aprovar antes do aceite da integração real. |

Os cinco projetos solicitados, Controllers, DI, interfaces, assincronia, OpenAI SDK, Structured Outputs e xUnit já são diretrizes desta arquitetura. Não dependem de nova aprovação para constar no desenho.

## 12. Referências

- [Requisitos do DocumentAI](requirements.md): fonte do escopo e critérios de aceite.
- [SDKs e bibliotecas oficiais da OpenAI](https://developers.openai.com/api/docs/libraries): referência para adoção do SDK .NET.
- [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs): referência para schema estrito e tratamento dos limites de saída estruturada.

Documentação OpenAI consultada em 20/10/2026. Versões de pacote, modelo e detalhes de configuração deverão ser revalidados na implementação.
