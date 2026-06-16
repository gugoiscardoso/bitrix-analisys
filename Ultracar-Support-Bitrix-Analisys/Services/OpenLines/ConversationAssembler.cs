using System.Text.Json;
using Ultracar_Support_Bitrix_Analisys.Models.OpenLines;
using static Ultracar_Support_Bitrix_Analisys.Services.OpenLines.JsonReadHelpers;

namespace Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

/// <summary>
/// Mapeia SessionRawData para AssembledSession (POCOs tipados para Excel).
/// Cada método auxiliar tem uma responsabilidade focada para manter ≤ 30 linhas.
/// </summary>
public class ConversationAssembler
{
    public AssembledSession AssembleSession(
        SessionRawData raw,
        IReadOnlyDictionary<string, JsonElement> crmEntitiesByKey,
        IReadOnlyDictionary<string, JsonElement> usersById)
    {
        var historyUsers = ExtractHistoryUsers(raw.SessionHistory);
        var userCode = UserCodeParser.Parse(raw.DialogInfo, raw.Activity);
        var messages = ConversationMessages.Build(raw, historyUsers, usersById);
        var files = ConversationFiles.Build(raw);
        var operatorId = ConversationOperator.PickOperatorId(raw, historyUsers);
        var operatorRow = ConversationOperator.Build(operatorId, usersById, historyUsers);
        var customer = ConversationCustomer.Build(raw, crmEntitiesByKey, historyUsers);
        EnrichCustomerWithConnectorPhone(customer, userCode);
        var conversation = BuildConversationRow(raw, userCode, customer, operatorRow, messages, files);
        return new AssembledSession
        {
            Conversation = conversation,
            Messages = messages,
            Files = files,
            Customer = customer,
            Operator = operatorRow
        };
    }

    private static IReadOnlyDictionary<string, JsonElement> ExtractHistoryUsers(JsonElement history)
    {
        if (history.ValueKind != JsonValueKind.Object) return new Dictionary<string, JsonElement>();
        if (!history.TryGetProperty("users", out var users) || users.ValueKind != JsonValueKind.Object)
            return new Dictionary<string, JsonElement>();

        var dict = new Dictionary<string, JsonElement>();
        foreach (var prop in users.EnumerateObject())
            dict[prop.Name] = prop.Value;
        return dict;
    }

    private static ConversationRow BuildConversationRow(
        SessionRawData raw,
        UserCodeInfo code,
        CustomerRow? customer,
        OperatorRow? op,
        List<MessageRow> messages,
        List<FileRow> files)
    {
        var counts = CountByAuthor(messages);
        var startedAt = messages.FirstOrDefault()?.Timestamp ?? GetDateTimeOrNull(raw.Activity, "START_TIME", "CREATED");
        var endedAt = messages.LastOrDefault()?.Timestamp ?? GetDateTimeOrNull(raw.Activity, "END_TIME");
        return new ConversationRow
        {
            SessionId = raw.SessionId,
            ChatId = ExtractChatId(raw),
            LineId = code.LineId,
            Channel = code.Channel.ToString(),
            ChannelRaw = code.ConnectorRaw,
            CustomerKey = customer?.CustomerKey ?? string.Empty,
            CustomerName = customer?.DisplayName ?? string.Empty,
            CustomerPhone = customer?.PhonesCsv ?? string.Empty,
            CustomerEmail = customer?.EmailsCsv ?? string.Empty,
            OperatorId = op?.UserId ?? string.Empty,
            OperatorName = op?.FullName ?? string.Empty,
            StartedAt = startedAt,
            EndedAt = endedAt,
            DurationMinutes = (startedAt.HasValue && endedAt.HasValue)
                ? (endedAt.Value - startedAt.Value).TotalMinutes : null,
            TotalMessages = messages.Count,
            CustomerMessages = counts.customer,
            OperatorMessages = counts.op,
            SystemMessages = counts.system,
            LinkedEntitiesCsv = BuildLinkedEntitiesCsv(raw.DialogInfo),
            HasFiles = files.Count > 0,
            HasVoiceNote = files.Any(f => f.IsVoiceNote)
        };
    }

    private static (int customer, int op, int system) CountByAuthor(List<MessageRow> messages)
    {
        var c = messages.Count(m => m.AuthorType == nameof(AuthorType.Customer));
        var o = messages.Count(m => m.AuthorType == nameof(AuthorType.Operator));
        var s = messages.Count(m => m.AuthorType == nameof(AuthorType.System));
        return (c, o, s);
    }

    private static string ExtractChatId(SessionRawData raw)
    {
        var fromHistoryChat = raw.SessionHistory.ValueKind == JsonValueKind.Object &&
                              raw.SessionHistory.TryGetProperty("chat", out var chat) &&
                              chat.ValueKind == JsonValueKind.Object
            ? GetString(chat, "id", "ID")
            : null;
        if (!string.IsNullOrEmpty(fromHistoryChat)) return fromHistoryChat;

        return GetString(raw.DialogInfo, "CHAT_ID", "chat_id");
    }

    private static string BuildLinkedEntitiesCsv(JsonElement dialogInfo)
    {
        if (dialogInfo.ValueKind != JsonValueKind.Object) return string.Empty;
        if (!dialogInfo.TryGetProperty("entity_data_2", out var bindings)) return string.Empty;
        return string.Join(";", EntityBindingsParser.Parse(bindings).Select(b => $"{b.Type}:{b.Id}"));
    }

    /// <summary>
    /// Quando o cliente é anônimo (sem binding CRM) e o connector é WhatsApp/Telegram,
    /// o ConnectorChatId do entity_id geralmente carrega o telefone do cliente.
    /// Preenche PhonesCsv se estiver vazio.
    /// </summary>
    private static void EnrichCustomerWithConnectorPhone(CustomerRow? customer, UserCodeInfo code)
    {
        if (customer is null) return;
        if (customer.Type != "anonymous") return;
        if (!string.IsNullOrEmpty(customer.PhonesCsv)) return;
        if (string.IsNullOrEmpty(code.ConnectorChatId)) return;
        if (!code.ConnectorChatId.StartsWith('+') && !char.IsDigit(code.ConnectorChatId[0])) return;
        customer.PhonesCsv = code.ConnectorChatId;
    }
}
