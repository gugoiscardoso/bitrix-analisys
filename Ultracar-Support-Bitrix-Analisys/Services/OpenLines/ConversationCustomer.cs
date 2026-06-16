using System.Text.Json;
using Ultracar_Support_Bitrix_Analisys.Models.OpenLines;
using static Ultracar_Support_Bitrix_Analisys.Services.OpenLines.JsonReadHelpers;

namespace Ultracar_Support_Bitrix_Analisys.Services.OpenLines;

/// <summary>
/// Resolve o cliente da sessão. Prioridade:
///   1) Lead vinculado em entity_data_2 → crm.lead.get
///   2) Contact vinculado em entity_data_2 → crm.contact.get
///   3) Fallback anônimo: encontra user com connector=true nos history users
///      e usa "anon:&lt;externalAuthId&gt;" como CustomerKey.
/// </summary>
public static class ConversationCustomer
{
    public static CustomerRow? Build(
        SessionRawData raw,
        IReadOnlyDictionary<string, JsonElement> crmEntitiesByKey,
        IReadOnlyDictionary<string, JsonElement> historyUsers)
    {
        var bindings = ExtractBindings(raw.DialogInfo);
        var leadBinding = bindings.FirstOrDefault(b => b.Type == "lead");
        var contactBinding = bindings.FirstOrDefault(b => b.Type == "contact");

        if (!string.IsNullOrEmpty(leadBinding.Id) &&
            crmEntitiesByKey.TryGetValue(CrmEntityResolver.CanonicalKey("lead", leadBinding.Id), out var leadJson))
            return BuildFromCrm("lead", leadBinding.Id, leadJson);

        if (!string.IsNullOrEmpty(contactBinding.Id) &&
            crmEntitiesByKey.TryGetValue(CrmEntityResolver.CanonicalKey("contact", contactBinding.Id), out var contactJson))
            return BuildFromCrm("contact", contactBinding.Id, contactJson);

        return BuildAnonymous(historyUsers);
    }

    private static CustomerRow BuildFromCrm(string type, string id, JsonElement entity)
    {
        var first = GetStringOrNull(entity, "NAME", "name") ?? string.Empty;
        var last = GetStringOrNull(entity, "LAST_NAME", "lastName") ?? string.Empty;
        var company = GetStringOrNull(entity, "COMPANY_TITLE", "companyTitle", "TITLE") ?? string.Empty;
        var displayName = $"{first} {last}".Trim();
        if (string.IsNullOrEmpty(displayName)) displayName = company;

        return new CustomerRow
        {
            CustomerKey = CrmEntityResolver.CanonicalKey(type, id),
            Type = type,
            EntityId = id,
            DisplayName = displayName,
            PhonesCsv = ExtractMultifield(entity, "PHONE"),
            EmailsCsv = ExtractMultifield(entity, "EMAIL"),
            CompanyName = company,
            SourceName = GetString(entity, "SOURCE_DESCRIPTION", "SOURCE_ID", "sourceId"),
            CreatedAt = GetDateTimeOrNull(entity, "DATE_CREATE", "dateCreate", "CREATED_TIME")
        };
    }

    private static CustomerRow? BuildAnonymous(IReadOnlyDictionary<string, JsonElement> historyUsers)
    {
        foreach (var (userId, user) in historyUsers)
        {
            if (!GetBool(user, "connector")) continue;
            var externalAuth = GetStringOrNull(user, "externalAuthId", "external_auth_id");
            var key = !string.IsNullOrEmpty(externalAuth) ? $"anon:{externalAuth}" : $"anon:user_{userId}";
            return new CustomerRow
            {
                CustomerKey = key,
                Type = "anonymous",
                EntityId = userId,
                DisplayName = GetString(user, "name", "NAME"),
                PhonesCsv = GetString(user, "phone", "PHONE"),
                EmailsCsv = GetString(user, "email", "EMAIL")
            };
        }
        return null;
    }

    private static string ExtractMultifield(JsonElement entity, string field)
    {
        if (entity.ValueKind != JsonValueKind.Object) return string.Empty;
        if (!entity.TryGetProperty(field, out var arr) || arr.ValueKind != JsonValueKind.Array) return string.Empty;

        var values = new List<string>();
        foreach (var item in arr.EnumerateArray())
        {
            var v = item.ValueKind == JsonValueKind.Object ? GetString(item, "VALUE", "value") : item.GetString() ?? string.Empty;
            if (!string.IsNullOrEmpty(v)) values.Add(v);
        }
        return string.Join(";", values);
    }

    private static List<(string Type, string Id)> ExtractBindings(JsonElement dialogInfo)
    {
        if (dialogInfo.ValueKind != JsonValueKind.Object) return [];
        if (!dialogInfo.TryGetProperty("entity_data_2", out var bindings)) return [];
        return EntityBindingsParser.Parse(bindings).ToList();
    }
}
