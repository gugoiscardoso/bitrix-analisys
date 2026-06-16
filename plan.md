# Plano — Extração de Conversas de Open Lines do Bitrix24 para Excel

## Contexto

O projeto hoje exporta tarefas do grupo 139 (Chamados Ultracar e Portocar) para JSON. Falta uma segunda capability: extrair **todas as conversas de Open Lines** (linhas abertas — WhatsApp, Telegram, livechat) entre atendentes de suporte e clientes finais, a partir da mesma data filtro (`CreatedFrom = 2025-10-01`), e exportar para um **Excel multi-aba relacional** que será analisado depois com Claude.

**Decisões do usuário fixadas:**
1. **Escopo:** todas as sessões de Open Lines no período (não só as vinculadas a tarefas)
2. **Mídia:** só URL e metadata no Excel (sem baixar binários)
3. **Layout:** multi-aba relacional (Conversations, Messages, Customers, Operators, Files, Metadata)

**Achado crítico da pesquisa Bitrix:** `imopenlines.session.list` **não existe**. A enumeração em massa de sessões precisa passar por `crm.activity.list` com filtro `PROVIDER_ID = "IMOPENLINE"` (cada sessão fechada gera uma atividade no timeline CRM, e `ASSOCIATED_ENTITY_ID = SESSION_ID`). O valor exato de `PROVIDER_ID` **não está documentado** — precisa ser validado in vivo antes da implementação. Por isso o plano começa com uma fase de Discovery bloqueante.

---

## Princípios de Design

- **Reuso total** da infraestrutura HTTP existente: [BitrixApiClient.PaginateAsync](Ultracar-Support-Bitrix-Analisys/Services/BitrixApiClient.cs:62), [BitrixBatchService.ExecuteAsync](Ultracar-Support-Bitrix-Analisys/Services/BitrixBatchService.cs:19), [RateLimitedHttpClient](Ultracar-Support-Bitrix-Analisys/Services/RateLimitedHttpClient.cs). Zero duplicação. Espelhar o padrão de `AssembleTaskData` em [TaskCollectorService.cs:109](Ultracar-Support-Bitrix-Analisys/Services/TaskCollectorService.cs:109) para sessões.
- **DTOs schema-flex (`JsonElement`)** para o que vem da API Bitrix; **POCOs tipados** para as linhas do Excel (compile-time safety na hora de mapear coluna).
- **CLI mode** via flag `--mode tasks|conversations|all|discover` em Program.cs; default = `tasks` para manter compatibilidade retroativa total. Switch simples no Program.cs (sem ExecutionModeRouter — mantém Program.cs enxuto, sem overhead).
- **Stack:** apenas `ClosedXML 0.105.0` (Apache 2.0) como nova dependência. Nada de Serilog/Polly (manter consistência com o projeto atual; `Console.WriteLine` com prefixos `[Discovery]`, `[Enumerator]`, `[Collector]`, `[Excel]`).
- **Constraints universais (CLAUDE.md global):** SOLID, sem Service Locator fora do Program.cs, métodos ≤ 30 linhas, arquivos ≤ 200 linhas, `CancellationToken` propagado, nomenclatura em inglês, comentários/logs de usuário em PT-BR.

---

## Arquivos a Criar/Editar

### Editar
- [Ultracar-Support-Bitrix-Analisys.csproj](Ultracar-Support-Bitrix-Analisys/Ultracar-Support-Bitrix-Analisys.csproj) — adicionar `PackageReference Include="ClosedXML" Version="0.105.0"`
- [appsettings.json](Ultracar-Support-Bitrix-Analisys/appsettings.json) — adicionar `OpenLinesCreatedFrom` (opcional, fallback para `CreatedFrom`)
- [Configuration/BitrixSettings.cs](Ultracar-Support-Bitrix-Analisys/Configuration/BitrixSettings.cs) — propriedade `OpenLinesCreatedFrom` + env var `BITRIX_OPENLINES_CREATED_FROM`. **Não exigir em `Validate()`** (cai no `CreatedFrom`)
- [Program.cs](Ultracar-Support-Bitrix-Analisys/Program.cs) — parse de `--mode` (e opcional `--from`); switch que delega para `RunTasksAsync` (comportamento atual extraído) ou `RunConversationsAsync` ou `RunDiscoveryAsync`

