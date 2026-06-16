using Ultracar_Support_Bitrix_Analisys.Configuration;

namespace Ultracar_Support_Bitrix_Analisys.Models.OpenLines;

public class ConversationExport
{
    public ConversationMetadata Metadata { get; internal set; } = new();
    public List<ConversationRow> Conversations { get; internal set; } = [];
    public List<MessageRow> Messages { get; internal set; } = [];
    public List<CustomerRow> Customers { get; internal set; } = [];
    public List<OperatorRow> Operators { get; internal set; } = [];
    public List<FileRow> Files { get; internal set; } = [];

    public const string ToolVersion = "1.0.0";

    public static ConversationExport Build(IEnumerable<AssembledSession> sessions, BitrixSettings settings)
    {
        var export = new ConversationExport();
        var customers = new Dictionary<string, CustomerRow>();
        var operators = new Dictionary<string, OperatorRow>();

        foreach (var session in sessions)
        {
            export.Conversations.Add(session.Conversation);
            export.Messages.AddRange(session.Messages);
            export.Files.AddRange(session.Files);
            MergeCustomer(customers, session);
            MergeOperator(operators, session);
        }

        export.Customers = [.. customers.Values];
        export.Operators = [.. operators.Values];
        export.Metadata = BuildMetadata(export, settings);
        return export;
    }

    private static void MergeCustomer(Dictionary<string, CustomerRow> bucket, AssembledSession session)
    {
        if (session.Customer is null || string.IsNullOrEmpty(session.Customer.CustomerKey))
            return;

        if (bucket.TryGetValue(session.Customer.CustomerKey, out var existing))
        {
            existing.TotalSessions++;
            existing.SessionIdsCsv = AppendCsv(existing.SessionIdsCsv, session.Conversation.SessionId);
        }
        else
        {
            session.Customer.TotalSessions = 1;
            session.Customer.SessionIdsCsv = session.Conversation.SessionId;
            bucket[session.Customer.CustomerKey] = session.Customer;
        }
    }

    private static void MergeOperator(Dictionary<string, OperatorRow> bucket, AssembledSession session)
    {
        if (session.Operator is null || string.IsNullOrEmpty(session.Operator.UserId))
            return;

        if (bucket.TryGetValue(session.Operator.UserId, out var existing))
        {
            existing.SessionsHandled++;
            existing.MessagesSent += session.Conversation.OperatorMessages;
        }
        else
        {
            session.Operator.SessionsHandled = 1;
            session.Operator.MessagesSent = session.Conversation.OperatorMessages;
            bucket[session.Operator.UserId] = session.Operator;
        }
    }

    private static ConversationMetadata BuildMetadata(ConversationExport export, BitrixSettings settings) => new()
    {
        ExportedAt = DateTime.UtcNow,
        CreatedFromFilter = settings.EffectiveOpenLinesCreatedFrom ?? string.Empty,
        TotalConversations = export.Conversations.Count,
        TotalMessages = export.Messages.Count,
        TotalCustomers = export.Customers.Count,
        TotalOperators = export.Operators.Count,
        TotalFiles = export.Files.Count,
        ToolVersion = ToolVersion,
        WebhookHost = settings.WebhookHost,
        Notes = "URLs de download podem expirar; baixar mídia em ate 24h. Historico de edicoes/delecoes nao e exposto pela REST do Bitrix."
    };

    private static string AppendCsv(string current, string value) =>
        string.IsNullOrEmpty(current) ? value : current + ";" + value;
}
