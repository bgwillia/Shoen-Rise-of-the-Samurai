#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "domain/World.h"
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
    void Rebuild(const domain::World& State, const domain::Formation& Formation);
    void UpdatePose(const domain::Formation& Formation, bool Selected);
    int32 InstanceCount() const;
private:
    UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> Instances;
    UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> Material;
    bool bWasSelected = false;
};
