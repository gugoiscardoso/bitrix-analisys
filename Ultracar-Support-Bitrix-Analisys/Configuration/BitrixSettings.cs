using System.Text.Json;

namespace Ultracar_Support_Bitrix_Analisys.Configuration;

public class BitrixSettings
{
    public string WebhookUrl { get; set; } = string.Empty;
    public string GroupId { get; set; } = string.Empty;
    public string? CreatedFrom { get; set; }

    public string BaseUrl => WebhookUrl.TrimEnd('/') + "/";

    public static BitrixSettings Load()
    {
        var settings = new BitrixSettings();

        var configPath = Path.Combine(AppContext.BaseDirectory, "appsettings.json");
        if (File.Exists(configPath))
        {
            var json = File.ReadAllText(configPath);
            using var doc = JsonDocument.Parse(json);
            if (doc.RootElement.TryGetProperty("Bitrix", out var bitrixSection))
            {
                settings.WebhookUrl = bitrixSection.GetProperty("WebhookUrl").GetString() ?? string.Empty;
                settings.GroupId = bitrixSection.GetProperty("GroupId").GetString() ?? string.Empty;
                if (bitrixSection.TryGetProperty("CreatedFrom", out var createdFrom))
                    settings.CreatedFrom = createdFrom.GetString();
            }
        }

        settings.WebhookUrl = Environment.GetEnvironmentVariable("BITRIX_WEBHOOK_URL") ?? settings.WebhookUrl;
        settings.GroupId = Environment.GetEnvironmentVariable("BITRIX_GROUP_ID") ?? settings.GroupId;
        settings.CreatedFrom = Environment.GetEnvironmentVariable("BITRIX_CREATED_FROM") ?? settings.CreatedFrom;

        return settings;
    }

    public void Validate()
    {
        var missing = new List<string>();
        if (string.IsNullOrWhiteSpace(WebhookUrl)) missing.Add("WebhookUrl");
        if (string.IsNullOrWhiteSpace(GroupId)) missing.Add("GroupId");

        if (missing.Count > 0)
            throw new InvalidOperationException(
                $"Missing Bitrix settings: {string.Join(", ", missing)}. " +
                "Set them in appsettings.json or via environment variables (BITRIX_WEBHOOK_URL, BITRIX_GROUP_ID).");
    }
}
