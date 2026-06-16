using System.Text.Json;
using Ultracar_Support_Bitrix_Analisys.Configuration;
using Ultracar_Support_Bitrix_Analisys.Models.OpenLines;
using Ultracar_Support_Bitrix_Analisys.Services;
using Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

(string mode, string? overrideFrom) parsedArgs;
try
{
    parsedArgs = CliArgs.Parse(args);
}
catch (ArgumentException ex)
{
    Console.Error.WriteLine($"CLI error: {ex.Message}");
    return 1;
}

var settings = BitrixSettings.Load();
if (parsedArgs.overrideFrom is not null)
{
    settings.CreatedFrom = parsedArgs.overrideFrom;
    settings.OpenLinesCreatedFrom = parsedArgs.overrideFrom;
}

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
Console.WriteLine($"Mode: {parsedArgs.mode}");

using var httpClient = new HttpClient();
httpClient.DefaultRequestHeaders.Add("Accept", "application/json");
var rateLimitedClient = new RateLimitedHttpClient(httpClient);
var apiClient = new BitrixApiClient(rateLimitedClient, settings);
var batchService = new BitrixBatchService(apiClient);

return parsedArgs.mode switch
{
    CliArgs.ModeDiscover => await RunDiscoveryAsync(),
    CliArgs.ModeConversations => await RunConversationsAsync(),
    CliArgs.ModeAll => await RunAllAsync(),
    _ => await RunTasksAsync()
};

async Task<int> RunTasksAsync()
{
    Console.WriteLine($"WorkGroup ID: {settings.GroupId}");
    Console.WriteLine();

    var collector = new TaskCollectorService(apiClient, batchService);
    var exportData = await collector.CollectAllAsync(settings.GroupId, settings.CreatedFrom);

    var jsonOptions = new JsonSerializerOptions { WriteIndented = true };
    var json = JsonSerializer.Serialize(exportData, jsonOptions);

    var outputDir = ResolveOutputDir();
    var timestamp = DateTime.UtcNow.ToString("yyyyMMdd_HHmmss");
    var filePath = Path.Combine(outputDir, $"bitrix_export_{settings.GroupId}_{timestamp}.json");
    await File.WriteAllTextAsync(filePath, json);

    Console.WriteLine();
    Console.WriteLine($"Exported {exportData.Metadata.TotalTasks} tasks to {Path.GetFullPath(filePath)}");
    return 0;
}

async Task<int> RunConversationsAsync()
{
    Console.WriteLine($"OpenLines CreatedFrom: {settings.EffectiveOpenLinesCreatedFrom ?? "(none)"}");
    Console.WriteLine();

    var enumerator = new OpenLinesSessionEnumerator(apiClient);
    var crmResolver = new CrmEntityResolver(batchService);
    var userResolver = new UserResolver(batchService);
    var collector = new OpenLinesConversationCollector(batchService, enumerator, crmResolver, userResolver);

    var collected = await collector.CollectAllAsync(settings.EffectiveOpenLinesCreatedFrom);
    if (collected.Sessions.Count == 0)
    {
        Console.WriteLine("No sessions found. Nothing to export.");
        return 0;
    }

    var assembler = new ConversationAssembler();
    var assembled = collected.Sessions
        .Select(s => assembler.AssembleSession(s, collected.CrmEntitiesByKey, collected.UsersById))
        .ToList();

    var export = ConversationExport.Build(assembled, settings);
    var exporter = new ConversationExcelExporter();

    var outputDir = ResolveOutputDir();
    var timestamp = DateTime.UtcNow.ToString("yyyyMMdd_HHmmss");
    var filePath = Path.Combine(outputDir, $"conversations_export_{timestamp}.xlsx");
    await exporter.ExportAsync(export, filePath);

    Console.WriteLine();
    Console.WriteLine($"Exported {export.Metadata.TotalConversations} conversations to {Path.GetFullPath(filePath)}");
    return 0;
}

async Task<int> RunAllAsync()
{
    var tasksResult = await RunTasksAsync();
    if (tasksResult != 0) return tasksResult;
    Console.WriteLine();
    return await RunConversationsAsync();
}

async Task<int> RunDiscoveryAsync()
{
    Console.WriteLine();
    var discovery = new OpenLinesDiscoveryService(apiClient, settings);
    await discovery.RunAsync();
    return 0;
}

static string ResolveOutputDir()
{
    var outputDir = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "output");
    Directory.CreateDirectory(outputDir);
    return outputDir;
}
