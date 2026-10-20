# DocumentAI — Especificações da API

## 1. Escopo e precedência do contrato

Esta especificação detalha [requirements.md](requirements.md) e [architecture.md](architecture.md), sem implementação. O contrato público utiliza os nomes em português definidos nesta etapa:

| Método | Rota | Finalidade |
| --- | --- | --- |
| `POST` | `/api/documentos/analisar` | Analisar título e conteúdo textual de um documento. |
| `GET` | `/health` | Verificar a disponibilidade da aplicação. |

A rota `/api/documentos/analisar` e os campos em português substituíram o contrato inicial em inglês. Os requisitos e a arquitetura estão sincronizados com esse contrato vigente. Não será criado alias para a rota anterior. A sincronização documental não aprova as demais decisões pendentes da arquitetura.

| Nome anterior | Nome público vigente |
| --- | --- |
| `title` | `titulo` |
| `content` | `conteudo` |
| `documentType` | `tipoDocumento` |
| `summary` | `resumo` |
| `riskLevel` | `nivelRisco` |
| `keywords` | `palavrasChave` |
| `attentionPoints` | `pontosAtencao` |

Não estão previstos endpoints adicionais, upload de arquivos, OCR, armazenamento, consulta de histórico ou processamento em segundo plano.

## 2. POST /api/documentos/analisar

### 2.1. Comportamento

O endpoint recebe um único documento textual, valida a entrada e executa o caso de uso de análise de forma assíncrona. Retorna a análise completa na mesma requisição. Não cria um recurso persistido e não retorna análise parcial.

O Controller utiliza o serviço da Application por DI; a chamada à OpenAI fica na Infrastructure, conforme a arquitetura. O cancelamento HTTP é propagado até a integração.

### 2.2. Request

- Cabeçalho obrigatório: `Content-Type: application/json`.
- Corpo obrigatório: objeto JSON contendo os campos abaixo.
- Nomes canônicos dos campos: exatamente os apresentados nesta especificação, sem acentos.

| Campo | Tipo JSON | Obrigatório | Validação |
| --- | --- | --- | --- |
| `titulo` | string | Sim | Não pode estar ausente, ser nulo, vazio ou conter somente espaços em branco. |
| `conteudo` | string | Sim | Não pode estar ausente, ser nulo, vazio ou conter somente espaços em branco. Deve conter o texto a analisar. |

Não haverá conversão de números, booleanos, arrays ou objetos para strings. Corpo vazio, `null`, array ou outro valor que não seja um objeto válido para o contrato resultará em HTTP `400`.

A verificação de vazio considera espaços, tabulações e quebras de linha. Espaços no início ou no fim de uma string com texto não tornam o campo inválido. A validação não deve modificar o conteúdo documental de forma que altere seu significado.

Limites máximos de título, conteúdo e corpo HTTP continuam pendentes em DA-06. Esta especificação não define aceitação ilimitada: os limites e o comportamento de excesso deverão ser documentados antes da implementação desses controles. Não se deve truncar o documento silenciosamente.

Exemplo de request válido:

```json
{
  "titulo": "Comunicado de manutenção",
  "conteudo": "O portal interno ficará indisponível no sábado, das 8h às 10h, para manutenção programada. O acesso será restabelecido após a conclusão do serviço."
}
```

Exemplo de request inválido:

```json
{
  "titulo": "   ",
  "conteudo": null
}
```

### 2.3. Response de sucesso

- Status: HTTP `200 OK`.
- Tipo de conteúdo: `application/json`.
- Corpo: um objeto contendo exatamente os cinco campos abaixo, todos obrigatórios e não nulos. A ordem das propriedades não tem significado contratual.

| Campo | Tipo JSON | Restrições |
| --- | --- | --- |
| `tipoDocumento` | string | Não vazio nem composto apenas por espaços. Usar `INDETERMINADO` se não houver evidência suficiente para identificar o tipo. Os demais tipos não formam uma enumeração fechada nesta etapa. |
| `resumo` | string | Não vazio; no máximo 150 palavras; objetivo e fiel aos fatos centrais do documento. |
| `nivelRisco` | string | Exclusivamente `BAIXO`, `MEDIO` ou `ALTO`, com essa grafia e caixa. |
| `palavrasChave` | array de strings | De 1 a 10 palavras ou expressões relevantes; sem nulos, itens vazios ou duplicados. |
| `pontosAtencao` | array de strings | Sem nulos ou itens vazios. Array vazio quando não houver pontos identificados. Para `MEDIO` e `ALTO`, ao menos um item deve indicar evidência que justifique o risco. |

