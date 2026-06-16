FROM mcr.microsoft.com/dotnet/runtime:10.0 AS base
USER $APP_UID
WORKDIR /app

FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
ARG BUILD_CONFIGURATION=Release
WORKDIR /src
COPY ["Ultracar-Support-Bitrix-Analisys/Ultracar-Support-Bitrix-Analisys.csproj", "Ultracar-Support-Bitrix-Analisys/"]
RUN dotnet restore "Ultracar-Support-Bitrix-Analisys/Ultracar-Support-Bitrix-Analisys.csproj"
COPY . .
WORKDIR "/src/Ultracar-Support-Bitrix-Analisys"
RUN dotnet build "./Ultracar-Support-Bitrix-Analisys.csproj" -c $BUILD_CONFIGURATION -o /app/build

FROM build AS publish
ARG BUILD_CONFIGURATION=Release
RUN dotnet publish "./Ultracar-Support-Bitrix-Analisys.csproj" -c $BUILD_CONFIGURATION -o /app/publish /p:UseAppHost=false

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "Ultracar-Support-Bitrix-Analisys.dll"]
