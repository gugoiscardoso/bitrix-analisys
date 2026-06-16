namespace Ultracar_Support_Bitrix_Analisys.Models.OpenLines;

public class MessageRow
{
    public string MessageId { get; set; } = string.Empty;
    public string SessionId { get; set; } = string.Empty;
    public DateTime? Timestamp { get; set; }
    public string AuthorId { get; set; } = string.Empty;
    public string AuthorType { get; set; } = string.Empty;
    public string AuthorName { get; set; } = string.Empty;
    public string TextContent { get; set; } = string.Empty;
    public string MessageType { get; set; } = string.Empty;
    public bool HasFiles { get; set; }
    public int FilesCount { get; set; }
}