Regra proposta de contagem do resumo: após remover espaços nas extremidades, cada sequência não vazia separada por um ou mais caracteres de espaço em branco conta como uma palavra. Pontuação anexada e termos com hífen sem espaços permanecem no mesmo segmento. Assim, `análise de risco` contém três palavras e `contrato-padrão` contém uma. Essa regra detalha DA-09 e permanece sujeita à aprovação prevista na arquitetura.

Para unicidade de palavras-chave, a comparação desconsidera espaços nas extremidades e diferenças entre maiúsculas e minúsculas, com comparação ordinal independente de cultura. Não remove acentos nem equipara sinônimos. Por exemplo, `Contrato` e ` contrato ` são duplicados. Um resultado inválido não será corrigido silenciosamente para ser aceito como sucesso.

Exemplo de resposta para o comunicado:

```json
{
  "tipoDocumento": "COMUNICADO",
  "resumo": "O portal interno passará por manutenção programada no sábado, das 8h às 10h, com restabelecimento do acesso após a conclusão do serviço.",
  "nivelRisco": "BAIXO",
  "palavrasChave": ["portal interno", "manutenção programada", "indisponibilidade"],
  "pontosAtencao": []
}
```

Exemplo de documento com risco alto:

```json
{
  "titulo": "Notificação de descumprimento contratual",
  "conteudo": "A entrega prevista para 10 de outubro de 2026 não ocorreu. O contrato prevê multa de R$ 500.000,00 pelo descumprimento desse prazo. Solicitamos manifestação do fornecedor."
}
```

Exemplo de resposta correspondente:

```json
{
  "tipoDocumento": "NOTIFICACAO",
  "resumo": "A notificação informa o descumprimento do prazo de entrega de 10 de outubro de 2026, prevê multa de R$ 500.000,00 e solicita manifestação do fornecedor.",
  "nivelRisco": "ALTO",
  "palavrasChave": ["descumprimento contratual", "prazo de entrega", "multa", "fornecedor"],
  "pontosAtencao": [
    "O prazo de entrega indicado foi descumprido.",
    "O documento prevê multa de R$ 500.000,00 pelo descumprimento do prazo."
  ]
}
```

Os exemplos ilustram o contrato e não fixam uma redação literal para a IA. A classificação segue a rubrica dos requisitos: `BAIXO` sem indícios relevantes; `MEDIO` com obrigações, ambiguidades ou exposição que exijam revisão; `ALTO` com evidências explícitas de consequência grave. Havendo múltiplos níveis, prevalece o maior sustentado pelo texto.

### 2.4. Validação do resultado da integração

A saída estruturada deverá respeitar o contrato e as verificações locais descritas na arquitetura. Não serão retornados cercas Markdown, texto fora do JSON, valores de risco inventados ou objetos incompletos.

A Infrastructure verifica protocolo, conclusão e estrutura; a Application submete os dados às invariantes centralizadas no Domain. Regras de resumo, unicidade, risco e pontos de atenção não serão reimplementadas em Controllers ou no adaptador. Violações da entrada são traduzidas para `400`; violações do resultado externo, para `502`. A rubrica pertence ao Domain e é fornecida pela Application ao adaptador, que a traduz para o prompt sem definir uma política própria.

Saída com campo obrigatório ausente, tipo incorreto, texto vazio, mais de 150 palavras no resumo, quantidade inválida de palavras-chave, duplicidade ou ausência de justificativa para risco `MEDIO`/`ALTO` será tratada como falha de integração. Recusa do modelo e resposta truncada seguem a proposta de erro da arquitetura, ainda sujeita à DA-05.

Instruções contidas no documento são dados a analisar e não podem alterar o contrato. Fidelidade factual, relevância e justificativa semântica serão verificadas no conjunto de referência; validações estruturais, isoladamente, não comprovam esses aspectos.

