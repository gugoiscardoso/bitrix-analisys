using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using Ultracar_Support_Bitrix_Analisys.Configuration;
using Ultracar_Support_Bitrix_Analisys.Models;

namespace Ultracar_Support_Bitrix_Analisys.Services;

public class BitrixApiClient
{
    private readonly RateLimitedHttpClient _httpClient;
    private readonly string _baseUrl;
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };

    public BitrixApiClient(RateLimitedHttpClient httpClient, BitrixSettings settings)
    {
        _httpClient = httpClient;
        _baseUrl = settings.BaseUrl;
    }

    public async Task<BitrixApiResponse<JsonElement>> PostAsync(
        string method,
        Dictionary<string, object> parameters,
        CancellationToken ct = default)
    {
        var url = _baseUrl + method;
        var json = JsonSerializer.Serialize(parameters);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await _httpClient.PostAsync(url, content, ct);
        var responseJson = await response.Content.ReadAsStringAsync(ct);

        return JsonSerializer.Deserialize<BitrixApiResponse<JsonElement>>(responseJson, JsonOptions)
               ?? throw new InvalidOperationException($"Failed to deserialize response from {method}");
    }

    public async Task<BitrixBatchResponse> PostBatchAsync(
        Dictionary<string, string> commands,
        CancellationToken ct = default)
    {
        var url = _baseUrl + "batch";
        var payload = new Dictionary<string, object>
        {
            ["halt"] = 0,
            ["cmd"] = commands
        };
        var json = JsonSerializer.Serialize(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await _httpClient.PostAsync(url, content, ct);
        var responseJson = await response.Content.ReadAsStringAsync(ct);

        return JsonSerializer.Deserialize<BitrixBatchResponse>(responseJson, JsonOptions)
               ?? throw new InvalidOperationException("Failed to deserialize batch response");
    }

    /// <summary>
    /// Fast pagination using ID > lastId trick with start=-1 to skip COUNT.
    /// resultProperty is the property name inside "result" that contains the array (e.g. "tasks").
    /// If null, "result" itself is the array.
    /// </summary>
    public async IAsyncEnumerable<JsonElement> PaginateAsync(
        string method,
        Dictionary<string, object> baseParams,
        string? resultProperty = null,
        [EnumeratorCancellation] CancellationToken ct = default)
    {
        var lastId = 0L;
        var hasMore = true;

        while (hasMore)
        {
            var parameters = new Dictionary<string, object>(baseParams);

            if (!parameters.ContainsKey("order"))
                parameters["order"] = new Dictionary<string, string> { ["ID"] = "asc" };

            parameters["start"] = -1;

            if (lastId > 0)
            {
                var filter = parameters.TryGetValue("filter", out var existingFilter)
                    ? JsonSerializer.Deserialize<Dictionary<string, object>>(
                        JsonSerializer.Serialize(existingFilter))!
                    : new Dictionary<string, object>();

                filter[">ID"] = lastId;
                parameters["filter"] = filter;
            }

            var response = await PostAsync(method, parameters, ct);

            if (response.Result.ValueKind == JsonValueKind.Undefined ||
                response.Result.ValueKind == JsonValueKind.Null)
                break;

            JsonElement items;
            if (resultProperty != null)
            {
                if (!response.Result.TryGetProperty(resultProperty, out items))
                    break;
            }
            else
            {
                items = response.Result;
            }

            if (items.ValueKind != JsonValueKind.Array || items.GetArrayLength() == 0)
                break;

            foreach (var item in items.EnumerateArray())
            {
                yield return item;

                if (item.TryGetProperty("id", out var idProp) ||
                    item.TryGetProperty("ID", out idProp))
                {
                    if (idProp.ValueKind == JsonValueKind.String)
                        lastId = long.Parse(idProp.GetString()!);
                    else
                        lastId = idProp.GetInt64();
                }
            }

            if (items.GetArrayLength() < 50)
                hasMore = false;
        }
    }
}
