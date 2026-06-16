using System.Text.Json;
using System.Text.RegularExpressions;
using Ultracar_Support_Bitrix_Analisys.Models.OpenLines;
using static Ultracar_Support_Bitrix_Analisys.Services.OpenLines.JsonReadHelpers;

namespace Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

/// <summary>
/// Identifica o canal de uma sessão. Estratégia em camadas:
///   1) USER_CODE em imopenlines.dialog.get (formato &lt;connector&gt;|&lt;LINE_ID&gt;|...)
///   2) Subject da activity ("Open Channel chat: '...' (WhatsApp ...)") via regex
/// Se nenhuma camada conseguir identificar, retorna ChannelKind.Unknown.
/// </summary>
public static class UserCodeParser
{
    private static readonly Regex SubjectChannelRegex = new(
        @"\((WhatsApp|Telegram|Live\s*chat|Facebook|Instagram|Email|Voximplant|Wazapp|edna)[^)]*\)",
        RegexOptions.IgnoreCase | RegexOptions.Compiled);

    public static UserCodeInfo Parse(JsonElement dialogInfo, JsonElement activity)
    {
        var fromCode = ParseFromUserCode(dialogInfo);
        if (fromCode.Channel != ChannelKind.Unknown || !string.IsNullOrEmpty(fromCode.ConnectorRaw))
            return fromCode;

        var fromEntityId = ParseFromEntityId(dialogInfo);
        if (fromEntityId.Channel != ChannelKind.Unknown || !string.IsNullOrEmpty(fromEntityId.ConnectorRaw))
            return fromEntityId;

        var fromSubject = ParseFromActivitySubject(activity);
        return fromSubject ?? fromCode;
    }

    /// <summary>
    /// Em tenants onde USER_CODE não vem populado, o campo entity_id da dialog
    /// carrega o mesmo formato: "&lt;connector&gt;|&lt;LINE_ID&gt;|&lt;CONNECTOR_CHAT_ID&gt;|&lt;CONNECTOR_USER_ID&gt;".
    /// Ex: "whatsapp|7|+5591980702472|43403" — o ConnectorChatId é o número do cliente.
    /// </summary>
    private static UserCodeInfo ParseFromEntityId(JsonElement dialogInfo)
    {
        var raw = GetStringOrNull(dialogInfo, "entity_id", "ENTITY_ID");
        if (string.IsNullOrEmpty(raw) || !raw.Contains('|'))
            return new UserCodeInfo(string.Empty, string.Empty, string.Empty, string.Empty, ChannelKind.Unknown);

        var parts = raw.Split('|');
        var connector = parts.Length > 0 ? parts[0] : string.Empty;
        var lineId = parts.Length > 1 ? parts[1] : string.Empty;
        var connectorChatId = parts.Length > 2 ? parts[2] : string.Empty;
        var connectorUserId = parts.Length > 3 ? parts[3] : string.Empty;
        return new UserCodeInfo(connector, lineId, connectorChatId, connectorUserId, MapChannel(connector));
    }

    private static UserCodeInfo ParseFromUserCode(JsonElement dialogInfo)
    {
        var raw = ExtractRaw(dialogInfo);
        if (string.IsNullOrEmpty(raw))
            return new UserCodeInfo(string.Empty, string.Empty, string.Empty, string.Empty, ChannelKind.Unknown);

        var parts = raw.Split('|');
        var connector = parts.Length > 0 ? parts[0] : string.Empty;
        var lineId = parts.Length > 1 ? parts[1] : string.Empty;
        var connectorChatId = parts.Length > 2 ? parts[2] : string.Empty;
        var connectorUserId = parts.Length > 3 ? parts[3] : string.Empty;
        return new UserCodeInfo(connector, lineId, connectorChatId, connectorUserId, MapChannel(connector));
    }

    private static UserCodeInfo? ParseFromActivitySubject(JsonElement activity)
    {
        var subject = GetStringOrNull(activity, "SUBJECT", "subject");
        if (string.IsNullOrEmpty(subject)) return null;

        var match = SubjectChannelRegex.Match(subject);
        if (!match.Success) return null;

        var connectorRaw = match.Groups[1].Value;
        return new UserCodeInfo(connectorRaw, string.Empty, string.Empty, string.Empty, MapChannel(connectorRaw));
    }

    private static string ExtractRaw(JsonElement dialogInfo)
    {
        if (dialogInfo.ValueKind != JsonValueKind.Object) return string.Empty;
        foreach (var name in new[] { "USER_CODE", "user_code", "userCode" })
        {
            if (!dialogInfo.TryGetProperty(name, out var prop)) continue;
            if (prop.ValueKind == JsonValueKind.String) return prop.GetString() ?? string.Empty;
        }
        return string.Empty;
    }

    /// <summary>
    /// Mapeia o prefixo connector para o enum ChannelKind. Lista parcial — ajustar
    /// conforme a saída do --mode discover identificar os connectors do tenant.
    /// </summary>
    private static ChannelKind MapChannel(string connector) => connector.ToLowerInvariant() switch
    {
        "wazapp" or "wz" or "whatsapp" or "whatsappbytwilio" or "edna_whatsapp" => ChannelKind.WhatsApp,
        "telegrambot" or "telegram" => ChannelKind.Telegram,
        "livechat" => ChannelKind.LiveChat,
        "facebook" or "fbmessenger" or "facebookmessenger" => ChannelKind.Facebook,
        "instagram" or "instagramdirect" => ChannelKind.Instagram,
        "network" or "email" or "imap" => ChannelKind.Email,
        "voximplant" => ChannelKind.Voximplant,
        "" => ChannelKind.Unknown,
        _ => ChannelKind.Other
    };
}

public sealed record UserCodeInfo(
    string ConnectorRaw,
    string LineId,
    string ConnectorChatId,
    string ConnectorUserId,
    ChannelKind Channel);
