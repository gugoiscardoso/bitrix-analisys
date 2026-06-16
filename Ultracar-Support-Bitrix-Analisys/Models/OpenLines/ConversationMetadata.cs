namespace Ultracar_Support_Bitrix_Analisys.Models.OpenLines;

public class ConversationMetadata
{
    public DateTime ExportedAt { get; set; }
    public string CreatedFromFilter { get; set; } = string.Empty;
    public int TotalConversations { get; set; }
    public int TotalMessages { get; set; }
    public int TotalCustomers { get; set; }
    public int TotalOperators { get; set; }
    public int TotalFiles { get; set; }
    public string ToolVersion { get; set; } = string.Empty;
    public string WebhookHost { get; set; } = string.Empty;
    public string Notes { get; set; } = string.Empty;
}
