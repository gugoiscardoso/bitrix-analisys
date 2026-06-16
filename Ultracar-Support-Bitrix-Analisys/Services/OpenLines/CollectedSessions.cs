using System.Text.Json;
using Ultracar_Support_Bitrix_Analisys.Models.OpenLines;

namespace Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

public sealed class CollectedSessions
{
    public IReadOnlyList<SessionRawData> Sessions { get; init; } = [];
    public IReadOnlyDictionary<string, JsonElement> CrmEntitiesByKey { get; init; } = new Dictionary<string, JsonElement>();
    public IReadOnlyDictionary<string, JsonElement> UsersById { get; init; } = new Dictionary<string, JsonElement>();
}
