using System.Net;
using System.Text.Json;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;

namespace DocumentAI.Tests.API;

public class DocumentationTests
{
    [Theory]
    [InlineData("Development")]
    [InlineData("Production")]
    public async Task OpenApiAndScalarAreAvailableWithoutPublishingPlannedEndpoints(string environment)
    {
        await using var factory = new WebApplicationFactory<Program>()
            .WithWebHostBuilder(builder => builder.UseEnvironment(environment));
        using var client = factory.CreateClient(new WebApplicationFactoryClientOptions
        {
            BaseAddress = new Uri("https://localhost"),
            AllowAutoRedirect = false
        });

        using var openApiResponse = await client.GetAsync("/openapi/v1.json");
        Assert.Equal(HttpStatusCode.OK, openApiResponse.StatusCode);
        using var document = JsonDocument.Parse(await openApiResponse.Content.ReadAsStringAsync());
        var root = document.RootElement;
        Assert.Equal("DocumentAI — Referência da API", root.GetProperty("info").GetProperty("title").GetString());
        var description = root.GetProperty("info").GetProperty("description").GetString();
        Assert.Contains("contratos planejados", description);
        Assert.Contains("titulo", description);
        Assert.Contains("nivelRisco", description);
        Assert.Contains("504", description);
        Assert.True(!root.TryGetProperty("paths", out var paths) || !paths.EnumerateObject().Any());

        using var scalarResponse = await client.GetAsync("/scalar/v1");
        Assert.Equal(HttpStatusCode.OK, scalarResponse.StatusCode);
        Assert.Equal("text/html", scalarResponse.Content.Headers.ContentType?.MediaType);
        var scalarHtml = await scalarResponse.Content.ReadAsStringAsync();
        Assert.Contains("openapi/v1.json", scalarHtml);
        using var scalarScript = await client.GetAsync("/scalar/scalar.js");
        Assert.Equal(HttpStatusCode.OK, scalarScript.StatusCode);

        Assert.Equal(HttpStatusCode.NotFound, (await client.GetAsync("/health")).StatusCode);
        using var request = new StringContent("{}", System.Text.Encoding.UTF8, "application/json");
        Assert.Equal(HttpStatusCode.NotFound,
            (await client.PostAsync("/api/documentos/analisar", request)).StatusCode);
        Assert.Equal(HttpStatusCode.NotFound, (await client.GetAsync("/weatherforecast")).StatusCode);
    }
}
