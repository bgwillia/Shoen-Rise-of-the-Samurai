using UnrealBuildTool;
public class Shoen : ModuleRules
{
    public Shoen(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        CppStandard = CppStandardVersion.Cpp20;
        bEnableExceptions = true;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "InputCore", "DomainCore" });
        PrivateDependencyModuleNames.AddRange(new[] { "Json", "JsonUtilities", "Slate", "SlateCore", "ApplicationCore", "MeshDescription", "StaticMeshDescription" });
    }
}
