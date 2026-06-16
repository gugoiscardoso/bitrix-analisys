using System.Text.Json;
using Ultracar_Support_Bitrix_Analisys.Models.OpenLines;
using static Ultracar_Support_Bitrix_Analisys.Services.OpenLines.JsonReadHelpers;

namespace Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

/// <summary>
/// Constrói FileRow a partir de SessionHistory.files. O Bitrix retorna files
/// como objeto (chave = fileId) OU array; aqui tratamos os dois.
/// </summary>
public static class ConversationFiles
{
    public static List<FileRow> Build(SessionRawData raw)
    {
        var rows = new List<FileRow>();
        if (raw.SessionHistory.ValueKind != JsonValueKind.Object) return rows;
        if (!raw.SessionHistory.TryGetProperty("files", out var files)) return rows;

        switch (files.ValueKind)
        {
            case JsonValueKind.Object:
                foreach (var entry in files.EnumerateObject())
                    rows.Add(ToRow(entry.Value, raw.SessionId, fallbackId: entry.Name));
                break;
            case JsonValueKind.Array:
                foreach (var file in files.EnumerateArray())
                    rows.Add(ToRow(file, raw.SessionId, fallbackId: null));
                break;
        }
        return rows;
    }

    private static FileRow ToRow(JsonElement file, string sessionId, string? fallbackId) => new()
    {
        FileId = GetStringOrNull(file, "id", "ID") ?? fallbackId ?? string.Empty,
        MessageId = GetString(file, "messageId", "message_id", "MESSAGE_ID"),
        SessionId = sessionId,
        FileName = GetString(file, "name", "NAME", "fileName"),
        MimeType = GetString(file, "type", "TYPE", "mimeType"),
        SizeBytes = GetInt64OrNull(file, "size", "SIZE", "fileSize"),
        DownloadUrl = GetString(file, "urlDownload", "URL_DOWNLOAD", "url"),
        IsVoiceNote = GetBool(file, "isVoiceMessage", "isVoiceNote", "isVoice")
    };
}
