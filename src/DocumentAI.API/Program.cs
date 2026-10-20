using Scalar.AspNetCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
var documentation = await File.ReadAllTextAsync(
    Path.Combine(AppContext.BaseDirectory, "Documentation", "api-reference.md"));

builder.Services.AddOpenApi("v1", options =>
{
    options.AddDocumentTransformer((document, context, cancellationToken) =>
    {
        document.Info.Title = "DocumentAI — Referência da API";
        document.Info.Version = "v1";
        document.Info.Description = documentation;
        return Task.CompletedTask;
    });
});

var app = builder.Build();

// A documentação foi autorizada em Development e Production.
app.MapOpenApi();
app.MapScalarApiReference(options =>
{
    options.WithTitle("DocumentAI — Documentação e testes")
        .DisableAgent();
});

app.UseHttpsRedirection();

app.UseAuthorization();

app.MapControllers();

app.Run();

// Permite testes de inicialização com WebApplicationFactory.
public partial class Program;
