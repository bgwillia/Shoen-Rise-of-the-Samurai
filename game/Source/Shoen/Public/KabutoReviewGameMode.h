#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "KabutoReviewGameMode.generated.h"

class UPoseableMeshComponent;
class USkeletalMeshComponent;
class UStaticMeshComponent;
class UStaticMesh;

// An opt-in art review world. It never reads or changes the gameplay ledger.
UCLASS()
class SHOEN_API AKabutoReviewGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AKabutoReviewGameMode();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

private:
    bool CreateReview();
    void CompleteReview();
    void Fail(const FString& Reason);

    UPROPERTY() TObjectPtr<UPoseableMeshComponent> HeadPreview;
    UPROPERTY() TObjectPtr<USkeletalMeshComponent> AnimatedPreview;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> AttachedHelmet;
    UPROPERTY() TObjectPtr<UStaticMesh> HelmetMesh;
    UPROPERTY() TObjectPtr<UStaticMesh> MannequinMesh;
    FTransform HeadReference;
    int32 Count = 100;
    int32 RenderedBodies = 0;
    int32 RenderedHelmets = 0;
    int32 InstanceComponents = 0;
    FString Mode = TEXT("helmet");
    FString Camera = TEXT("close");
    FString Animation = TEXT("idle");
    FString Output;
    FString Screenshot;
    double Seconds = 0;
    double WarmupUntil = 0;
    double LastFrame = 0;
    double CaptureElapsed = 0;
    double ScreenshotRequestedAt = 0;
    double CameraDistance = 0;
    double MaxAttachmentPositionError = 0;
    double MaxHelmetRotationFromFirst = 0;
    FQuat FirstHelmetRotation = FQuat::Identity;
    bool bObservedHelmetRotation = false;
    uint64 PeakMemory = 0;
    bool bClose = true;
    bool bSamplingComplete = false;
    bool bFailed = false;
    bool bFinished = false;
    TArray<double> FrameTimes;
    TArray<double> GameTimes;
    TArray<double> RenderTimes;
    TArray<double> GpuTimes;
    TArray<double> DrawCalls;
    TArray<double> Primitives;
};
