using ClosedXML.Excel;
using Ultracar_Support_Bitrix_Analisys.Models.OpenLines;

namespace Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

/// <summary>
/// Exporta ConversationExport para um arquivo XLSX multi-aba. Usa ClosedXML
/// InsertTable que infere colunas via reflection sobre os POCOs.
/// </summary>
public class ConversationExcelExporter
{
    private const double MaxColumnWidth = 80;

    public Task ExportAsync(ConversationExport export, string outputPath, CancellationToken ct = default)
    {
        Console.WriteLine($"[Excel] Building workbook with {export.Conversations.Count} conversations, " +
                          $"{export.Messages.Count} messages, {export.Customers.Count} customers, " +
                          $"{export.Operators.Count} operators, {export.Files.Count} files...");

        using var workbook = new XLWorkbook();
        AddRowsSheet(workbook, "Conversations", export.Conversations);
        AddRowsSheet(workbook, "Messages", export.Messages);
        AddRowsSheet(workbook, "Customers", export.Customers);
        AddRowsSheet(workbook, "Operators", export.Operators);
        AddRowsSheet(workbook, "Files", export.Files);
        AddRowsSheet(workbook, "Metadata", new[] { export.Metadata });

        ct.ThrowIfCancellationRequested();
        Directory.CreateDirectory(Path.GetDirectoryName(outputPath)!);
        workbook.SaveAs(outputPath);
        Console.WriteLine($"[Excel] Saved {Path.GetFullPath(outputPath)}");
        return Task.CompletedTask;
    }

    private static void AddRowsSheet<T>(XLWorkbook workbook, string sheetName, IEnumerable<T> rows)
    {
        var sheet = workbook.Worksheets.Add(sheetName);
        var list = rows as IList<T> ?? rows.ToList();

        if (list.Count == 0)
        {
            sheet.Cell(1, 1).Value = "(no data)";
            return;
        }

        var table = sheet.Cell(1, 1).InsertTable(list, $"{sheetName}Table", createTable: true);
        table.Theme = XLTableTheme.TableStyleMedium2;

        sheet.Columns().AdjustToContents(1, list.Count + 1, minWidth: 8, maxWidth: MaxColumnWidth);
        sheet.SheetView.FreezeRows(1);
    }
}
