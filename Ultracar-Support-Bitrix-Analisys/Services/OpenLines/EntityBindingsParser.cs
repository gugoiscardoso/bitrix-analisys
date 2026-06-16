using System.Text.Json;
using static Ultracar_Support_Bitrix_Analisys.Services.OpenLines.JsonReadHelpers;

namespace Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

/// <summary>
/// Parseia entity_data_2 do imopenlines.dialog.get em qualquer formato observado:
///   - Object: { "1": id, "3": id, "LEAD": id, ... }
///   - String pipe-delimited: "LEAD|0|COMPANY|0|CONTACT|60657|DEAL|60711"
/// Retorna pares (type, id) normalizados em lower-case (lead/contact/company/deal),
/// já filtrando ids zerados/vazios.
/// </summary>
public static class EntityBindingsParser
{
    public static IEnumerable<(string Type, string Id)> Parse(JsonElement entityData2)
    {
        return entityData2.ValueKind switch
        {
            JsonValueKind.Object => FromObject(entityData2),
            JsonValueKind.String => FromString(entityData2.GetString() ?? string.Empty),
            _ => []
        };
    }

    private static IEnumerable<(string, string)> FromObject(JsonElement obj)
    {
        foreach (var prop in obj.EnumerateObject())
        {
            var type = NormalizeType(prop.Name);
            if (type is null) continue;
            var id = ExtractId(prop.Value);
            if (string.IsNullOrEmpty(id) || id == "0") continue;
            yield return (type, id);
        }
    }

    private static IEnumerable<(string, string)> FromString(string raw)
    {
        if (string.IsNullOrWhiteSpace(raw)) yield break;
        var parts = raw.Split('|');
        for (var i = 0; i + 1 < parts.Length; i += 2)
        {
            var type = NormalizeType(parts[i]);
            if (type is null) continue;
            var id = parts[i + 1];
            if (string.IsNullOrEmpty(id) || id == "0") continue;
            yield return (type, id);
        }
    }

    public static string? NormalizeType(string key) => key.ToUpperInvariant() switch
    {
        "1" or "LEAD" or "CRM_LEAD" => "lead",
        "2" or "DEAL" or "CRM_DEAL" => "deal",
        "3" or "CONTACT" or "CRM_CONTACT" => "contact",
        "4" or "COMPANY" or "CRM_COMPANY" => "company",
        _ => null
    };

    private static string ExtractId(JsonElement value) => value.ValueKind switch
    {
        JsonValueKind.String => value.GetString() ?? string.Empty,
        JsonValueKind.Number => value.GetRawText(),
        JsonValueKind.Object => GetString(value, "id", "ID", "entity_id", "ENTITY_ID"),
        _ => string.Empty
    };
}
