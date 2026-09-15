#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BattlefieldView.generated.h"
class UInstancedStaticMeshComponent;
class UStaticMeshComponent;
UCLASS()
class SHOEN_API ABattlefieldView : public AActor
{
    GENERATED_BODY()
public:
    ABattlefieldView();
    virtual void BeginPlay() override;
private:
    UPROPERTY() TObjectPtr<UStaticMeshComponent> Ground;
    UPROPERTY() TArray<TObjectPtr<UInstancedStaticMeshComponent>> SurfaceLayers;
};
