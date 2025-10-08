using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;

namespace LastWarTextureExtractor
{
    [BepInPlugin(PluginGUID, PluginName, PluginVersion)]
    public class TextureExtractorPlugin : BaseUnityPlugin
    {
        public const string PluginGUID = "com.k33bz.lastwar.textureextractor";
        public const string PluginName = "LastWar Texture Extractor";
        public const string PluginVersion = "1.0.0";

        private ManualLogSource Log;
        private ConfigEntry<KeyCode> ExtractKey;
        private ConfigEntry<KeyCode> ExtractAllKey;
        private ConfigEntry<bool> AutoExtractOnLoad;
        private ConfigEntry<string> OutputDirectory;

        private string outputPath;
        private HashSet<string> extractedTextures = new HashSet<string>();
        private bool hasExtractedAll = false;

        void Awake()
        {
            Log = Logger;

            // Configuration
            ExtractKey = Config.Bind("Hotkeys", "ExtractVisibleTextures", KeyCode.F9,
                "Key to extract currently visible textures");

            ExtractAllKey = Config.Bind("Hotkeys", "ExtractAllTextures", KeyCode.F10,
                "Key to extract ALL loaded textures in memory");

            AutoExtractOnLoad = Config.Bind("General", "AutoExtractOnLoad", false,
                "Automatically extract all textures when game loads");

            OutputDirectory = Config.Bind("General", "OutputPath", "BepInEx/ExtractedTextures",
                "Directory to save extracted textures");

            // Set up output directory
            outputPath = Path.Combine(Paths.GameRootPath, OutputDirectory.Value);
            Directory.CreateDirectory(outputPath);

            Log.LogInfo($"{PluginName} v{PluginVersion} loaded!");
            Log.LogInfo($"Press {ExtractKey.Value} to extract visible textures");
            Log.LogInfo($"Press {ExtractAllKey.Value} to extract ALL loaded textures");
            Log.LogInfo($"Output directory: {outputPath}");
        }

        void Update()
        {
            // Extract visible textures
            if (Input.GetKeyDown(ExtractKey.Value))
            {
                Log.LogInfo("Extracting visible textures...");
                ExtractVisibleTextures();
            }

            // Extract all textures
            if (Input.GetKeyDown(ExtractAllKey.Value))
            {
                Log.LogInfo("Extracting ALL textures in memory...");
                ExtractAllTextures();
            }
        }

        void Start()
        {
            if (AutoExtractOnLoad.Value)
            {
                Log.LogInfo("Auto-extracting all textures on load...");
                // Delay extraction to ensure assets are loaded
                Invoke(nameof(ExtractAllTextures), 5f);
            }
        }

        private void ExtractVisibleTextures()
        {
            try
            {
                int count = 0;

                // Find all active Image components (UI images)
                var images = Resources.FindObjectsOfTypeAll<UnityEngine.UI.Image>();
                foreach (var img in images)
                {
                    if (img.sprite != null && img.sprite.texture != null)
                    {
                        if (SaveTexture(img.sprite.texture, "UI"))
                            count++;
                    }
                }

                // Find all active SpriteRenderer components
                var spriteRenderers = Resources.FindObjectsOfTypeAll<SpriteRenderer>();
                foreach (var sr in spriteRenderers)
                {
                    if (sr.sprite != null && sr.sprite.texture != null)
                    {
                        if (SaveTexture(sr.sprite.texture, "Sprite"))
                            count++;
                    }
                }

                // Find all RawImage components
                var rawImages = Resources.FindObjectsOfTypeAll<UnityEngine.UI.RawImage>();
                foreach (var ri in rawImages)
                {
                    if (ri.texture != null && ri.texture is Texture2D tex)
                    {
                        if (SaveTexture(tex, "RawImage"))
                            count++;
                    }
                }

                Log.LogInfo($"Extracted {count} visible textures!");
            }
            catch (Exception ex)
            {
                Log.LogError($"Error extracting visible textures: {ex}");
            }
        }

        private void ExtractAllTextures()
        {
            try
            {
                int count = 0;
                int skipped = 0;

                // Find ALL Texture2D objects in memory (loaded assets)
                var allTextures = Resources.FindObjectsOfTypeAll<Texture2D>();

                Log.LogInfo($"Found {allTextures.Length} Texture2D objects in memory");

                foreach (var texture in allTextures)
                {
                    if (texture == null) continue;

                    // Skip already extracted
                    string textureName = GetSafeTextureName(texture);
                    if (extractedTextures.Contains(textureName))
                    {
                        skipped++;
                        continue;
                    }

                    if (SaveTexture(texture, "All"))
                    {
                        count++;
                    }
                }

                hasExtractedAll = true;
                Log.LogInfo($"Extraction complete! New: {count}, Skipped (already extracted): {skipped}");
                Log.LogInfo($"Total unique textures extracted: {extractedTextures.Count}");
            }
            catch (Exception ex)
            {
                Log.LogError($"Error extracting all textures: {ex}");
            }
        }