## 3. Códigos HTTP e contrato de erro do POST

| Código | Situação | Chamada à OpenAI |
| --- | --- | --- |
| `200` | Entrada válida e análise completa aceita pelo contrato. | Executada com sucesso. |
| `400` | Corpo ausente ou inválido, JSON malformado, campo obrigatório ausente/nulo/em branco ou com tipo incorreto. | Não deve ocorrer. |
| `415` | Conteúdo enviado com tipo não suportado, como `text/plain`. | Não deve ocorrer. |
| `502` | Falha de comunicação ou erro do provedor, inclusive autenticação ou limite do provedor; saída incompatível; conforme proposta DA-05, também recusa e resposta incompleta. | Tentada ou executada sem resultado utilizável. |
| `504` | Orçamento de tempo configurado para a integração esgotado. | Iniciada e cancelada ao esgotar o orçamento. |
| `500` | Falha interna inesperada da aplicação. | Pode ter ocorrido; depende do ponto de falha. |

Falha de autenticação ou limite de uso da OpenAI não será exposta como `401` ou `429` ao consumidor; o contrato atual mapeia falhas do provedor para `502`. O timeout de integração deve ser distinguido de desconexão do cliente. Nesta última, o trabalho será cancelado sem garantia de resposta em uma conexão encerrada.

O timeout corresponde a um único orçamento total da operação remota, incluindo todas as tentativas e intervalos de espera eventualmente aprovados. Não se reinicia por tentativa. O valor, o modelo e a política de retries continuam pendentes; não se presume aprovação da proposta inicial por esta revisão.

### 3.1. Formato padronizado

Erros produzidos pelo pipeline da aplicação utilizarão `application/problem+json`, incluindo falhas de validação e tipo de conteúdo. O tratamento será centralizado conforme a arquitetura.

| Campo | Tipo | Regra |
| --- | --- | --- |
| `type` | string | Identificador do tipo de problema; nesta especificação, `about:blank`. |
| `title` | string | Descrição curta e segura em português. |
| `status` | integer | Mesmo código do status HTTP. |
| `traceId` | string | Identificador não vazio, associado aos logs da requisição. |
| `errors` | objeto de arrays de strings | Presente em `400`; associa campo ou corpo inválido a mensagens seguras. |

Para campo inválido, as chaves de `errors` serão `titulo` e/ou `conteudo`. Para JSON malformado ou corpo incompatível, a chave será `body`. Mensagens não repetirão os valores recebidos. A redação das mensagens pode variar; status, estrutura e chaves são verificáveis.

Não serão expostos stack trace, credenciais, prompts, documento, resposta bruta ou mensagens internas do provedor. Erros emitidos por serviços de hospedagem antes de alcançar a aplicação estão fora da garantia deste formato.

Exemplo de HTTP `400` para o request inválido da seção 2.2:

```json
{
  "type": "about:blank",
  "title": "Dados de entrada inválidos.",
  "status": 400,
  "traceId": "exemplo-validacao-001",
  "errors": {
    "titulo": ["O título é obrigatório e não pode conter somente espaços."],
    "conteudo": ["O conteúdo é obrigatório."]
  }
}
```

Exemplo de HTTP `502`:

```json
{
  "type": "about:blank",
  "title": "Não foi possível obter uma análise válida do serviço de IA.",
  "status": 502,
  "traceId": "exemplo-integracao-002"
}
```

Exemplo de HTTP `504`:

```json
{
  "type": "about:blank",
  "title": "O tempo limite do serviço de IA foi excedido.",
  "status": 504,
  "traceId": "exemplo-timeout-003"
}
```

Os identificadores acima são ilustrativos; cada requisição terá seu identificador real.

## 4. GET /health

### 4.1. Request e response

Não recebe corpo nem exige parâmetros. Retorna HTTP `200 OK`, `Content-Type: application/json`, com o seguinte corpo quando a aplicação estiver apta a responder:

```json
{
  "status": "Healthy"
}
```

A representação JSON fixa como será exposto o estado já exigido nos requisitos. O endpoint não chama a OpenAI, não executa análise, não retorna configurações ou segredos e não atesta disponibilidade do provedor.

