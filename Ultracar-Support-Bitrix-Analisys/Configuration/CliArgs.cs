using System.Globalization;

namespace Ultracar_Support_Bitrix_Analisys.Configuration;

/// <summary>
/// Parser CLI minimalista. Aceita:
///   --mode &lt;tasks|conversations|all|discover&gt;  (default: tasks)
///   --from &lt;yyyy-MM-dd&gt;                         (início da janela de criação)
///   --to &lt;yyyy-MM-dd&gt;                           (fim da janela de criação)
///   --changed-since &lt;yyyy-MM-dd&gt;                (coleta incremental)
///
/// Sobre --changed-since: filtra por data de ALTERAÇÃO em vez de criação. Traz numa
/// consulta só tanto os chamados novos quanto os que mudaram de status desde a última
/// coleta — é o que permite atualizar os que estavam em aberto sem refazer tudo.
/// Quando informado, prevalece sobre --from na listagem de chamados.
/// </summary>
public static class CliArgs
{
    public const string ModeTasks = "tasks";
    public const string ModeConversations = "conversations";
    public const string ModeAll = "all";
    public const string ModeDiscover = "discover";

    private static readonly string[] ValidModes = [ModeTasks, ModeConversations, ModeAll, ModeDiscover];

    public sealed record Options(string Mode, string? From, string? To, string? ChangedSince);

    public static Options Parse(string[] args)
    {
        var mode = ModeTasks;
        string? from = null, to = null, changedSince = null;

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
                case "--to" when i + 1 < args.Length:
                    to = args[++i];
                    break;
                case "--changed-since" when i + 1 < args.Length:
                    changedSince = args[++i];
                    break;
            }
        }

        if (!ValidModes.Contains(mode))
            throw new ArgumentException(
                $"Invalid --mode '{mode}'. Valid options: {string.Join(", ", ValidModes)}.");

        // Formato exato e cultura invariante: sem isso "01-05-2026" seria aceito em pt-BR
        // e viraria uma janela silenciosamente errada.
        foreach (var (nome, valor) in new[] { ("--from", from), ("--to", to), ("--changed-since", changedSince) })
            if (valor is not null && !DateOnly.TryParseExact(valor, "yyyy-MM-dd",
                    CultureInfo.InvariantCulture, DateTimeStyles.None, out _))
                throw new ArgumentException($"Invalid date for {nome}: '{valor}'. Expected yyyy-MM-dd.");

        if (from is not null && to is not null && string.CompareOrdinal(from, to) > 0)
            throw new ArgumentException($"--from ({from}) is after --to ({to}).");

        return new Options(mode, from, to, changedSince);
    }
}
