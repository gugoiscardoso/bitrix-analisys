using System.Text.Json;

namespace Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

public class UserResolver
{
    private readonly BitrixBatchService _batchService;
    private readonly Dictionary<string, JsonElement> _cache = new();

    public UserResolver(BitrixBatchService batchService)
    {
        _batchService = batchService;
    }

    public async Task<IReadOnlyDictionary<string, JsonElement>> ResolveAsync(
        IEnumerable<string> userIds,
        CancellationToken ct = default)
    {
        var pending = userIds
            .Where(id => !string.IsNullOrEmpty(id) && id != "0" && !_cache.ContainsKey(id))
            .Distinct()
            .ToList();

        if (pending.Count > 0)
        {
            Console.WriteLine($"[UserResolver] Fetching {pending.Count} new users (cache has {_cache.Count})...");
            var commands = pending.ToDictionary(id => $"user_{id}", id => $"user.get?ID={id}");
            var (results, _) = await _batchService.ExecuteAsync(commands, ct);
            foreach (var id in pending)
            {
                if (!results.TryGetValue($"user_{id}", out var user)) continue;
                _cache[id] = UnwrapSingle(user);
            }
        }

        var resolved = new Dictionary<string, JsonElement>();
        foreach (var id in userIds.Distinct())
        {
            if (_cache.TryGetValue(id, out var user))
                resolved[id] = user;
        }
        return resolved;
    }

    private static JsonElement UnwrapSingle(JsonElement element)
    {
        if (element.ValueKind == JsonValueKind.Array && element.GetArrayLength() > 0)
            return element[0].Clone();
        return element.Clone();
    }
}
