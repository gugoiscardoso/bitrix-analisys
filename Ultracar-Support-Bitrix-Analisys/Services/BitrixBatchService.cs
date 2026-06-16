using System.Text.Json;

namespace Ultracar_Support_Bitrix_Analisys.Services;

public class BitrixBatchService
{
    private readonly BitrixApiClient _apiClient;
    private const int MaxCommandsPerBatch = 50;

    public BitrixBatchService(BitrixApiClient apiClient)
    {
        _apiClient = apiClient;
    }

    /// <summary>
    /// Executes commands in batches of 50. Returns all sub-results keyed by command name.
    /// Also returns follow-up info for paginated sub-commands via the out parameter.
    /// </summary>
    public async Task<(Dictionary<string, JsonElement> Results, Dictionary<string, int> NextPages)> ExecuteAsync(
        Dictionary<string, string> commands,
        CancellationToken ct = default)
    {
        var allResults = new Dictionary<string, JsonElement>();
        var allNextPages = new Dictionary<string, int>();

        var chunks = commands
            .Chunk(MaxCommandsPerBatch)
            .Select(chunk => chunk.ToDictionary(kv => kv.Key, kv => kv.Value))
            .ToList();

        foreach (var chunk in chunks)
        {
            var response = await _apiClient.PostBatchAsync(chunk, ct);
            var container = response.Result;

            if (container != null)
            {
                foreach (var kv in container.GetResults())
                    allResults[kv.Key] = kv.Value;

                foreach (var kv in container.GetNextPages())
                    allNextPages[kv.Key] = kv.Value;
            }
        }

        return (allResults, allNextPages);
    }

    /// <summary>
    /// Fetches all pages for sub-commands that had pagination (result_next).
    /// Appends results to the provided dictionary.
    /// </summary>
    public async Task FetchRemainingPagesAsync(
        Dictionary<string, string> originalCommands,
        Dictionary<string, int> nextPages,
        Dictionary<string, JsonElement> allResults,
        CancellationToken ct = default)
    {
        var pendingPages = new Dictionary<string, int>(nextPages);

        while (pendingPages.Count > 0)
        {
            var followUpCommands = new Dictionary<string, string>();
            foreach (var (key, start) in pendingPages)
            {
                if (!originalCommands.TryGetValue(key, out var originalCmd))
                    continue;

                var separator = originalCmd.Contains('?') ? "&" : "?";
                var pageKey = $"{key}_p{start}";
                followUpCommands[pageKey] = $"{originalCmd}{separator}start={start}";
            }

            if (followUpCommands.Count == 0)
                break;

            var (results, newNextPages) = await ExecuteAsync(followUpCommands, ct);

            foreach (var kv in results)
            {
                var baseKey = GetBaseKey(kv.Key);
                if (allResults.TryGetValue(baseKey, out var existing))
                    allResults[baseKey] = MergeArrayResults(existing, kv.Value);
                else
                    allResults[kv.Key] = kv.Value;
            }

            pendingPages.Clear();
            foreach (var kv in newNextPages)
            {
                var baseKey = GetBaseKey(kv.Key);
                if (originalCommands.ContainsKey(baseKey))
                    pendingPages[baseKey] = kv.Value;
            }
        }
    }

    private static string GetBaseKey(string paginatedKey)
    {
        var idx = paginatedKey.IndexOf("_p", StringComparison.Ordinal);
        if (idx < 0) return paginatedKey;

        var suffix = paginatedKey[(idx + 2)..];
        return int.TryParse(suffix, out _) ? paginatedKey[..idx] : paginatedKey;
    }

    private static JsonElement MergeArrayResults(JsonElement existing, JsonElement newItems)
    {
        if (existing.ValueKind != JsonValueKind.Array || newItems.ValueKind != JsonValueKind.Array)
            return newItems;

        using var ms = new MemoryStream();
        using var writer = new Utf8JsonWriter(ms);
        writer.WriteStartArray();

        foreach (var item in existing.EnumerateArray())
            item.WriteTo(writer);
        foreach (var item in newItems.EnumerateArray())
            item.WriteTo(writer);

        writer.WriteEndArray();
        writer.Flush();

        return JsonDocument.Parse(ms.ToArray()).RootElement.Clone();
    }
}
