namespace Ultracar_Support_Bitrix_Analisys.Models.OpenLines;

public sealed class AssembledSession
{
    public ConversationRow Conversation { get; init; } = new();
    public List<MessageRow> Messages { get; init; } = [];
    public List<FileRow> Files { get; init; } = [];
    public CustomerRow? Customer { get; init; }
    public OperatorRow? Operator { get; init; }
}
