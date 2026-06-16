namespace Ultracar_Support_Bitrix_Analisys.Models.OpenLines;

public class CustomerRow
{
    public string CustomerKey { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public string EntityId { get; set; } = string.Empty;
    public string DisplayName { get; set; } = string.Empty;
    public string PhonesCsv { get; set; } = string.Empty;
    public string EmailsCsv { get; set; } = string.Empty;
    public string CompanyName { get; set; } = string.Empty;
    public string SourceName { get; set; } = string.Empty;
    public DateTime? CreatedAt { get; set; }
    public string SessionIdsCsv { get; set; } = string.Empty;
    public int TotalSessions { get; set; }
}
