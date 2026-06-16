namespace Ultracar_Support_Bitrix_Analisys.Models.OpenLines;

public class FileRow
{
    public string FileId { get; set; } = string.Empty;
    public string MessageId { get; set; } = string.Empty;
    public string SessionId { get; set; } = string.Empty;
    public string FileName { get; set; } = string.Empty;
    public string MimeType { get; set; } = string.Empty;
    public long? SizeBytes { get; set; }
    public string DownloadUrl { get; set; } = string.Empty;
    public bool IsVoiceNote { get; set; }
}
