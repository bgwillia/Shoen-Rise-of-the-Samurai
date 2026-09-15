using UnrealBuildTool;
using System.IO;
public class DomainCore : ModuleRules
{
    public DomainCore(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.NoPCHs;
        CppStandard = CppStandardVersion.Cpp20;
        bEnableExceptions = true;
        bUseUnity = false;
        ForceIncludeFiles.Add(Path.Combine(ModuleDirectory, "Private", "UnrealExports.h"));
        PublicDependencyModuleNames.Add("Core");
    }
}