Se o mecanismo local de Health Check reportar indisponibilidade enquanto o processo ainda puder responder, retornará HTTP `503 Service Unavailable`, JSON com `status` igual a `Unhealthy`. Uma aplicação que não iniciou ou um processo encerrado não pode garantir resposta HTTP. Ausência da credencial obrigatória continua sendo falha de inicialização, sem simular um endpoint saudável.

## 5. Critérios de aceite

| ID | Critério verificável |
| --- | --- |
| CA-01 | O contrato de análise utiliza somente a rota pública `/api/documentos/analisar` e os nomes em português; não exige campos em inglês. |
| CA-02 | Entrada válida com provedor controlado produz `200`, JSON e exatamente os cinco campos de saída, com tipos e restrições definidos. |
| CA-03 | Cada variação inválida de `titulo` e `conteudo` produz `400`, identifica o campo e registra zero chamadas ao provedor. Corpo inválido identifica `body`. |
| CA-04 | Tipo de conteúdo não suportado produz `415` sem chamar o provedor. |
| CA-05 | Saída inválida do provedor nunca resulta em `200`. Erros de integração retornam `502`, timeout retorna `504` e erro interno inesperado retorna `500`. Recusa e truncamento seguem DA-05 quando aprovada. |
| CA-06 | Erros da aplicação seguem Problem Details, com status coerente e `traceId` não vazio, sem dados internos ou conteúdo documental. |
| CA-07 | `GET /health` retorna `200` e o JSON de estado saudável sem executar qualquer chamada ao provedor; uma falha da OpenAI não torna esse check local indisponível. |
| CA-08 | A análise preserva a rubrica de risco; os casos de referência cobrem `BAIXO`, `MEDIO`, `ALTO`, `INDETERMINADO`, ausência de pontos de atenção e documento com instruções adversárias. |
| CA-09 | A suíte xUnit executa por `dotnet test`, com fakes/transporte controlado, sem chave real nem rede externa. A homologação separada comprova análise real via HTTPS no Azure. |
| CA-10 | Cancelamento do cliente interrompe a integração e não é confundido com timeout; não se exige resposta após o encerramento da conexão. |
| CA-11 | Testes automatizados de arquitetura verificam referências permitidas, ausência de ciclos, SDK restrito à Infrastructure e isolamento dos Controllers. Revisão confirma invariantes únicas no Domain e rubrica traduzida pelo adaptador sem redefinição. |

## 6. Cenários de testes

Os cenários são especificações de testes futuros, sem implementação nesta etapa. As verificações determinísticas serão automatizadas com xUnit. Os testes HTTP usarão host de teste e substituição por DI; os testes do adaptador usarão transporte controlado para exercitar a integração sem rede.