        private string GetSafeTextureName(Texture2D texture)
        {
            string name = string.IsNullOrEmpty(texture.name) ? $"Texture_{texture.GetInstanceID()}" : texture.name;

            // Sanitize filename
            foreach (char c in Path.GetInvalidFileNameChars())
            {
                name = name.Replace(c, '_');
            }

            return name;
        }

        private string CategorizeTexture(string textureName)
        {
            string nameLower = textureName.ToLower();

            // Categorize by name patterns
            if (nameLower.Contains("alliance") || nameLower.Contains("guild") || nameLower.Contains("clan"))
                return "Alliance";

            if (nameLower.Contains("item") || nameLower.Contains("icon") || nameLower.Contains("resource"))
                return "Items";

            if (nameLower.Contains("hero") || nameLower.Contains("character") || nameLower.Contains("portrait"))
                return "Characters";

            if (nameLower.Contains("building") || nameLower.Contains("structure"))
                return "Buildings";

            if (nameLower.Contains("ui") || nameLower.Contains("button") || nameLower.Contains("panel"))
                return "UI";

            if (nameLower.Contains("map") || nameLower.Contains("terrain"))
                return "Map";

            if (nameLower.Contains("font") || nameLower.Contains("atlas") || nameLower.Contains("sdf"))
                return "Fonts";

            return "Misc";
        }

        private bool SaveTexture(Texture2D texture, string source)
        {
            try
            {
                // Skip null or invalid textures
                if (texture == null || texture.width == 0 || texture.height == 0)
                    return false;

                string textureName = GetSafeTextureName(texture);

                // Skip if already extracted
                if (extractedTextures.Contains(textureName))
                    return false;

                // Skip Unity's internal textures
                if (textureName.ToLower().Contains("unity") &&
                    (textureName.ToLower().Contains("default") ||
                     textureName.ToLower().Contains("builtin") ||
                     textureName.ToLower().Contains("watermark")))
                {
                    return false;
                }

                // Categorize texture
                string category = CategorizeTexture(textureName);
                string categoryPath = Path.Combine(outputPath, category);
                Directory.CreateDirectory(categoryPath);

                // Try to read the texture
                Texture2D readableTexture = null;

                try
                {
                    // If texture is not readable, we need to copy it
                    if (!texture.isReadable)
                    {
                        // Create a temporary RenderTexture
                        RenderTexture tmp = RenderTexture.GetTemporary(
                            texture.width,
                            texture.height,
                            0,
                            RenderTextureFormat.Default,
                            RenderTextureReadWrite.Linear);

                        // Blit the texture to the RenderTexture
                        Graphics.Blit(texture, tmp);

                        // Read the RenderTexture
                        RenderTexture previous = RenderTexture.active;
                        RenderTexture.active = tmp;

                        readableTexture = new Texture2D(texture.width, texture.height, TextureFormat.RGBA32, false);
                        readableTexture.ReadPixels(new Rect(0, 0, tmp.width, tmp.height), 0, 0);
                        readableTexture.Apply();

                        RenderTexture.active = previous;
                        RenderTexture.ReleaseTemporary(tmp);
                    }
                    else
                    {
                        readableTexture = texture;
                    }

                    // Encode to PNG
                    byte[] pngData = readableTexture.EncodeToPNG();

                    if (pngData != null && pngData.Length > 0)
                    {
                        string filePath = Path.Combine(categoryPath, $"{textureName}.png");
                        File.WriteAllBytes(filePath, pngData);

                        extractedTextures.Add(textureName);

                        Log.LogDebug($"[{source}] Saved: {category}/{textureName}.png ({texture.width}x{texture.height})");

                        // Clean up if we created a copy
                        if (readableTexture != texture)
                        {
                            Destroy(readableTexture);
                        }

                        return true;
                    }
                }
                catch (Exception ex)
                {
                    Log.LogWarning($"Could not read texture '{textureName}': {ex.Message}");

                    // Clean up
                    if (readableTexture != null && readableTexture != texture)
                    {
                        Destroy(readableTexture);
                    }
                }

                return false;
            }
            catch (Exception ex)
            {
                Log.LogError($"Error saving texture: {ex}");
                return false;
            }
        }
    }
}
