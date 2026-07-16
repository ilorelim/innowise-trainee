var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/", () => "Hello from multi-stage .NET");
app.MapGet("/health", () => Results.Ok("ok"));

app.Run();
