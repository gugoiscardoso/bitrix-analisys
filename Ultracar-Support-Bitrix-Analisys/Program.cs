using System.Text.Json;
using Ultracar_Support_Bitrix_Analisys.Configuration;
using Ultracar_Support_Bitrix_Analisys.Services;

// Load and validate settings
var settings = BitrixSettings.Load();
try
{
    settings.Validate();
}
catch (InvalidOperationException ex)
{
    Console.Error.WriteLine($"Configuration error: {ex.Message}");
    return 1;
}

Console.WriteLine($"Webhook: {settings.BaseUrl}");
Console.WriteLine($"WorkGroup ID: {settings.GroupId}");
Console.WriteLine();

// Wire up services
using var httpClient = new HttpClient();
httpClient.DefaultRequestHeaders.Add("Accept", "application/json");

var rateLimitedClient = new RateLimitedHttpClient(httpClient);
var apiClient = new BitrixApiClient(rateLimitedClient, settings);
var batchService = new BitrixBatchService(apiClient);
var collector = new TaskCollectorService(apiClient, batchService);

// Collect all data
var exportData = await collector.CollectAllAsync(settings.GroupId, settings.CreatedFrom);

// Serialize and write to file
var jsonOptions = new JsonSerializerOptions { WriteIndented = true };
var json = JsonSerializer.Serialize(exportData, jsonOptions);

var outputDir = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "output");
Directory.CreateDirectory(outputDir);
var timestamp = DateTime.UtcNow.ToString("yyyyMMdd_HHmmss");
var filePath = Path.Combine(outputDir, $"bitrix_export_{settings.GroupId}_{timestamp}.json");
await File.WriteAllTextAsync(filePath, json);

Console.WriteLine();
Console.WriteLine($"Exported {exportData.Metadata.TotalTasks} tasks to {Path.GetFullPath(filePath)}");
return 0;
