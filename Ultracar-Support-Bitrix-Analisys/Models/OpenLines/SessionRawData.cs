using System.Text.Json;

namespace Ultracar_Support_Bitrix_Analisys.Models.OpenLines;

public class SessionRawData
{
    public string SessionId { get; init; } = string.Empty;
    public JsonElement Activity { get; set; }
    public JsonElement SessionHistory { get; set; }
    public JsonElement DialogInfo { get; set; }
    public List<JsonElement> MessagesExtended { get; set; } = [];
}
