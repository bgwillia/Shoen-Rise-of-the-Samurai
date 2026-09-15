#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "domain/World.h"
#include "SettlementView.generated.h"

class UInstancedStaticMeshComponent;
class UStaticMeshComponent;
class UStaticMesh;
class UMaterialInterface;
class UMaterialInstanceDynamic;

// Passive projection of the saved settlement. Rebuilding never submits commands.
UCLASS()
class SHOEN_API ASettlementView : public AActor
{
    GENERATED_BODY()
public:
    ASettlementView();
    void Rebuild(const domain::World& State);
    int32 BuildingCount() const;
    bool GetBuildingTransform(uint64 Id, FTransform& Out) const;
    bool PickBuilding(const FVector& Origin, const FVector& Direction, uint64& OutId) const;
    void SetSelectedBuilding(uint64 Id, const domain::World& State);
    uint64 SelectedBuildingId() const { return SelectedId; }
    int32 TerrainTriangleCount() const { return BuiltTerrainTriangles; }
    void SetPreview(const domain::BuildingDefinition& Definition,
        const domain::PlacementCommand& Command, int32 GroundZ, bool bValid);
    void HidePreview();

private:
    void PrepareMeshesAndMaterials();
    void RebuildTerrain(const domain::World& State);
    double PreviewHeight(double X, double Y, int32 GroundZ) const;
    void RebuildFootprint(UInstancedStaticMeshComponent* Component, int32 X, int32 Y,
        int32 Yaw, int32 Width, int32 Depth, int32 GroundZ, double LineWidth);

    UPROPERTY() TObjectPtr<UStaticMeshComponent> Terrain;
    UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> Bodies;
    UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> Roofs;
    UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> Boundary;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> PreviewBody;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> PreviewRoof;
    UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> PreviewFootprint;
    UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> SelectedFootprint;
    UPROPERTY() TObjectPtr<UStaticMesh> TerrainMesh;
    UPROPERTY() TObjectPtr<UStaticMesh> RoofMesh;
    UPROPERTY() TObjectPtr<UMaterialInterface> BaseMaterial;
    UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> PreviewMaterial;

    TMap<uint64, FTransform> BuildingTransforms;
    // Presentation-only decoding table. Instance indices never persist as selection.
    TArray<uint64> InstanceBuildingIds;
    uint64 SelectedId = 0;
    std::map<domain::EntityId, domain::BuildArea> PresentedAreas;
    int32 BuiltTerrainTriangles = 0;
    bool bHasBuiltTerrain = false;
};
