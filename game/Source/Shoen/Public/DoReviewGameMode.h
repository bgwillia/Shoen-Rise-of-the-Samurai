#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "DoReviewGameMode.generated.h"

class UAnimSequence;
class UPoseableMeshComponent;
class USkinnedMeshComponent;
class USkeletalMesh;
class UStaticMesh;
class UStaticMeshComponent;
class USceneComponent;

// Opt-in Dō art inspection only; no gameplay, population or combat ownership.
UCLASS()
class SHOEN_API ADoReviewGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    ADoReviewGameMode();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
private:
    bool CreateReview();
    bool ReadReviewContract();
    bool CreateCharacter(AActor* Owner, USceneComponent* Root, const FVector& Position);
    void UpdateInspectionPose();
    void CompleteReview();
    void Fail(const FString& Reason);
    UPROPERTY() TObjectPtr<UAnimSequence> ReviewClip;
    UPROPERTY() TObjectPtr<USkeletalMesh> BodyMesh;
    UPROPERTY() TObjectPtr<USkeletalMesh> ArmorMesh;
    UPROPERTY() TObjectPtr<UStaticMesh> HelmetMesh;
    UPROPERTY() TObjectPtr<UStaticMesh> MannequinMesh;
    UPROPERTY() TObjectPtr<UStaticMesh> ArmorStaticMesh;
    UPROPERTY() TArray<TObjectPtr<USkinnedMeshComponent>> Bodies;
    UPROPERTY() TArray<TObjectPtr<USkinnedMeshComponent>> Armors;
    UPROPERTY() TArray<TObjectPtr<UStaticMeshComponent>> Helmets;
    UPROPERTY() TObjectPtr<UPoseableMeshComponent> PoseBody;
    UPROPERTY() TObjectPtr<UPoseableMeshComponent> PoseArmor;
    FTransform RootReference;
    FTransform HeadReference;
    FTransform HelmetAtReference;
    FTransform HelmetRelative;
    FVector HelmetOffset = FVector::ZeroVector;
    FVector HelmetScale = FVector::OneVector;
    FRotator HelmetRotation = FRotator::ZeroRotator;
    double ComponentYaw = 0;
    FName TurnBone;
    FName BendBone;
    TArray<FName> ArmorValidationBones;
    FString ContractPath;
    int32 Count = 100;
    int32 RenderedBodies = 0;
    int32 RenderedHelmets = 0;
    int32 RenderedArmors = 0;
    int32 InstanceComponents = 0;
    FString Mode = TEXT("armor");
    FString Camera = TEXT("close");
    FString Animation = TEXT("idle");
    FString Pose = TEXT("animation");
    FString Crowd = TEXT("static");
    FString AnimationAsset;
    FString Output;
    FString Screenshot;
    double Seconds = 0;
    double MinAnimationPosition = 1e30;
    double MaxAnimationPosition = -1e30;
    double WarmupUntil = 0;
    double LastFrame = 0;
    double CaptureElapsed = 0;
    double ScreenshotRequestedAt = 0;
    double CameraDistance = 0;
    double MaxRootPositionError = 0;
    double MaxRootRotationError = 0;
    double MaxAttachmentPositionError = 0;
    double MaxArmorBonePositionError = 0;
    double MaxArmorBoneRotationError = 0;
    double MaxWorldScaleError = 0;
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
