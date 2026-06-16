using System.Text.Json;
using Ultracar_Support_Bitrix_Analisys.Configuration;

namespace Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

public class OpenLinesDiscoveryService
{
    private readonly BitrixApiClient _apiClient;
    private readonly BitrixSettings _settings;
    private const string CandidateProviderId = "IMOPENLINES_SESSION";

    public OpenLinesDiscoveryService(BitrixApiClient apiClient, BitrixSettings settings)
    {
        _apiClient = apiClient;
        _settings = settings;
    }

    public async Task RunAsync(CancellationToken ct = default)
    {
        var from = _settings.EffectiveOpenLinesCreatedFrom ?? "2025-01-01";
        Console.WriteLine($"[Discovery] CreatedFrom filter: {from}");
        Console.WriteLine();

        await PrintDistinctProvidersAsync(from, ct);
        Console.WriteLine();

        var sampleSessionId = await ProbeImOpenlineProviderAsync(from, ct);
        Console.WriteLine();

        if (string.IsNullOrEmpty(sampleSessionId))
        {
            Console.WriteLine("[Discovery] Nao foi possivel obter sample SESSION_ID. " +
                              "Ajuste CandidateProviderId no Enumerator e rode novamente.");
            return;
        }

        await ProbeSessionHistoryAsync(sampleSessionId, ct);
        Console.WriteLine();
        await ProbeDialogAsync(sampleSessionId, ct);
        Console.WriteLine();
        Console.WriteLine("[Discovery] Done. Valide o output acima antes de rodar --mode conversations.");
    }

    private async Task PrintDistinctProvidersAsync(string from, CancellationToken ct)
    {
        Console.WriteLine("[Discovery] Listando PROVIDER_IDs distintos em crm.activity.list...");
        var parameters = new Dictionary<string, object>
        {
            ["filter"] = new Dictionary<string, object> { [">CREATED"] = from },
            ["select"] = new[] { "ID", "PROVIDER_ID", "PROVIDER_TYPE_ID", "ASSOCIATED_ENTITY_ID", "SUBJECT", "CREATED" },
            ["order"] = new Dictionary<string, string> { ["ID"] = "DESC" },
            ["start"] = 0
        };

        var response = await _apiClient.PostAsync("crm.activity.list", parameters, ct);
        if (response.Result.ValueKind != JsonValueKind.Array)
        {
            Console.WriteLine("  (sem atividades no periodo)");
            return;
        }

        var distinct = new Dictionary<string, (string TypeId, string Subject, string SampleSessionId)>();
        foreach (var activity in response.Result.EnumerateArray())
        {
            var providerId = TryString(activity, "PROVIDER_ID") ?? "(null)";
            if (distinct.ContainsKey(providerId)) continue;
            distinct[providerId] = (
                TryString(activity, "PROVIDER_TYPE_ID") ?? "(null)",
                TryString(activity, "SUBJECT") ?? string.Empty,
                TryString(activity, "ASSOCIATED_ENTITY_ID") ?? string.Empty);
        }

        foreach (var (provider, info) in distinct)
            Console.WriteLine($"  provider={provider,-25} type={info.TypeId,-25} sampleSessionId={info.SampleSessionId,-12} subject='{Truncate(info.Subject, 60)}'");
    }

    private async Task<string> ProbeImOpenlineProviderAsync(string from, CancellationToken ct)
    {
        Console.WriteLine($"[Discovery] Probe PROVIDER_ID=\"{CandidateProviderId}\" (>=CREATED={from})...");
        var parameters = new Dictionary<string, object>
        {
            ["filter"] = new Dictionary<string, object>
            {
                ["PROVIDER_ID"] = CandidateProviderId,
                [">=CREATED"] = from
            },
            ["select"] = new[] { "ID", "ASSOCIATED_ENTITY_ID", "OWNER_TYPE_ID", "OWNER_ID", "CREATED", "END_TIME" },
            ["order"] = new Dictionary<string, string> { ["ID"] = "DESC" },
            ["start"] = 0
        };

        var response = await _apiClient.PostAsync("crm.activity.list", parameters, ct);
        var total = response.Total ?? 0;
        var count = response.Result.ValueKind == JsonValueKind.Array ? response.Result.GetArrayLength() : 0;
        Console.WriteLine($"  total={total}, first page count={count}");

        if (count == 0) return string.Empty;
        var first = response.Result[0];
        var sessionId = TryString(first, "ASSOCIATED_ENTITY_ID") ?? string.Empty;
        Console.WriteLine($"  sample SESSION_ID={sessionId} OWNER_TYPE_ID={TryString(first, "OWNER_TYPE_ID")} OWNER_ID={TryString(first, "OWNER_ID")}");
        return sessionId;
    }

