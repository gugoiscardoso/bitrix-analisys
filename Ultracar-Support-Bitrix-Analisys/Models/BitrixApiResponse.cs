using System.Text.Json;
using System.Text.Json.Serialization;

namespace Ultracar_Support_Bitrix_Analisys.Models;

public class BitrixApiResponse<T>
{
    [JsonPropertyName("result")]
    public T? Result { get; set; }

    [JsonPropertyName("total")]
    public int? Total { get; set; }

    [JsonPropertyName("next")]
    public int? Next { get; set; }
}

public class BitrixBatchResponse
{
    [JsonPropertyName("result")]
    public BatchResultContainer? Result { get; set; }
}

public class BatchResultContainer
{
    [JsonPropertyName("result")]
    public JsonElement Result { get; set; }

    [JsonPropertyName("result_error")]
    public JsonElement ResultError { get; set; }

    [JsonPropertyName("result_total")]
    public JsonElement ResultTotal { get; set; }

    [JsonPropertyName("result_next")]
    public JsonElement ResultNext { get; set; }

    public Dictionary<string, JsonElement> GetResults()
    {
        if (Result.ValueKind == JsonValueKind.Object)
            return JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(Result)!;
        return new();
    }

    public Dictionary<string, int> GetNextPages()
    {
        if (ResultNext.ValueKind == JsonValueKind.Object)
            return JsonSerializer.Deserialize<Dictionary<string, int>>(ResultNext)!;
        return new();
    }
}
