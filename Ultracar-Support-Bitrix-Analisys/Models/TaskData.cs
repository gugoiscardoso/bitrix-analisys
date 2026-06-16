using System.Text.Json;
using System.Text.Json.Serialization;

namespace Ultracar_Support_Bitrix_Analisys.Models;

public class TaskData
{
    [JsonPropertyName("task")]
    public JsonElement Task { get; set; }

    [JsonPropertyName("comments")]
    public List<JsonElement> Comments { get; set; } = [];

    [JsonPropertyName("history")]
    public List<JsonElement> History { get; set; } = [];

    [JsonPropertyName("checklist")]
    public List<JsonElement> Checklist { get; set; } = [];

    [JsonPropertyName("elapsedItems")]
    public List<JsonElement> ElapsedItems { get; set; } = [];

    [JsonPropertyName("results")]
    public List<JsonElement> Results { get; set; } = [];
}

public class ExportRoot
{
    [JsonPropertyName("metadata")]
    public ExportMetadata Metadata { get; set; } = new();

    [JsonPropertyName("tasks")]
    public List<TaskData> Tasks { get; set; } = [];
}

public class ExportMetadata
{
    [JsonPropertyName("groupId")]
    public string GroupId { get; set; } = string.Empty;

    [JsonPropertyName("exportedAt")]
    public DateTime ExportedAt { get; set; }

    [JsonPropertyName("totalTasks")]
    public int TotalTasks { get; set; }
}
