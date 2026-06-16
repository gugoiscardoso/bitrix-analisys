namespace Ultracar_Support_Bitrix_Analisys.Configuration;

/// <summary>
/// Parser CLI minimalista. Aceita:
///   --mode &lt;tasks|conversations|all|discover&gt;  (default: tasks)
///   --from &lt;yyyy-MM-dd&gt;                         (override de CreatedFrom + OpenLinesCreatedFrom)
/// </summary>
public static class CliArgs
{
    public const string ModeTasks = "tasks";
    public const string ModeConversations = "conversations";
    public const string ModeAll = "all";
    public const string ModeDiscover = "discover";

    private static readonly string[] ValidModes = [ModeTasks, ModeConversations, ModeAll, ModeDiscover];

    public static (string Mode, string? OverrideFrom) Parse(string[] args)
    {
        var mode = ModeTasks;
        string? from = null;

        for (var i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "--mode" when i + 1 < args.Length:
                    mode = args[++i].ToLowerInvariant();
                    break;
                case "--from" when i + 1 < args.Length:
                    from = args[++i];
                    break;
            }
        }

        if (!ValidModes.Contains(mode))
            throw new ArgumentException(
                $"Invalid --mode '{mode}'. Valid options: {string.Join(", ", ValidModes)}.");

        return (mode, from);
    }
}
