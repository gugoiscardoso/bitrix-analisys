using System.Text.Json;
using Ultracar_Support_Bitrix_Analisys.Models;

namespace Ultracar_Support_Bitrix_Analisys.Services;

public class TaskCollectorService
{
    private readonly BitrixApiClient _apiClient;
    private readonly BitrixBatchService _batchService;
    private const int TasksPerBatch = 8; // 8 * 6 endpoints = 48 commands (limit is 50)

    public TaskCollectorService(BitrixApiClient apiClient, BitrixBatchService batchService)
    {
        _apiClient = apiClient;
        _batchService = batchService;
    }

    public async Task<ExportRoot> CollectAllAsync(string groupId, string? createdFrom = null, CancellationToken ct = default)
    {
        Console.WriteLine($"Fetching tasks for WorkGroup {groupId}...");
        if (createdFrom != null)
            Console.WriteLine($"Filtering tasks created from: {createdFrom}");

        // Step 1: Paginate all task IDs
        var taskIds = new List<string>();
        var filter = new Dictionary<string, object> { ["GROUP_ID"] = groupId };
        if (createdFrom != null)
            filter[">=CREATED_DATE"] = createdFrom;

        var listParams = new Dictionary<string, object>
        {
            ["filter"] = filter,
            ["select"] = new[] { "ID", "TITLE" }
        };

        await foreach (var task in _apiClient.PaginateAsync("tasks.task.list", listParams, "tasks", ct))
        {
            var id = task.TryGetProperty("id", out var idProp)
                ? idProp.GetString()!
                : task.GetProperty("ID").GetString()!;

            taskIds.Add(id);

            if (taskIds.Count % 50 == 0)
                Console.WriteLine($"  Listed {taskIds.Count} tasks...");
        }

        Console.WriteLine($"Found {taskIds.Count} tasks. Fetching details...");

        // Step 2: Batch-fetch details for all tasks
        var allTaskData = new List<TaskData>();
        var chunks = taskIds.Chunk(TasksPerBatch).ToList();
        var batchNumber = 0;

        foreach (var chunk in chunks)
        {
            batchNumber++;
            var firstId = chunk.First();
            var lastId = chunk.Last();
            Console.WriteLine($"  Batch {batchNumber}/{chunks.Count}: tasks {firstId}..{lastId}");

            var commands = BuildBatchCommands(chunk);
            var (results, nextPages) = await _batchService.ExecuteAsync(commands, ct);

            // Handle pagination for sub-endpoints with >50 items
            if (nextPages.Count > 0)
            {
                Console.WriteLine($"    Fetching additional pages for {nextPages.Count} sub-commands...");
                await _batchService.FetchRemainingPagesAsync(commands, nextPages, results, ct);
            }

            // Assemble TaskData for each task in this chunk
            foreach (var taskId in chunk)
            {
                var taskData = AssembleTaskData(taskId, results);
                allTaskData.Add(taskData);
            }
        }

        return new ExportRoot
        {
            Metadata = new ExportMetadata
            {
                GroupId = groupId,
                ExportedAt = DateTime.UtcNow,
                TotalTasks = allTaskData.Count
            },
            Tasks = allTaskData
        };
    }

    private static Dictionary<string, string> BuildBatchCommands(string[] taskIds)
    {
        var commands = new Dictionary<string, string>();

        foreach (var id in taskIds)
        {
            commands[$"task_{id}"] = $"tasks.task.get?taskId={id}";
            commands[$"comments_{id}"] = $"task.commentitem.getlist?TASKID={id}&ORDER[ID]=ASC";
            commands[$"history_{id}"] = $"tasks.task.history.list?taskId={id}";
            commands[$"checklist_{id}"] = $"task.checklistitem.getlist?TASKID={id}";
            commands[$"elapsed_{id}"] = $"task.elapseditem.getlist?TASKID={id}";
            commands[$"results_{id}"] = $"tasks.task.result.list?taskId={id}";
        }

        return commands;
    }

    private static TaskData AssembleTaskData(string taskId, Dictionary<string, JsonElement> results)
    {
        var taskData = new TaskData();

        // Task details — tasks.task.get returns { "task": { ... } }
        if (results.TryGetValue($"task_{taskId}", out var taskResult))
        {
            if (taskResult.ValueKind == JsonValueKind.Object &&
                taskResult.TryGetProperty("task", out var taskObj))
                taskData.Task = taskObj.Clone();
            else
                taskData.Task = taskResult.Clone();
        }

        // Comments
        if (results.TryGetValue($"comments_{taskId}", out var comments))
            taskData.Comments = ExtractArray(comments);

        // History — tasks.task.history.list returns { "list": [...] }
        if (results.TryGetValue($"history_{taskId}", out var history))
        {
            if (history.ValueKind == JsonValueKind.Object &&
                history.TryGetProperty("list", out var historyList))
                taskData.History = ExtractArray(historyList);
            else
                taskData.History = ExtractArray(history);
        }

        // Checklist
        if (results.TryGetValue($"checklist_{taskId}", out var checklist))
            taskData.Checklist = ExtractArray(checklist);

        // Elapsed items
        if (results.TryGetValue($"elapsed_{taskId}", out var elapsed))
            taskData.ElapsedItems = ExtractArray(elapsed);

        // Results
        if (results.TryGetValue($"results_{taskId}", out var taskResults))
            taskData.Results = ExtractArray(taskResults);

        return taskData;
    }

    private static List<JsonElement> ExtractArray(JsonElement element)
    {
        if (element.ValueKind == JsonValueKind.Array)
            return element.EnumerateArray().Select(e => e.Clone()).ToList();

        // Some endpoints return an object wrapping the array
        if (element.ValueKind == JsonValueKind.Object)
        {
            foreach (var prop in element.EnumerateObject())
            {
                if (prop.Value.ValueKind == JsonValueKind.Array)
                    return prop.Value.EnumerateArray().Select(e => e.Clone()).ToList();
            }
        }

        return [];
    }
}
