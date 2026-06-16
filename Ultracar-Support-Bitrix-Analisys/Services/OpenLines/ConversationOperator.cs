using System.Text.Json;
using Ultracar_Support_Bitrix_Analisys.Models.OpenLines;
using static Ultracar_Support_Bitrix_Analisys.Services.OpenLines.JsonReadHelpers;

namespace Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

/// <summary>
/// Resolve o atendente principal de uma sessão. Heurística:
///   1) activity.RESPONSIBLE_ID, se presente
///   2) Primeiro user em historyUsers com connector==false e bot==false
/// </summary>
public static class ConversationOperator
{
    public static string PickOperatorId(SessionRawData raw, IReadOnlyDictionary<string, JsonElement> historyUsers)
    {
        var fromActivity = GetStringOrNull(raw.Activity, "RESPONSIBLE_ID", "responsible_id");
        if (!string.IsNullOrEmpty(fromActivity) && fromActivity != "0") return fromActivity;

        foreach (var (userId, user) in historyUsers)
        {
            if (userId == "0") continue;
            if (GetBool(user, "connector")) continue;
            if (GetBool(user, "bot")) continue;
            return userId;
        }
        return string.Empty;
    }

    public static OperatorRow? Build(
        string operatorId,
        IReadOnlyDictionary<string, JsonElement> usersById,
        IReadOnlyDictionary<string, JsonElement> historyUsers)
    {
        if (string.IsNullOrEmpty(operatorId)) return null;

        if (usersById.TryGetValue(operatorId, out var bitrixUser))
            return BuildFromBitrixUser(operatorId, bitrixUser);

        if (historyUsers.TryGetValue(operatorId, out var historyUser))
            return BuildFromHistoryUser(operatorId, historyUser);

        return new OperatorRow { UserId = operatorId, FullName = $"(unknown user {operatorId})" };
    }

    private static OperatorRow BuildFromBitrixUser(string userId, JsonElement user)
    {
        var first = GetStringOrNull(user, "NAME", "name") ?? string.Empty;
        var last = GetStringOrNull(user, "LAST_NAME", "lastName") ?? string.Empty;
        var fullName = $"{first} {last}".Trim();
        if (string.IsNullOrEmpty(fullName))
            fullName = GetString(user, "FULL_NAME", "fullName");
        return new OperatorRow
        {
            UserId = userId,
            FullName = string.IsNullOrEmpty(fullName) ? $"(user {userId})" : fullName,
            Email = GetString(user, "EMAIL", "email"),
            Department = ExtractDepartment(user)
        };
    }

    private static OperatorRow BuildFromHistoryUser(string userId, JsonElement user) => new()
    {
        UserId = userId,
        FullName = GetStringOrNull(user, "name", "NAME") ?? $"(user {userId})",
        Email = GetString(user, "email", "EMAIL"),
        Department = GetString(user, "workPosition", "work_position", "WORK_POSITION")
    };

    private static string ExtractDepartment(JsonElement user)
    {
        var work = GetStringOrNull(user, "WORK_POSITION", "workPosition");
        if (!string.IsNullOrEmpty(work)) return work;

        if (user.ValueKind != JsonValueKind.Object) return string.Empty;
        if (!user.TryGetProperty("UF_DEPARTMENT", out var dept) || dept.ValueKind != JsonValueKind.Array)
            return string.Empty;

        var ids = new List<string>();
        foreach (var item in dept.EnumerateArray())
            if (item.ValueKind == JsonValueKind.Number)
                ids.Add(item.GetRawText());
        return string.Join(";", ids);
    }
}
