#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "StrategyCameraPawn.generated.h"
class USpringArmComponent;
class UCameraComponent;
UCLASS()
class SHOEN_API AStrategyCameraPawn : public APawn
{
    GENERATED_BODY()
public:
    AStrategyCameraPawn();
    virtual void Tick(float DeltaSeconds) override;
    void FrameScenario(int32 FormationCount);
    float Zoom() const;
    void FrameSettlement();
    void FramePrototype(FVector Center, float Span);
    bool bBenchmarkMotion = false;
private:
    UPROPERTY() TObjectPtr<USpringArmComponent> Arm;
    UPROPERTY() TObjectPtr<UCameraComponent> Camera;
    FVector TargetFocus = FVector::ZeroVector;
    float TargetZoom = 7000;
    float TargetYaw = -90;
    float SweepTime = 0;
    FVector ScenarioFocus = FVector::ZeroVector;
    float ScenarioZoom = 7000;
};
