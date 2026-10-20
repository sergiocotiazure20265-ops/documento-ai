# DocumentAI — Guia da API e testes

## Estado desta versão

Estrutura inicial em .NET 10, com Controllers registrados e documentação OpenAPI/Scalar disponível em Development e Production. Não há endpoints de negócio implementados. Nenhuma chamada à OpenAI é realizada, e a inicialização desta etapa não exige credenciais.

As operações abaixo são **contratos planejados**, não operações disponíveis para execução nesta versão. Por isso, não estão cadastradas em `paths` no documento OpenAPI e ainda não têm botão de execução no Scalar. Requisições a essas rotas atualmente retornam `404`. Os detalhes de `specifications.md` continuam sendo a referência normativa.

## Documentação disponível agora

| Método | Caminho | Resultado |
| --- | --- | --- |
| GET | `/scalar/v1` | Página de referência e cliente interativo Scalar. |
| GET | `/openapi/v1.json` | Documento OpenAPI com este guia e operações efetivamente implementadas. |

Essas são rotas de documentação, sem ampliação dos endpoints de negócio. A interface utiliza o documento da própria instância, sem endereço de produção fixado no código.

## POST /api/documentos/analisar — planejado

Receberá `Content-Type: application/json` e um objeto com dois campos string obrigatórios: `titulo` e `conteudo`. Ausência, nulo, vazio, somente espaços, tabulações ou quebras de linha serão rejeitados. Números, booleanos, arrays e objetos não serão convertidos para strings.

### Exemplo de entrada

```json
{
  "titulo": "Comunicado de manutenção",
  "conteudo": "O portal interno ficará indisponível no sábado, das 8h às 10h, para manutenção programada."
}
```

### Exemplo de sucesso futuro — HTTP 200

```json
{
  "tipoDocumento": "COMUNICADO",
  "resumo": "O portal interno ficará indisponível no sábado, das 8h às 10h, para manutenção programada.",
  "nivelRisco": "BAIXO",
  "palavrasChave": ["portal interno", "manutenção programada"],
  "pontosAtencao": []
}
```

O resultado terá exatamente cinco campos não nulos:

- `tipoDocumento`: string não vazia; `INDETERMINADO` se não houver evidência suficiente.
- `resumo`: string não vazia, fiel ao documento e com até 150 palavras.
- `nivelRisco`: somente `BAIXO`, `MEDIO` ou `ALTO`.
- `palavrasChave`: 1 a 10 strings relevantes, não vazias e únicas sem diferenciar caixa e espaços nas extremidades.
- `pontosAtencao`: array de strings não vazias; pode ser vazio para `BAIXO`. Para `MEDIO` e `ALTO`, ao menos um ponto deverá indicar evidência do risco.

A contagem de palavras proposta separa segmentos por espaços em branco; sua aprovação continua pendente em DA-09. Limites de entrada, modelo e timeout ainda não foram fixados.

### Respostas previstas

| HTTP | Condição futura |
| --- | --- |
| 200 | Análise completa e válida. |
| 400 | Campos, tipos ou corpo JSON inválidos; nenhuma chamada ao provedor. |
| 415 | Tipo de conteúdo não suportado; nenhuma chamada ao provedor. |
| 502 | Falha do provedor ou saída incompatível. Recusa/truncamento dependem de DA-05. |
| 504 | Esgotamento do orçamento total de integração. |
| 500 | Erro interno inesperado. |

### Exemplo de validação futura — HTTP 400

```json
{
  "type": "about:blank",
  "title": "Dados de entrada inválidos.",
  "status": 400,
  "traceId": "exemplo-validacao-001",
  "errors": {
    "titulo": ["O título é obrigatório."]
  }
}
```

Erros usarão `application/problem+json`, com correlação e sem segredos, conteúdo documental ou mensagens brutas do provedor. Para corpo inválido, a chave de `errors` será `body`.

## GET /health — planejado

Sem corpo ou parâmetros. Verificará somente a aplicação local, sem chamar a OpenAI.

Sucesso futuro: HTTP `200`, `application/json`:

```json
{"status":"Healthy"}
```

Indisponibilidade local, se o processo responder: HTTP `503`:

```json
{"status":"Unhealthy"}
```

O Health Check não certificará a disponibilidade do provedor. Nesta versão, `/health` ainda não foi implementado.

## Roteiro de testes para as próximas etapas

Quando os Controllers e serviços forem implementados, as operações serão descobertas automaticamente no OpenAPI e aparecerão no cliente Scalar. Para executá-las, abrir a operação, selecionar o cliente HTTP, preencher o JSON e enviar à própria instância.

| Cenário | Resultado esperado após implementação |
| --- | --- |
| Entrada válida e provedor disponível | 200 com os cinco campos válidos. |
| Campo ausente, nulo, vazio ou somente espaços | 400 identificando o campo, sem chamada à IA. |
| Tipo diferente de string ou JSON malformado | 400, sem chamada à IA. |
| Envio de `text/plain` | 415. |
| Resultado inválido ou falha do provedor | 502, sem análise parcial. |
| Timeout do provedor | 504; cancelamento distinto de desconexão. |
| Documento sem risco relevante | BAIXO; pontos de atenção podem ser vazios. |
| Documento com risco MEDIO/ALTO | Pelo menos um ponto de atenção sustentando o risco. |
| Health Check local saudável | 200, mesmo se o provedor estiver indisponível. |

Usar somente documentos autorizados no ambiente selecionado. Chaves da OpenAI pertencem à configuração do servidor e nunca devem ser inseridas no cliente Scalar. A documentação atual não exige nem configura credenciais.

## Acesso em Development e Production

Em desenvolvimento, executar `dotnet run --project src/DocumentAI.API --launch-profile http` e abrir `http://localhost:5249/scalar/v1`. O perfil HTTPS utiliza `https://localhost:7115/scalar/v1` com certificado local confiável.

Para simular Production localmente, configurar `ASPNETCORE_ENVIRONMENT=Production` e executar com `--no-launch-profile` e a URL desejada. `launchSettings.json` é apenas configuração local e não é utilizado na publicação.

Na instância publicada, abrir `/scalar/v1` e `/openapi/v1.json` no domínio HTTPS real. As duas rotas são habilitadas em ambos os ambientes por decisão explícita do usuário. Não houve publicação ou modificação no Azure nesta etapa.

O documento e este guia são incluídos no pacote da API. A versão adotada do Scalar serve o JavaScript da interface pela própria aplicação. A documentação não depende de OpenAI nem de um servidor proxy para testes.
