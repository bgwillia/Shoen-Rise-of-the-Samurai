#pragma once
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "domain/World.h"
#include "ShoenSimulationSubsystem.generated.h"

UCLASS()
class SHOEN_API UShoenSimulationSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    domain::World State;
    FString Message;
    uint64 ViewGeneration = 0;
    bool bHasPresentedLevel = false;
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    void ResetScenario(int32 Soldiers);
    void PrepareForLevel(int32 RequestedSoldiers);
    void Advance(float Seconds);
    void SetGameSpeed(int32 Speed);
    bool MobilizeProof();
    bool ResolveProof();
    bool DemobilizeProof();
    bool SaveToPath(const FString& Path);
    bool LoadFromPath(const FString& Path);
    bool Save();
    bool Load();
private:
    bool Report(const domain::Result& Result, const FString& Success);
};
