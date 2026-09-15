#pragma once
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "domain/Buildings.h"
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
    uint64 WorldGeneration = 0;
    bool bHasPresentedLevel = false;
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    void ResetScenario(int32 Soldiers);
    bool ResetSettlement();
    void PrepareForLevel(int32 RequestedSoldiers);
    bool PrepareSettlementForLevel();
    bool IsSettlement() const { return !State.build_areas.empty(); }
    const domain::BuildingCatalog& BuildingDefinitions() const { return BuildingCatalog; }
    domain::PlacementResult PreviewBuilding(const domain::PlacementCommand& Command) const;
    domain::PlacementResult PlaceBuilding(const domain::PlacementCommand& Command);
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
    domain::BuildingCatalog BuildingCatalog;
    bool Report(const domain::Result& Result, const FString& Success);
};