| ID | Dado / ação | Resultado esperado |
| --- | --- | --- |
| CT-01 | Enviar o comunicado válido com provedor controlado retornando a análise da seção 2.3. | `200`, `application/json`, nomes em português, cinco campos e valores correspondentes. |
| CT-02 | Omitir cada campo, enviar nulo, string vazia e somente espaços, tabulações ou quebras de linha, em casos separados. | `400`, chave do campo em `errors`, nenhuma chamada à IA. |
| CT-03 | Enviar número, booleano, array ou objeto em cada campo, separadamente. | `400`, sem coerção para string e sem chamada à IA. |
| CT-04 | Enviar corpo vazio, JSON malformado, `null`, array ou string na raiz. | `400`, `errors.body`, sem chamada à IA. |
| CT-05 | Enviar conteúdo com `Content-Type: text/plain`. | `415`, Problem Details e zero chamadas à IA. |
| CT-06 | Enviar título/conteúdo com texto e espaços nas extremidades. | Entrada aceita e encaminhada sem alteração de significado. |
| CT-07 | Simular resultados válidos para cada um dos três níveis. | `200`; `nivelRisco` mantém exatamente `BAIXO`, `MEDIO` ou `ALTO`. Para os dois últimos, há evidência em `pontosAtencao`. |
| CT-08 | Simular tipo `INDETERMINADO` com os demais campos válidos. | `200`; não é inventada classificação mais específica. |
| CT-09 | Simular `BAIXO` sem pontos de atenção. | `200` e `pontosAtencao` igual a `[]`, nunca nulo. |
| CT-10 | Simular campo de saída ausente/nulo, tipo incorreto, propriedade extra ou nível `CRITICO`. | `502`, nenhuma análise parcial. |
| CT-11 | Simular resumos de 150 e 151 palavras, e outro com espaços repetidos, quebras de linha e termos com hífen. | 150 palavras aceitas e 151 rejeitadas; contagem conforme regra da seção 2.3, após aprovação em DA-09. |
| CT-12 | Simular 0, 1, 10 e 11 palavras-chave, item vazio/nulo e duplicidade `Contrato`/` contrato `. | Aceitar somente 1 a 10 itens válidos e únicos; demais casos retornam `502`. |
| CT-13 | Simular pontos vazios/nulos ou risco `MEDIO`/`ALTO` com array vazio. | `502`. |
| CT-14 | Simular erro de conexão e respostas de erro do provedor, incluindo autenticação e limite de uso. | `502`, mensagem segura, sem repassar detalhes externos. |
| CT-15 | Simular recusa e resposta incompleta/truncada. | `502` conforme a proposta DA-05; sem desserializar como análise bem-sucedida. |
| CT-16 | Fazer a integração controlada exceder o timeout configurado. | `504`, cancelamento da operação e `traceId` presente. |
| CT-17 | Cancelar a requisição enquanto o provedor aguarda. | Token propagado, operação interrompida; sem classificá-la como timeout. |
| CT-18 | Simular exceção interna inesperada. | `500`, Problem Details; sem stack trace ou segredos no corpo. |
| CT-19 | Consultar `/health` em host apto a responder, inclusive com provedor simulado indisponível. | `200`, `{"status":"Healthy"}` e zero chamadas ao provedor. |
| CT-20 | Simular resultado local não saudável no mecanismo de Health Check. | `503`, JSON com `status` igual a `Unhealthy`. |
| CT-21 | Iniciar o host sem `OPENAI_API_KEY`. | Falha de inicialização com nome da configuração ausente, sem revelar valores de segredo. |
| CT-22 | Avaliar documento que contém comandos para ignorar regras ou modificar o formato. | Contrato preservado; instruções tratadas como dados. Evidência obtida também na avaliação semântica real. |
| CT-23 | Executar conjunto aprovado de documentos reais de referência. | Tipos, fatos centrais, palavras-chave, riscos e pontos obrigatórios correspondem aos resultados esperados, sem exigir redação idêntica. |
| CT-24 | Publicar e testar via HTTPS no Azure App Service. | `/health` retorna `200`; entrada inválida retorna `400`; análise real retorna `200` com o contrato vigente em português. |
| CT-25 | Verificar automaticamente referências de projeto e dependências de tipos dos Controllers e camadas internas. | Nenhum ciclo ou referência proibida; SDK limitado à Infrastructure; Controllers dependem dos contratos da Application e a API usa Infrastructure somente na composição. |
| CT-26 | Simular violação de invariantes em entrada e em resultado externo. | A mesma regra de domínio é reutilizada; entrada gera `400` sem chamar o provedor, resultado externo gera `502`. |
| CT-27 | Capturar a política enviada ao provedor e sua tradução em prompt/schema por transporte controlado. | Rubrica e restrições correspondem à política interna aprovada, sem critérios independentes adicionados pelo adaptador. |
| CT-28 | Controlar o tempo da integração e, se aprovadas, tentativas com intervalos de espera. | Operação respeita o único orçamento total, sem reiniciar a contagem por tentativa; ao esgotá-lo, cancela e retorna `504`. |

## 7. Pendências preservadas

Esta especificação não escolhe modelo, versão do SDK, valor do timeout, política de retries ou limites de entrada. Permanecem as decisões DA-01 a DA-09 da arquitetura. Em particular, recusa/truncamento como `502` detalham a proposta DA-05; a contagem de palavras e os documentos de referência detalham DA-09. Nenhuma dessas decisões é considerada aprovada apenas pela criação deste documento.

Os requisitos, a arquitetura e as tarefas devem permanecer alinhados a esta especificação. O mapeamento da seção 1 registra somente a migração histórica dos nomes, sem oferecer suporte ao contrato anterior.
