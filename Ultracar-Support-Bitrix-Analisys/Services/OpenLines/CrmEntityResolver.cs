using System.Text.Json;

namespace Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

public class CrmEntityResolver
{
    private readonly BitrixBatchService _batchService;
    private static readonly HashSet<string> SupportedTypes = ["lead", "contact", "company", "deal"];

    public CrmEntityResolver(BitrixBatchService batchService)
    {
        _batchService = batchService;
    }

    public async Task<IReadOnlyDictionary<string, JsonElement>> ResolveAsync(
        IEnumerable<(string Type, string Id)> refs,
        CancellationToken ct = default)
    {
        var unique = refs
            .Where(r => SupportedTypes.Contains(r.Type) && !string.IsNullOrEmpty(r.Id) && r.Id != "0")
            .Select(r => (Type: r.Type.ToLowerInvariant(), r.Id))
            .Distinct()
            .ToList();

        var resolved = new Dictionary<string, JsonElement>();
        if (unique.Count == 0) return resolved;

        Console.WriteLine($"[CrmResolver] Resolving {unique.Count} unique CRM entities...");

        var commands = BuildCommands(unique);
        var (results, _) = await _batchService.ExecuteAsync(commands, ct);

        foreach (var (type, id) in unique)
        {
            var commandKey = CommandKey(type, id);
            if (!results.TryGetValue(commandKey, out var entity)) continue;
            resolved[CanonicalKey(type, id)] = entity;
        }

        return resolved;
    }

    private static Dictionary<string, string> BuildCommands(IEnumerable<(string Type, string Id)> refs)
    {
        var commands = new Dictionary<string, string>();
        foreach (var (type, id) in refs)
            commands[CommandKey(type, id)] = $"crm.{type}.get?id={id}";
        return commands;
    }

    private static string CommandKey(string type, string id) => $"crm_{type}_{id}";

    public static string CanonicalKey(string type, string id) => $"{type.ToLowerInvariant()}:{id}";
}
