namespace Ultracar_Support_Bitrix_Analisys.Models.OpenLines;

public class ConversationRow
{
    public string SessionId { get; set; } = string.Empty;
    public string ChatId { get; set; } = string.Empty;
    public string LineId { get; set; } = string.Empty;
    public string Channel { get; set; } = string.Empty;
    public string ChannelRaw { get; set; } = string.Empty;
    public string CustomerKey { get; set; } = string.Empty;
    public string CustomerName { get; set; } = string.Empty;
    public string CustomerPhone { get; set; } = string.Empty;
    public string CustomerEmail { get; set; } = string.Empty;
    public string OperatorId { get; set; } = string.Empty;
    public string OperatorName { get; set; } = string.Empty;
    public DateTime? StartedAt { get; set; }
    public DateTime? EndedAt { get; set; }
    public double? DurationMinutes { get; set; }
    public int TotalMessages { get; set; }
    public int CustomerMessages { get; set; }
    public int OperatorMessages { get; set; }
    public int SystemMessages { get; set; }
    public string LinkedEntitiesCsv { get; set; } = string.Empty;
    public bool HasFiles { get; set; }
    public bool HasVoiceNote { get; set; }
}
