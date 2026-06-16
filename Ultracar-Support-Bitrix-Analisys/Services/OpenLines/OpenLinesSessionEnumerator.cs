using System.Runtime.CompilerServices;
using System.Text.Json;

namespace Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

public class OpenLinesSessionEnumerator
{
    private readonly BitrixApiClient _apiClient;

    public const string OpenLinesProviderId = "IMOPENLINES_SESSION";

    public OpenLinesSessionEnumerator(BitrixApiClient apiClient)
    {
        _apiClient = apiClient;
    }

    public async IAsyncEnumerable<SessionMeta> EnumerateAsync(
        string? createdFrom,
        [EnumeratorCancellation] CancellationToken ct = default)
    {
        var filter = new Dictionary<string, object>
        {
            ["PROVIDER_ID"] = OpenLinesProviderId
        };
        if (!string.IsNullOrWhiteSpace(createdFrom))
            filter[">=CREATED"] = createdFrom;

        var parameters = new Dictionary<string, object>
        {
            ["filter"] = filter,
            ["select"] = new[]
            {
                "ID", "PROVIDER_ID", "PROVIDER_TYPE_ID", "ASSOCIATED_ENTITY_ID",
                "OWNER_ID", "OWNER_TYPE_ID", "RESPONSIBLE_ID",
                "CREATED", "START_TIME", "END_TIME", "SUBJECT"
            }
        };

        var count = 0;
        await foreach (var activity in _apiClient.PaginateAsync("crm.activity.list", parameters, resultProperty: null, ct))
        {
            var sessionId = ExtractSessionId(activity);
            if (string.IsNullOrEmpty(sessionId) || sessionId == "0") continue;

            count++;
            if (count % 100 == 0)
                Console.WriteLine($"[Enumerator] Listed {count} sessions...");

            yield return new SessionMeta
            {
                SessionId = sessionId,
                Activity = activity.Clone()
            };
        }

        Console.WriteLine($"[Enumerator] Total sessions found: {count}");
    }

    private static string ExtractSessionId(JsonElement activity)
    {
        if (activity.ValueKind != JsonValueKind.Object) return string.Empty;
        if (!activity.TryGetProperty("ASSOCIATED_ENTITY_ID", out var prop) &&
            !activity.TryGetProperty("associated_entity_id", out prop))
            return string.Empty;

        return prop.ValueKind switch
        {
            JsonValueKind.String => prop.GetString() ?? string.Empty,
            JsonValueKind.Number => prop.GetInt64().ToString(),
            _ => string.Empty
        };
    }
}

public sealed class SessionMeta
{
    public string SessionId { get; init; } = string.Empty;
    public JsonElement Activity { get; init; }
}
