using System.Text.Json;
using Ultracar_Support_Bitrix_Analisys.Configuration;
using Ultracar_Support_Bitrix_Analisys.Models.OpenLines;
using Ultracar_Support_Bitrix_Analisys.Services;
using Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

CliArgs.Options opts;
try
{
    opts = CliArgs.Parse(args);
}
catch (ArgumentException ex)
{
    Console.Error.WriteLine($"CLI error: {ex.Message}");
    return 1;
}

var settings = BitrixSettings.Load();
if (opts.From is not null)
{
    settings.CreatedFrom = opts.From;
    settings.OpenLinesCreatedFrom = opts.From;
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
Console.WriteLine($"Mode: {opts.Mode}");

using var httpClient = new HttpClient();
httpClient.DefaultRequestHeaders.Add("Accept", "application/json");
var rateLimitedClient = new RateLimitedHttpClient(httpClient);
var apiClient = new BitrixApiClient(rateLimitedClient, settings);
var batchService = new BitrixBatchService(apiClient);

return opts.Mode switch
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
    var exportData = await collector.CollectAllAsync(
        settings.GroupId, settings.CreatedFrom, opts.To, opts.ChangedSince);

    var jsonOptions = new JsonSerializerOptions { WriteIndented = true };
    var json = JsonSerializer.Serialize(exportData, jsonOptions);

    var outputDir = ResolveOutputDir();
    var timestamp = DateTime.UtcNow.ToString("yyyyMMdd_HHmmss");
    var filePath = Path.Combine(outputDir, $"bitrix_export_{settings.GroupId}_{timestamp}.json");
    await File.WriteAllTextAsync(filePath, json);

    Console.WriteLine();
    Console.WriteLine($"Exported {exportData.Metadata.TotalTasks} tasks to {Path.GetFullPath(filePath)}");
    await RegistrarColetaAsync("chamados", filePath, exportData.Metadata.TotalTasks, opts);
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

    var collected = await collector.CollectAllAsync(settings.EffectiveOpenLinesCreatedFrom, opts.To);
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
    await RegistrarColetaAsync("conversas", filePath, export.Metadata.TotalConversations, opts);
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
    // data/raw é cache regenerável; o pipeline lê daqui e escreve o store em data/store.
    var outputDir = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "raw");
    Directory.CreateDirectory(outputDir);
    return outputDir;
}

/// <summary>
/// Registra a coleta em data/store/coleta.json. É o que permite ao modo incremental
/// saber a partir de quando buscar na próxima execução.
/// </summary>
static async Task RegistrarColetaAsync(string modo, string arquivo, int registros, CliArgs.Options opts)
{
    var storeDir = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "store");
    Directory.CreateDirectory(storeDir);
    var caminho = Path.Combine(storeDir, "coleta.json");

    var raiz = new Dictionary<string, JsonElement>();
    if (File.Exists(caminho))
    {
        using var doc = JsonDocument.Parse(await File.ReadAllTextAsync(caminho));
        foreach (var prop in doc.RootElement.EnumerateObject())
            raiz[prop.Name] = prop.Value.Clone();
    }

    var entrada = new
    {
        em = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
        arquivo = Path.GetFileName(arquivo),
        registros,
        from = opts.From,
        to = opts.To,
        changedSince = opts.ChangedSince
    };
    raiz[modo] = JsonSerializer.SerializeToElement(entrada);

    await File.WriteAllTextAsync(caminho,
        JsonSerializer.Serialize(raiz, new JsonSerializerOptions { WriteIndented = true }));
    Console.WriteLine($"Coleta registrada em {Path.GetFullPath(caminho)}");
}