    private async Task ProbeSessionHistoryAsync(string sessionId, CancellationToken ct)
    {
        Console.WriteLine($"[Discovery] imopenlines.session.history.get SESSION_ID={sessionId}");
        var parameters = new Dictionary<string, object> { ["SESSION_ID"] = sessionId };
        var response = await _apiClient.PostAsync("imopenlines.session.history.get", parameters, ct);
        var result = response.Result;
        if (result.ValueKind != JsonValueKind.Object)
        {
            Console.WriteLine($"  (resposta nao-objeto: {result.ValueKind})");
            return;
        }

        var keys = result.EnumerateObject().Select(p => p.Name).ToList();
        Console.WriteLine($"  keys: [{string.Join(", ", keys)}]");
        if (result.TryGetProperty("message", out var messages))
        {
            var msgCount = messages.ValueKind switch
            {
                JsonValueKind.Array => messages.GetArrayLength(),
                JsonValueKind.Object => messages.EnumerateObject().Count(),
                _ => -1
            };
            Console.WriteLine($"  message kind: {messages.ValueKind}, count: {msgCount}");
        }
        if (result.TryGetProperty("users", out var users) && users.ValueKind == JsonValueKind.Object)
            Console.WriteLine($"  users count: {users.EnumerateObject().Count()}");
        if (result.TryGetProperty("files", out var files))
            Console.WriteLine($"  files kind: {files.ValueKind}");
        var size = JsonSerializer.Serialize(result).Length;
        Console.WriteLine($"  payload bytes: {size}");
    }

    private async Task ProbeDialogAsync(string sessionId, CancellationToken ct)
    {
        Console.WriteLine($"[Discovery] imopenlines.dialog.get SESSION_ID={sessionId}");
        var parameters = new Dictionary<string, object> { ["SESSION_ID"] = sessionId };
        var response = await _apiClient.PostAsync("imopenlines.dialog.get", parameters, ct);
        var result = response.Result;
        if (result.ValueKind != JsonValueKind.Object)
        {
            Console.WriteLine($"  (resposta nao-objeto: {result.ValueKind})");
            return;
        }

        Console.WriteLine($"  USER_CODE: {TryString(result, "USER_CODE") ?? "(ausente)"}");
        Console.WriteLine($"  entity_type: {TryString(result, "entity_type") ?? "(ausente)"}");
        Console.WriteLine($"  entity_id:   {TryString(result, "entity_id") ?? "(ausente)"}");
        foreach (var name in new[] { "entity_data_1", "entity_data_2", "entity_data_3" })
        {
            if (!result.TryGetProperty(name, out var data)) continue;
            Console.WriteLine($"  {name} kind={data.ValueKind}, raw={Truncate(data.GetRawText(), 200)}");
        }
        var keys = result.EnumerateObject().Select(p => p.Name).ToList();
        Console.WriteLine($"  keys: [{string.Join(", ", keys)}]");
    }

    private static string? TryString(JsonElement el, string prop)
    {
        if (el.ValueKind != JsonValueKind.Object || !el.TryGetProperty(prop, out var value)) return null;
        return value.ValueKind switch
        {
            JsonValueKind.String => value.GetString(),
            JsonValueKind.Number => value.GetRawText(),
            JsonValueKind.True or JsonValueKind.False => value.GetRawText(),
            _ => null
        };
    }

    private static string Truncate(string s, int max) =>
        s.Length <= max ? s : s[..max] + "...";
}