### Criar — `Models/OpenLines/`
- `ChannelKind.cs` — enum (`Unknown`, `WhatsApp`, `Telegram`, `LiveChat`, `Facebook`, `Instagram`, `Email`, `Other`)
- `AuthorType.cs` — enum (`Unknown`, `Customer`, `Operator`, `System`, `Bot`)
- `SessionRawData.cs` — DTO schema-flex (espelho de `TaskData`): `SessionId`, `Activity`, `SessionHistory`, `DialogInfo`, `MessagesExtended` (fallback)
- `ConversationRow.cs`, `MessageRow.cs`, `CustomerRow.cs`, `OperatorRow.cs`, `FileRow.cs`, `ConversationMetadata.cs` — POCOs de Excel (shapes detalhados na seção "Shapes das Abas" abaixo)
- `AssembledSession.cs` — record intermediário retornado pelo Assembler (ConversationRow + Messages + Files + Customer + Operator de 1 sessão)
- `ConversationExport.cs` — aggregate raiz com factory `Build(IEnumerable<AssembledSession>, BitrixSettings)` que faz dedup de `Customers` por `CustomerKey` (`"lead:123"` / `"contact:456"` / `"anon:{externalAuthId}"`) e de `Operators` por `UserId`, calcula contadores agregados, monta `Metadata`. Setters `internal` — só `Build` popula.

### Criar — `Services/OpenLines/`
- `OpenLinesDiscoveryService.cs` — modo `--discover`: probe `crm.activity.list` listando providers distintos no período, valida `PROVIDER_ID="IMOPENLINE"`, pega 1 sample SESSION_ID e chama `imopenlines.session.history.get` + `imopenlines.dialog.get`, imprime keys + tamanho + `USER_CODE` + `entity_data_2`. **Sem exportar nada.**
- `OpenLinesSessionEnumerator.cs` — `EnumerateAsync(createdFrom, ct) → IAsyncEnumerable<SessionMeta>`. Usa `BitrixApiClient.PaginateAsync("crm.activity.list", filter={PROVIDER_ID, >=CREATED}, resultProperty: null)`. Extrai `SessionId = ASSOCIATED_ENTITY_ID`.
- `CrmEntityResolver.cs` — `ResolveAsync(IEnumerable<(type, id)>, ct) → IReadOnlyDictionary<string, JsonElement>`. Dedup + batches de até 50 com `crm.lead.get` / `crm.contact.get` / `crm.company.get` / `crm.deal.get`. Chave canônica `"{type}:{id}"`.
- `UserResolver.cs` — `ResolveAsync(IEnumerable<userId>, ct) → IReadOnlyDictionary<string, JsonElement>`. Cache em memória + batches de `user.get`.
- `CollectedSessions.cs` — record que o Collector retorna (sessões brutas + cache CRM + cache Users).
- `OpenLinesConversationCollector.cs` — orquestra: enumera → batch de até 24 sessões × 2 endpoints (history + dialog) = 48 cmds/batch → extrai entity refs + operator ids → resolve via resolvers → devolve `CollectedSessions`.
- `ConversationAssembler.cs` — mapper raw → POCOs. `ParseChannel(USER_CODE)` (prefix split por `|`), `AuthorOf(message)` (heurística `author_id==0` → System, `users[id].connector==true` → Customer, `users[id].bot==true` → Bot, senão Operator), `ResolveCustomer` (prioridade `entity_data_2` CRM → fallback `users[].connector==true` com `externalAuthId`).
- `ConversationExcelExporter.cs` — `ExportAsync(ConversationExport, outputPath, ct)`. Usa `XLWorkbook` + `Worksheet.Cell(1,1).InsertTable(rows, "Name", createTable:true)` (ClosedXML infere colunas via reflection sobre o POCO), `Columns().AdjustToContents()`, `FreezeRows(1)`.

---

## Shapes das Abas do Excel

