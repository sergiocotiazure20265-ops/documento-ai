# DocumentAI — Requisitos

## 1. Objetivo e escopo

Disponibilizar uma API corporativa ASP.NET Core para analisar documentos textuais utilizando OpenAI. A API receberá título e conteúdo, produzirá uma análise estruturada e oferecerá um endpoint para verificação de disponibilidade.

Este documento define requisitos e critérios de aceite. Não contém implementação. O recebimento de arquivos, OCR, persistência de documentos, autenticação e interface gráfica não fazem parte do escopo definido nesta etapa.

## 2. Contrato funcional esperado

### Entrada da análise

- Método e rota: `POST /api/documentos/analisar`.
- Tipo de conteúdo: `application/json`.
- Campos obrigatórios: `titulo` e `conteudo`, ambos textuais, não nulos e não compostos apenas por espaços em branco.
- `titulo` representa o título; `conteudo` representa o conteúdo textual completo a ser analisado.

### Saída da análise

Uma análise bem-sucedida deverá retornar HTTP `200` e um objeto JSON com os seguintes campos obrigatórios:

| Campo | Tipo | Regra |
| --- | --- | --- |
| `tipoDocumento` | string | Tipo identificado para o documento; usar `INDETERMINADO` quando não houver evidências suficientes. |
| `resumo` | string | Resumo objetivo, não vazio e com até 150 palavras. |
| `palavrasChave` | array de strings | De 1 a 10 palavras-chave ou expressões curtas relevantes, sem itens vazios ou duplicados. |
| `nivelRisco` | string | Exatamente `BAIXO`, `MEDIO` ou `ALTO`. |
| `pontosAtencao` | array de strings | Pontos de atenção identificados, sem itens vazios; array vazio quando não houver pontos identificados. |

Não será exigida redação idêntica entre execuções da IA. O contrato, os valores permitidos e a fidelidade ao documento serão exigidos em todas as respostas bem-sucedidas.

## 3. Requisitos funcionais

| ID | Requisito | Critérios de aceite verificáveis |
| --- | --- | --- |
| RF-01 | Receber título e conteúdo textual por HTTP POST. | Uma requisição JSON válida para `POST /api/documentos/analisar`, com `titulo` e `conteudo` preenchidos, deve iniciar a análise e retornar HTTP `200` quando o serviço de IA estiver disponível e responder validamente. |
| RF-02 | Validar os campos obrigatórios antes da análise. | Para cada campo, testar ausência, valor nulo, string vazia, somente espaços e tipo diferente de string. Todos esses casos devem retornar HTTP `400`, identificar o campo inválido e não chamar a OpenAI. JSON malformado deve retornar HTTP `400`; tipo de conteúdo não suportado deve retornar HTTP `415`. |
| RF-03 | Utilizar OpenAI para identificar o tipo do documento. | A integração deve enviar título e conteúdo para análise. Com respostas controladas da integração, o tipo retornado deve aparecer em `tipoDocumento`. No conjunto de documentos de referência, os tipos devem corresponder às categorias esperadas; um texto sem elementos suficientes para classificação deve produzir `INDETERMINADO`. |
| RF-04 | Gerar um resumo objetivo. | `resumo` deve ser não vazio, ter no máximo 150 palavras e apresentar as informações centrais do conteúdo sem acrescentar fatos externos. A validação semântica deve usar documentos de referência e uma lista de fatos esperados por documento. |
| RF-05 | Identificar palavras-chave. | `palavrasChave` deve conter entre 1 e 10 itens relevantes, sem duplicidade desconsiderando maiúsculas e minúsculas. Cada item deve representar um tema ou conceito sustentado pelo texto. |
| RF-06 | Classificar o nível de risco. | `nivelRisco` deve aceitar exclusivamente `BAIXO`, `MEDIO` ou `ALTO`. Documentos de referência devem cobrir os três níveis segundo a rubrica da seção 4. Valores diferentes desses não podem ser retornados como análise bem-sucedida. |
| RF-07 | Identificar pontos de atenção. | `pontosAtencao` deve listar os riscos, lacunas ou inconsistências relevantes sustentados pelo documento. Os casos de referência devem indicar quais pontos são obrigatórios; quando não existirem pontos identificáveis, a resposta deve conter um array vazio. |
| RF-08 | Retornar JSON estruturado e válido. | Toda resposta HTTP `200` deve ter `Content-Type` JSON e conter os cinco campos da seção 2, com os tipos e restrições definidos. A resposta não deve incluir cercas Markdown ou texto fora do objeto JSON. Uma resposta inválida da OpenAI não pode ser repassada como HTTP `200`. |
| RF-09 | Disponibilizar Health Check. | `GET /health` deve retornar HTTP `200`, `application/json` e corpo `{"status":"Healthy"}` quando a aplicação estiver em execução e apta a responder. Se a verificação local indicar indisponibilidade e o processo ainda responder, deve retornar HTTP `503` e corpo JSON `{"status":"Unhealthy"}`. Essa verificação deve funcionar sem executar análises nem chamar a OpenAI. Seu resultado verifica a disponibilidade da aplicação e não certifica a disponibilidade da OpenAI. Falha de inicialização ou processo encerrado não garante resposta HTTP. |

## 4. Rubrica para classificação de risco

