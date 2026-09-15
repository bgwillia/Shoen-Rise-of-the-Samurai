#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "domain/World.h"
#include "domain/Prototype.h"
#include "FormationView.generated.h"
class UInstancedStaticMeshComponent;
class UMaterialInstanceDynamic;
UCLASS()
class SHOEN_API AFormationView : public AActor
{
    GENERATED_BODY()
public:
    AFormationView();
    uint64 FormationId = 0;
    bool bEnemy = false;
    bool bTerrain = false;
    void SetEnemy(bool Enemy);
    void UpdateCombat(const domain::World& State, const domain::Formation& Formation, const domain::CombatUnit& Unit, bool Selected);
    void Rebuild(const domain::World& State, const domain::Formation& Formation);
    void UpdatePose(const domain::Formation& Formation, bool Selected);
    int32 InstanceCount() const;
private:
    UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> Instances;
    UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> Material;
    bool bWasSelected = false;
    bool bCombatPresentation = false;
    domain::Quantity CachedAlive = -1, CachedDead = -1, CachedWounded = -1;
    domain::TroopRole CachedRole = domain::TroopRole::Polearm;
    FVector SelectionExtent = FVector(560,560,10);
    FLinearColor BaseTint = FLinearColor(.28,.45,.55);
};
