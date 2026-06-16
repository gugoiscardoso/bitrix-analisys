namespace Ultracar_Support_Bitrix_Analisys.Models.OpenLines;

public class OperatorRow
{
    public string UserId { get; set; } = string.Empty;
    public string FullName { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string Department { get; set; } = string.Empty;
    public int SessionsHandled { get; set; }
    public int MessagesSent { get; set; }
}
