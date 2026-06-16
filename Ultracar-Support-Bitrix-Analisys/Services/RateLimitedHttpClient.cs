using System.Net;

namespace Ultracar_Support_Bitrix_Analisys.Services;

public class RateLimitedHttpClient
{
    private readonly HttpClient _httpClient;
    private readonly SemaphoreSlim _semaphore = new(1, 1);
    private DateTime _lastRequestTime = DateTime.MinValue;
    private static readonly TimeSpan MinInterval = TimeSpan.FromMilliseconds(500);
    private const int MaxRetries = 3;

    public RateLimitedHttpClient(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }

    public async Task<HttpResponseMessage> PostAsync(string url, HttpContent content, CancellationToken ct = default)
    {
        await _semaphore.WaitAsync(ct);
        try
        {
            var elapsed = DateTime.UtcNow - _lastRequestTime;
            if (elapsed < MinInterval)
                await Task.Delay(MinInterval - elapsed, ct);

            HttpResponseMessage? response = null;
            for (var attempt = 0; attempt <= MaxRetries; attempt++)
            {
                response = await _httpClient.PostAsync(url, content, ct);
                _lastRequestTime = DateTime.UtcNow;

                if (response.StatusCode != HttpStatusCode.TooManyRequests &&
                    (int)response.StatusCode < 500)
                    break;

                if (attempt == MaxRetries)
                    break;

                var delay = response.Headers.RetryAfter?.Delta
                            ?? TimeSpan.FromSeconds(Math.Pow(2, attempt));
                Console.WriteLine($"  [Retry] HTTP {(int)response.StatusCode}, waiting {delay.TotalSeconds:F1}s (attempt {attempt + 1}/{MaxRetries})...");
                await Task.Delay(delay, ct);
            }

            if (!response!.IsSuccessStatusCode)
            {
                var body = await response.Content.ReadAsStringAsync(ct);
                Console.Error.WriteLine($"[HTTP Error] {(int)response.StatusCode} {response.StatusCode}");
                Console.Error.WriteLine($"  URL: {url}");
                Console.Error.WriteLine($"  Response: {body}");
                response.EnsureSuccessStatusCode();
            }

            return response;
        }
        finally
        {
            _semaphore.Release();
        }
    }
}
