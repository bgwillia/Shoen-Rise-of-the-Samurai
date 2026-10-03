#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "domain/TerrainSuitability.h"
#include "domain/BuildingTypes.h"
#include "TerrainSuitability.generated.h"
class UInstancedStaticMeshComponent;

struct FTerrainSuitabilitySample
{
    FVector Position=FVector::ZeroVector, Normal=FVector::UpVector;
    double SlopeDegrees=0, WaterSurfaceZ=0;
    bool bInside=false, bNearLowWater=false;
    domain::suitability::Water Water=domain::suitability::Water::Dry;
};
struct FBuildingSuitability
{
    domain::suitability::BuildingResult Result=domain::suitability::BuildingResult::OutsideBuildableTerrain;
    double MaxSlopeDegrees=0, HeightVariationCm=0, GroundZ=0;
};

// One opt-in sampled overlay and on-demand queries against the existing landscape/water.
UCLASS()
class SHOEN_API ATerrainSuitability : public AActor
{
    GENERATED_BODY()
public:
    ATerrainSuitability();
    static ATerrainSuitability* Find(UWorld* World);
    UFUNCTION(BlueprintCallable, CallInEditor, Category="TerrainSuitability") void InitializeSources();
    UFUNCTION(BlueprintCallable, CallInEditor, Category="TerrainSuitability") void CycleDebugMode();
    UFUNCTION(BlueprintCallable, Category="TerrainSuitability") void SetDebugMode(int32 Mode);
    UFUNCTION(BlueprintCallable, Category="TerrainSuitability") float GetSlopeDegrees(FVector Location) const;
    UFUNCTION(BlueprintCallable, Category="TerrainSuitability") FString DescribeLocation(FVector Location) const;
    UFUNCTION(BlueprintCallable, CallInEditor, Category="TerrainSuitability") void WriteQuickCheck();
    FString DebugLabel() const;
    FTerrainSuitabilitySample Query(FVector Location) const;
    FBuildingSuitability EvaluateBuildingFootprint(const FTransform& Transform, FVector2D SizeCm) const;
    domain::suitability::Quality EvaluateRiceSuitability(FVector Location) const;
    domain::suitability::Quality EvaluateDryFarmSuitability(FVector Location) const;
    domain::suitability::Traversal GetInfantryTraversal(FVector Location) const;
    domain::suitability::Traversal GetCavalryTraversal(FVector Location) const;
    bool TraceGround(const FVector& Start,const FVector& End,FHitResult& Hit) const;
    domain::BuildArea MakeBuildArea(uint64 SettlementId);
    domain::suitability::Rules Rules;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Transient, Category="TerrainSuitability") int32 DebugMode=0;
private:
    struct FWaterOutline { TArray<FVector> Points; TArray<double> HalfWidths; domain::suitability::Water Type; bool bClosed=false; };
    TArray<FWaterOutline> WaterOutlines;
    FCollisionQueryParams GroundTrace;
    FBox LandscapeBounds=FBox(ForceInit);
    struct FDebugSample { FTerrainSuitabilitySample Terrain; FBuildingSuitability Building; };
    TArray<FDebugSample> DebugSamples;
    UPROPERTY(Transient) TArray<TObjectPtr<UInstancedStaticMeshComponent>> Markers;
    double DebugSpacingCm=1000, FootprintSpacingCm=150, DebugFootprintCm=600;
    bool bSourcesReady=false;
    void BuildDebugSamples();
};
