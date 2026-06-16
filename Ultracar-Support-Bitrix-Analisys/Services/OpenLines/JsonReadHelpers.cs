using System.Globalization;
using System.Text.Json;

namespace Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

/// <summary>
/// Helpers tolerantes para leitura de JsonElement do Bitrix (que mistura
/// strings, números e nulls dependendo do endpoint/versão).
/// </summary>
public static class JsonReadHelpers
{
    public static string? GetStringOrNull(JsonElement el, params string[] propNames)
    {
        if (el.ValueKind != JsonValueKind.Object) return null;
        foreach (var name in propNames)
        {
            if (!el.TryGetProperty(name, out var prop)) continue;
            return prop.ValueKind switch
            {
                JsonValueKind.String => prop.GetString(),
                JsonValueKind.Number => prop.GetRawText(),
                JsonValueKind.True or JsonValueKind.False => prop.GetRawText(),
                _ => null
            };
        }
        return null;
    }

    public static string GetString(JsonElement el, params string[] propNames) =>
        GetStringOrNull(el, propNames) ?? string.Empty;

    public static bool GetBool(JsonElement el, params string[] propNames)
    {
        if (el.ValueKind != JsonValueKind.Object) return false;
        foreach (var name in propNames)
        {
            if (!el.TryGetProperty(name, out var prop)) continue;
            return prop.ValueKind switch
            {
                JsonValueKind.True => true,
                JsonValueKind.False => false,
                JsonValueKind.String => bool.TryParse(prop.GetString(), out var b) && b,
                JsonValueKind.Number => prop.TryGetInt32(out var n) && n != 0,
                _ => false
            };
        }
        return false;
    }

    public static long? GetInt64OrNull(JsonElement el, params string[] propNames)
    {
        if (el.ValueKind != JsonValueKind.Object) return null;
        foreach (var name in propNames)
        {
            if (!el.TryGetProperty(name, out var prop)) continue;
            return prop.ValueKind switch
            {
                JsonValueKind.Number when prop.TryGetInt64(out var n) => n,
                JsonValueKind.String when long.TryParse(prop.GetString(), out var n) => n,
                _ => null
            };
        }
        return null;
    }

    public static DateTime? GetDateTimeOrNull(JsonElement el, params string[] propNames)
    {
        var raw = GetStringOrNull(el, propNames);
        if (string.IsNullOrEmpty(raw)) return null;

        if (DateTime.TryParse(raw, CultureInfo.InvariantCulture,
                DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal, out var dt))
            return dt;

        if (long.TryParse(raw, NumberStyles.Integer, CultureInfo.InvariantCulture, out var unix))
        {
            try { return DateTimeOffset.FromUnixTimeSeconds(unix).UtcDateTime; }
            catch { return null; }
        }
        return null;
    }

    public static int CountArray(JsonElement el, string propName)
    {
        if (el.ValueKind != JsonValueKind.Object) return 0;
        if (!el.TryGetProperty(propName, out var prop)) return 0;
        return prop.ValueKind == JsonValueKind.Array ? prop.GetArrayLength() : 0;
    }
}