| Aba | Colunas |
|---|---|
| **Conversations** | SessionId, ChatId, LineId, Channel, ChannelRaw, CustomerKey, CustomerName, CustomerPhone, CustomerEmail, OperatorId, OperatorName, StartedAt, EndedAt, DurationMinutes, TotalMessages, CustomerMessages, OperatorMessages, SystemMessages, LinkedEntitiesCsv (`"deal:123;lead:456;task:789"`), HasFiles, HasVoiceNote |
| **Messages** | MessageId, SessionId, Timestamp, AuthorId, AuthorType, AuthorName, TextContent, MessageType (`text` / `deleted` / `system`), HasFiles, FilesCount |
| **Customers** (dedup) | CustomerKey, Type (`lead`/`contact`/`anonymous`), EntityId, DisplayName, PhonesCsv, EmailsCsv, CompanyName, SourceName, CreatedAt, SessionIdsCsv, TotalSessions |
| **Operators** (dedup) | UserId, FullName, Email, Department, SessionsHandled, MessagesSent |
| **Files** | FileId, MessageId, SessionId, FileName, MimeType, SizeBytes, DownloadUrl, IsVoiceNote |
| **Metadata** | ExportedAt, CreatedFromFilter, TotalConversations, TotalMessages, TotalCustomers, TotalOperators, TotalFiles, ToolVersion, WebhookHost (só host, sem token), Notes |

---

## Fluxo de Execução

1. **Enumerar:** `crm.activity.list` paginado com `filter={PROVIDER_ID:"IMOPENLINE", >=CREATED:<from>}` → coleta `SESSION_ID`s
2. **Coletar bruto:** em chunks de 24 sessões × 2 endpoints = 48 cmds por batch:
   - `imopenlines.session.history.get?SESSION_ID=<id>` (mensagens, users, files, chat)
   - `imopenlines.dialog.get?SESSION_ID=<id>` (entity_data_2 com bindings CRM + USER_CODE com canal)
3. **Resolver CRM:** extrai todos os `(type, id)` distintos de Lead/Contact/Company/Deal → batches de `crm.<entity>.get`
4. **Resolver Users:** extrai todos os user IDs distintos (autores e operadores) → batches de `user.get`
5. **Montar Excel:** `ConversationAssembler` mapeia cada `SessionRawData` para linhas tipadas; `ConversationExport.Build` faz dedup + contagens agregadas; `ConversationExcelExporter` escreve XLSX
6. **Output:** `output/conversations_export_{timestamp}.xlsx`

---

## Fases de Implementação

| # | Fase | Critério de saída |
|---|---|---|
| **0** | **Discovery (BLOQUEANTE)** — `OpenLinesDiscoveryService` + flag `--mode discover` + enums `ChannelKind`/`AuthorType` + roteamento mínimo no Program.cs | Stdout confirma `PROVIDER_ID` exato, retorno de `session.history.get` (keys, tamanho, presença de `message[]`) e formato do `USER_CODE`. **Sem isso, não avançar.** |
| 1 | Models + Configuration (toda a pasta `Models/OpenLines/`, update em `BitrixSettings.cs` + `appsettings.json`) | Projeto compila |
| 2 | `OpenLinesSessionEnumerator` | Conta sessões corretamente em smoke test (período curto) |
| 3 | `CrmEntityResolver`, `UserResolver`, `OpenLinesConversationCollector` | Retorna `CollectedSessions` populado (validável serializando para JSON temporário) |
| 4 | `ConversationAssembler` + `ConversationExcelExporter` + NuGet `ClosedXML` | Gera XLSX válido com mock de 1 sessão hard-coded |
| 5 | Refactor de `Program.cs` com `--mode` switch | `dotnet run` (sem args) mantém comportamento atual; `dotnet run -- --mode conversations` executa pipeline novo end-to-end |
| 6 | Verificação | Smoke + full run; validar contadores cruzados; documentar lessons em `tasks/lessons.md` |

---

## Riscos & Mitigações