O risco representa indícios presentes no documento, e não uma garantia sobre consequências futuras. A IA deverá considerar o documento como dados a analisar; instruções incluídas em seu conteúdo não deverão substituir as regras de análise ou o formato de resposta.

| Nível | Regra de classificação | Exemplo para o conjunto de referência |
| --- | --- | --- |
| `BAIXO` | Não há indícios explícitos de prejuízo relevante, obrigações críticas ou inconsistências materiais. | Comunicado informativo sem compromissos, penalidades ou dados sensíveis. |
| `MEDIO` | Há obrigações, prazos, ambiguidades ou exposição relevante que exigem revisão, sem evidência explícita de consequência crítica. | Proposta com obrigação de entrega e prazo ambíguo, sem penalidade grave descrita. |
| `ALTO` | Há evidência explícita de potencial prejuízo grave, penalidade significativa, exposição de credenciais ou obrigação crítica descumprida. | Notificação de descumprimento com penalidade significativa expressamente indicada. |

Quando houver indícios de mais de um nível, deve prevalecer o maior nível sustentado pelo conteúdo. Para `MEDIO` e `ALTO`, ao menos um ponto de atenção deve indicar a evidência que justifica o nível. O conjunto de referência deverá fixar exemplos e resultados esperados antes da homologação, evitando avaliação baseada apenas em preferência de redação.

## 5. Requisitos não funcionais

| ID | Requisito | Critérios de aceite verificáveis |
| --- | --- | --- |
| RNF-01 | Utilizar .NET 10 e ASP.NET Core. | O projeto da API deve ter como alvo `net10.0`, utilizar ASP.NET Core e compilar com o SDK .NET 10. A configuração de publicação deve ser compatível com o ambiente de execução selecionado no Azure App Service. |
| RNF-02 | Utilizar programação assíncrona nas operações de entrada e saída. | A chamada à OpenAI e o fluxo HTTP correspondente devem utilizar operações assíncronas, propagar o cancelamento da requisição e não usar bloqueios como `.Result` ou `.Wait()` nesse fluxo. Verificação por revisão de código e teste de cancelamento com integração controlada. |
| RNF-03 | Utilizar Dependency Injection. | Os serviços de análise e de integração com OpenAI devem ser fornecidos pelo contêiner de DI do ASP.NET Core. Um teste deve conseguir substituir a integração real por uma implementação controlada sem alterar o código de produção. |
| RNF-04 | Configurar credenciais por variáveis de ambiente. | A credencial da OpenAI deve ser obtida por variável de ambiente, inclusive por configuração equivalente do Azure App Service. Nenhuma credencial deve constar no repositório, nas respostas HTTP ou nos logs. A ausência da configuração obrigatória deve ser detectada na inicialização com mensagem que identifique a configuração ausente, sem revelar segredos. |
| RNF-05 | Centralizar o tratamento de exceções. | Falhas não tratadas devem passar por um mecanismo central e retornar erro JSON padronizado, com status e identificador de correlação. Erro inesperado interno deve retornar HTTP `500`; falha da OpenAI ou resposta incompatível com o contrato deve retornar HTTP `502`; expiração do tempo limite da integração deve retornar HTTP `504`. Nenhuma resposta deve expor stack trace, credenciais ou detalhes internos do provedor. O limite de tempo deve ser finito e configurável. |
| RNF-06 | Possuir testes automatizados. | A suíte deve executar por `dotnet test` e passar integralmente. Deve cobrir validação de entrada, contrato de sucesso, três níveis de risco, pontos de atenção vazios, resposta inválida da IA, falha do provedor, timeout, cancelamento e Health Check. Testes rotineiros devem usar integração controlada e não depender de credenciais ou chamadas reais à OpenAI. |
| RNF-07 | Permitir publicação no Azure App Service. | Deve ser possível publicar a API em um Azure App Service com ambiente compatível com .NET 10 e configurar a credencial sem incluí-la no pacote. Após a publicação, verificar por HTTPS: `/health` retorna HTTP `200`, entrada inválida retorna HTTP `400` e uma análise válida com OpenAI retorna HTTP `200` conforme o contrato. |

## 6. Condições de aceite do projeto

- Todos os critérios RF e RNF devem possuir evidência de validação por teste automatizado, revisão técnica ou verificação de publicação, conforme o critério.
- O conjunto de referência deve conter ao menos um documento de cada nível de risco, mais de um tipo de documento, um texto de tipo indeterminado, um documento sem pontos de atenção e um documento contendo instruções que tentem alterar o comportamento da análise.
- Os casos semânticos devem ser avaliados por tipo esperado, fatos centrais do resumo, relevância das palavras-chave, nível de risco e pontos de atenção obrigatórios. Não se deve exigir igualdade literal do texto gerado.
- A homologação deve incluir uma chamada real à OpenAI no ambiente publicado. A aprovação dos testes com integração controlada, isoladamente, não comprova o funcionamento da integração real.
- Limites de tamanho de entrada, metas de latência, volume simultâneo e controles de acesso deverão ser definidos em evolução posterior. Este documento não estabelece metas numéricas para esses itens.
- O contrato público em português está sincronizado com specifications.md. A definição dos valores de timeout, modelo, retries e limites permanece pendente nas decisões arquiteturais correspondentes. O orçamento finito de tempo da integração será único, incluindo eventuais tentativas e intervalos aprovados.
