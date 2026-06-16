using System.Text.Json;
using Ultracar_Support_Bitrix_Analisys.Models.OpenLines;

namespace Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

public class OpenLinesConversationCollector
{
    private readonly BitrixBatchService _batchService;
    private readonly OpenLinesSessionEnumerator _enumerator;
    private readonly CrmEntityResolver _crmResolver;
    private readonly UserResolver _userResolver;
    private const int SessionsPerBatch = 24;

    public OpenLinesConversationCollector(
        BitrixBatchService batchService,
        OpenLinesSessionEnumerator enumerator,
        CrmEntityResolver crmResolver,
        UserResolver userResolver)
    {
        _batchService = batchService;
        _enumerator = enumerator;
        _crmResolver = crmResolver;
        _userResolver = userResolver;
    }

    public async Task<CollectedSessions> CollectAllAsync(string? createdFrom, CancellationToken ct = default)
    {
        Console.WriteLine($"[Collector] Phase 1: enumerating sessions (from={createdFrom ?? "(all)"})...");
        var metas = await CollectMetasAsync(createdFrom, ct);
        if (metas.Count == 0)
            return new CollectedSessions();

        Console.WriteLine($"[Collector] Phase 2: fetching history+dialog for {metas.Count} sessions...");
        var rawList = await FetchSessionsRawAsync(metas, ct);

        Console.WriteLine("[Collector] Phase 3: resolving CRM entities...");
        var crmRefs = rawList.SelectMany(ExtractCrmRefs).ToList();
        var crmEntities = await _crmResolver.ResolveAsync(crmRefs, ct);

        Console.WriteLine("[Collector] Phase 4: resolving users (operators + message authors)...");
        var userIds = rawList.SelectMany(ExtractUserIds).Distinct().ToList();
        var users = await _userResolver.ResolveAsync(userIds, ct);

        return new CollectedSessions
        {
            Sessions = rawList,
            CrmEntitiesByKey = crmEntities,
            UsersById = users
        };
    }

    private async Task<List<SessionMeta>> CollectMetasAsync(string? createdFrom, CancellationToken ct)
    {
        var metas = new List<SessionMeta>();
        await foreach (var meta in _enumerator.EnumerateAsync(createdFrom, ct))
            metas.Add(meta);
        return metas;
    }

    private async Task<IReadOnlyList<SessionRawData>> FetchSessionsRawAsync(
        List<SessionMeta> metas,
        CancellationToken ct)
    {
        var rawList = new List<SessionRawData>(metas.Count);
        var chunks = metas.Chunk(SessionsPerBatch).ToList();
        var batchNumber = 0;

        foreach (var chunk in chunks)
        {
            batchNumber++;
            Console.WriteLine($"[Collector] Batch {batchNumber}/{chunks.Count}: sessions {chunk[0].SessionId}..{chunk[^1].SessionId}");

            var commands = BuildBatchCommands(chunk);
            var (results, nextPages) = await _batchService.ExecuteAsync(commands, ct);
            if (nextPages.Count > 0)
                await _batchService.FetchRemainingPagesAsync(commands, nextPages, results, ct);

            foreach (var meta in chunk)
                rawList.Add(AssembleRaw(meta, results));
        }

        return rawList;
    }

    private static Dictionary<string, string> BuildBatchCommands(SessionMeta[] chunk)
    {
        var commands = new Dictionary<string, string>();
        foreach (var meta in chunk)
        {
            commands[$"history_{meta.SessionId}"] = $"imopenlines.session.history.get?SESSION_ID={meta.SessionId}";
            commands[$"dialog_{meta.SessionId}"] = $"imopenlines.dialog.get?SESSION_ID={meta.SessionId}";
        }
        return commands;
    }

    private static SessionRawData AssembleRaw(SessionMeta meta, Dictionary<string, JsonElement> results)
    {
        var raw = new SessionRawData
        {
            SessionId = meta.SessionId,
            Activity = meta.Activity
        };
        if (results.TryGetValue($"history_{meta.SessionId}", out var history))
            raw.SessionHistory = history;
        if (results.TryGetValue($"dialog_{meta.SessionId}", out var dialog))
            raw.DialogInfo = dialog;
        return raw;
    }

    private static IEnumerable<(string Type, string Id)> ExtractCrmRefs(SessionRawData raw)
    {
        if (raw.DialogInfo.ValueKind != JsonValueKind.Object) return [];
        if (!raw.DialogInfo.TryGetProperty("entity_data_2", out var bindings)) return [];
        return EntityBindingsParser.Parse(bindings);
    }

    private static IEnumerable<string> ExtractUserIds(SessionRawData raw)
    {
        if (raw.SessionHistory.ValueKind == JsonValueKind.Object &&
            raw.SessionHistory.TryGetProperty("users", out var users) &&
            users.ValueKind == JsonValueKind.Object)
        {
            foreach (var user in users.EnumerateObject())
                if (!string.IsNullOrEmpty(user.Name) && user.Name != "0")
                    yield return user.Name;
        }

        if (raw.Activity.ValueKind == JsonValueKind.Object &&
            raw.Activity.TryGetProperty("RESPONSIBLE_ID", out var respId) &&
            respId.ValueKind is JsonValueKind.String or JsonValueKind.Number)
        {
            var id = respId.ValueKind == JsonValueKind.String ? respId.GetString()! : respId.GetRawText();
            if (!string.IsNullOrEmpty(id) && id != "0") yield return id;
        }
    }
}