| Risco | Mitigação |
|---|---|
| `PROVIDER_ID="IMOPENLINE"` retorna 0 | Discovery printa todos os providers distintos no período; usuário identifica correto (candidatos: `OPENLINE`, `IMOPENLINES`); ajuste é uma constante única no Enumerator |
| `session.history.get` pagina silenciosamente | Discovery mede `messages.Count` + payload size; se truncado, fallback para `im.dialog.messages.get` (cursor `LAST_ID`, LIMIT 50, ordem descendente) implementado no Collector como fase opcional |
| Sessões anônimas (sem binding CRM) | `CustomerKey = "anon:" + externalAuthId`; fallback `"anon:user_" + chatUserId` se ausente; `Type = "anonymous"` |
| URLs de mídia (WhatsApp) expiram | Aviso na aba Metadata: "Download URLs may expire — fetch within 24h". Não baixar binários (decisão do usuário) |
| Volume alto (>50k mensagens) | ClosedXML em memória; se OOM, refator para streaming (`SaveStream`) — **não bloqueante para v1** |
| User inativo retorna vazio | `OperatorName = "(unknown user " + id + ")"`; não bloqueia exportação |

**Open questions resolvidas por default (configuráveis depois):**
- Sessões em aberto (sem `END_TIME`): `EndedAt = null`, `DurationMinutes = null`
- Bindings: incluir todas em `LinkedEntitiesCsv` (`"deal:X;lead:Y;task:Z"`)
- Mensagens deletadas: `MessageType = "deleted"`, texto = estado atual (REST do Bitrix não expõe histórico de edições)

---

## Verificação End-to-End

1. **Fase 0 (smoke obrigatório):**
   ```
   dotnet run -- --mode discover
   ```
   Stdout deve mostrar providers, contagem com `PROVIDER_ID=IMOPENLINE`, keys de `session.history.get` (deve conter `message`, `users`, `files`, `chat`), `USER_CODE` formatado, `entity_data_2` keys.

2. **Smoke pós-implementação** (editar `OpenLinesCreatedFrom` para 2 dias atrás):
   ```
   dotnet run -- --mode conversations
   ```
   Abrir XLSX e validar:
   - Conversations: 1 linha por sessão
   - Messages: ordem cronológica dentro de cada SessionId
   - Customers: sem duplicatas, `SessionIdsCsv` referenciando IDs reais
   - Operators: `MessagesSent` somado bate com `OperatorMessages` somado em Conversations
   - Files: apenas sessões com anexos
   - Metadata: contadores corretos

3. **Compatibilidade retroativa:**
   ```
   dotnet run
   ```
   Sem flag → modo `tasks` → JSON em `output/bitrix_export_*.json` como sempre.

4. **Full run final:**
   ```
   dotnet run -- --mode conversations
   ```
   Com `OpenLinesCreatedFrom=2025-10-01`. Volume estimado: 1000 sessões ≈ ~70 requisições ≈ ~35 s (folgado nos 480s/janela do Bitrix).

---

## Pontos de Reuso (referência precisa)

| Onde | Como reusar |
|---|---|
| [BitrixApiClient.PaginateAsync](Ultracar-Support-Bitrix-Analisys/Services/BitrixApiClient.cs:62) | Enumerator chama em `crm.activity.list`, `resultProperty: null` (array vem em `result`) |
| [BitrixApiClient.PostAsync](Ultracar-Support-Bitrix-Analisys/Services/BitrixApiClient.cs:21) | Discovery faz chamadas one-shot |
| [BitrixBatchService.ExecuteAsync](Ultracar-Support-Bitrix-Analisys/Services/BitrixBatchService.cs:19) | Collector e Resolvers, sem alteração |
| [BitrixBatchService.FetchRemainingPagesAsync](Ultracar-Support-Bitrix-Analisys/Services/BitrixBatchService.cs:53) | Cobertura de sub-comandos com paginação |
| [RateLimitedHttpClient](Ultracar-Support-Bitrix-Analisys/Services/RateLimitedHttpClient.cs) | Transitivo — 500ms + retry exponencial + Retry-After já cobertos |
| Padrão `AssembleTaskData` em [TaskCollectorService.cs:109](Ultracar-Support-Bitrix-Analisys/Services/TaskCollectorService.cs:109) | Espelhar em `Collector.AssembleRaw` |
| Padrão de chunking [TaskCollectorService.cs:50](Ultracar-Support-Bitrix-Analisys/Services/TaskCollectorService.cs:50) | Mesmo loop, `SessionsPerBatch = 24` |
