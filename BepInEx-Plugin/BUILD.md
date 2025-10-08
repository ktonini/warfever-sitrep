# Building the BepInEx Plugin

## Prerequisites

1. **.NET SDK 6.0 or higher**
   - Download from: https://dotnet.microsoft.com/download
   - Verify installation: `dotnet --version`

2. **Visual Studio 2022** (optional, for easier development)
   - Community Edition (free): https://visualstudio.microsoft.com/
   - Or use VS Code with C# extension

## Build Instructions

### Method 1: Command Line (Recommended)

```bash
cd C:\Users\k33bz\OneDrive\git\lastwar-asset-extractor\BepInEx-Plugin
dotnet build -c Release
```

The compiled plugin will be in: `bin/Release/netstandard2.1/LastWarTextureExtractor.dll`

### Method 2: Visual Studio

1. Open `LastWarTextureExtractor.csproj` in Visual Studio
2. Set configuration to "Release"
3. Build → Build Solution (Ctrl+Shift+B)
4. Find DLL in `bin\Release\netstandard2.1\`

## Troubleshooting

### Missing NuGet Packages
```bash
dotnet restore
```

### Unity Version Mismatch
If The Last War uses a different Unity version than 2019.4.40:
1. Open `LastWarTextureExtractor.csproj`
2. Change `UnityEngine.Modules` version to match the game
3. Rebuild

### Build Errors
- Ensure .NET SDK is installed
- Run `dotnet restore` first
- Check that BepInEx packages are restored

## Installation After Build

Copy the compiled DLL to:
```
C:\Users\k33bz\AppData\Local\TheLastWar\app-1.0.198\BepInEx\plugins\
```

See `INSTALLATION.md` for full setup instructions.
