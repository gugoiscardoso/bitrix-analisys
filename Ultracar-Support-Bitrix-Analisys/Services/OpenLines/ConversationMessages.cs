using System.Text.Json;
using Ultracar_Support_Bitrix_Analisys.Models.OpenLines;
using static Ultracar_Support_Bitrix_Analisys.Services.OpenLines.JsonReadHelpers;

namespace Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

/// <summary>
/// Constrói MessageRow a partir de SessionHistory.message[].
/// Classifica AuthorType com base no flag connector/bot dos users do history.
/// </summary>
public static class ConversationMessages
{
    public static List<MessageRow> Build(
        SessionRawData raw,
        IReadOnlyDictionary<string, JsonElement> historyUsers,
        IReadOnlyDictionary<string, JsonElement> usersById)
    {
        var rows = new List<MessageRow>();
        if (raw.SessionHistory.ValueKind != JsonValueKind.Object) return rows;
        if (!raw.SessionHistory.TryGetProperty("message", out var messages)) return rows;

        foreach (var msg in EnumerateMessages(messages))
            rows.Add(ToRow(msg, raw.SessionId, historyUsers, usersById));

        return rows.OrderBy(r => r.Timestamp ?? DateTime.MinValue).ToList();
    }

    private static IEnumerable<JsonElement> EnumerateMessages(JsonElement messages) => messages.ValueKind switch
    {
        JsonValueKind.Array => messages.EnumerateArray(),
        JsonValueKind.Object => messages.EnumerateObject().Select(p => p.Value),
        _ => []
    };

    private static MessageRow ToRow(
        JsonElement msg,
        string sessionId,
        IReadOnlyDictionary<string, JsonElement> historyUsers,
        IReadOnlyDictionary<string, JsonElement> usersById)
    {
        var authorId = GetString(msg, "author_id", "AUTHOR_ID", "id_user");
        var author = ClassifyAuthor(authorId, historyUsers);
        return new MessageRow
        {
            MessageId = GetString(msg, "id", "ID"),
            SessionId = sessionId,
            Timestamp = GetDateTimeOrNull(msg, "date", "DATE", "date_create"),
            AuthorId = authorId,
            AuthorType = author.ToString(),
            AuthorName = ResolveAuthorName(authorId, historyUsers, usersById),
            TextContent = GetString(msg, "text", "TEXT", "message"),
            MessageType = ClassifyMessageType(msg, author),
            HasFiles = HasFilesAttached(msg),
            FilesCount = ExtractFilesCount(msg)
        };
    }

    private static AuthorType ClassifyAuthor(string authorId, IReadOnlyDictionary<string, JsonElement> historyUsers)
    {
        if (string.IsNullOrEmpty(authorId) || authorId == "0") return AuthorType.System;
        if (!historyUsers.TryGetValue(authorId, out var user)) return AuthorType.Unknown;
        if (GetBool(user, "connector")) return AuthorType.Customer;
        if (GetBool(user, "bot")) return AuthorType.Bot;
        return AuthorType.Operator;
    }

    private static string ResolveAuthorName(
        string authorId,
        IReadOnlyDictionary<string, JsonElement> historyUsers,
        IReadOnlyDictionary<string, JsonElement> usersById)
    {
        if (string.IsNullOrEmpty(authorId) || authorId == "0") return "(system)";
        if (historyUsers.TryGetValue(authorId, out var hUser))
        {
            var name = GetStringOrNull(hUser, "name", "NAME");
            if (!string.IsNullOrEmpty(name)) return name;
        }
        if (usersById.TryGetValue(authorId, out var bUser))
        {
            var first = GetStringOrNull(bUser, "NAME") ?? string.Empty;
            var last = GetStringOrNull(bUser, "LAST_NAME") ?? string.Empty;
            var full = $"{first} {last}".Trim();
            if (!string.IsNullOrEmpty(full)) return full;
        }
        return $"(user {authorId})";
    }

    private static string ClassifyMessageType(JsonElement msg, AuthorType author)
    {
        if (author == AuthorType.System) return "system";
        if (!msg.TryGetProperty("params", out var p) || p.ValueKind != JsonValueKind.Object) return "text";
        if (GetBool(p, "IS_DELETED")) return "deleted";
        if (GetBool(p, "IS_EDITED")) return "edited";
        return "text";
    }

    private static bool HasFilesAttached(JsonElement msg)
    {
        if (!msg.TryGetProperty("params", out var p) || p.ValueKind != JsonValueKind.Object) return false;
        if (!p.TryGetProperty("FILE_ID", out var files)) return false;
        return files.ValueKind == JsonValueKind.Array && files.GetArrayLength() > 0;
    }

    private static int ExtractFilesCount(JsonElement msg)
    {
        if (!msg.TryGetProperty("params", out var p) || p.ValueKind != JsonValueKind.Object) return 0;
        if (!p.TryGetProperty("FILE_ID", out var files)) return 0;
        return files.ValueKind == JsonValueKind.Array ? files.GetArrayLength() : 0;
    }
}
