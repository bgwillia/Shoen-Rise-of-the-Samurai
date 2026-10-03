// Editor-only bridge for reversible terrain authoring from Unreal Python.
#if WITH_EDITOR
#include "HAL/IConsoleManager.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Landscape.h"
#include "LandscapeEditLayer.h"

namespace
{
FAutoConsoleCommandWithWorldAndArgs CreateTerrainEditLayer(
    TEXT("Shoen.Terrain.CreateEditLayer"),
    TEXT("Create a named landscape edit layer once. Editor worlds only; requires exactly one landscape."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
    {
        if (!World || World->WorldType != EWorldType::Editor || Args.Num() != 1 || Args[0].IsEmpty()) return;
        ALandscape* Landscape = nullptr;
        for (TActorIterator<ALandscape> It(World); It; ++It)
        {
            if (Landscape) return;
            Landscape = *It;
        }
        if (!Landscape) return;
        const FName Name(*Args[0]);
        if (!Landscape->GetEditLayer(Name)) Landscape->CreateLayer(Name);
    }));
}
#endif
