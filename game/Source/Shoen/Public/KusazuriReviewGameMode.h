#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "KusazuriReviewGameMode.generated.h"

class UAnimSequence;
class UPoseableMeshComponent;
class USkinnedMeshComponent;
class USkeletalMesh;
class UStaticMesh;
class UStaticMeshComponent;
class USceneComponent;

// Opt-in modular waist armor inspection and static asset-cost probe only; no gameplay, population or combat ownership.
UCLASS()
class SHOEN_API AKusazuriReviewGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AKusazuriReviewGameMode();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
private:
    bool CreateReview();
    bool ReadReviewContract();
    bool CreateCharacter(AActor* Owner, USceneComponent* Root, const FVector& Position);
    void UpdateInspectionPose();
    bool UpdateSodeSuspension();
    bool UpdateKusazuriHinges();
    void CompleteReview();
    void Fail(const FString& Reason);
    UPROPERTY() TObjectPtr<UAnimSequence> ReviewClip;
    UPROPERTY() TObjectPtr<USkeletalMesh> KusazuriMesh;
    UPROPERTY() TObjectPtr<UPoseableMeshComponent> PoseKusazuri;
    UPROPERTY() TObjectPtr<UStaticMesh> KusazuriStaticMesh;
    UPROPERTY() TObjectPtr<UStaticMesh> MannequinStaticMesh;
    UPROPERTY() TObjectPtr<UStaticMesh> SodeLeftStaticMesh;
    UPROPERTY() TObjectPtr<UStaticMesh> SodeRightStaticMesh;
    FTransform PanelTargets[7];
    double PanelAngles[7] = {};
    double MaxPanelAngles[7] = {};
    int32 KusazuriControllerSamples = 0;
    int32 RenderedKusazuri = 0;
    int32 InstanceComponents = 0;
    int32 Count = 1;
    double MaxKusazuriBonePositionError = 0;
    double MaxKusazuriBoneRotationError = 0;
    double CameraElevation = 15;
    UPROPERTY() TObjectPtr<USkeletalMesh> BodyMesh;
    UPROPERTY() TObjectPtr<USkeletalMesh> ArmorMesh;
    UPROPERTY() TObjectPtr<UStaticMesh> HelmetMesh;
    UPROPERTY() TObjectPtr<UStaticMesh> ArmorStaticMesh;
    UPROPERTY() TArray<TObjectPtr<USkinnedMeshComponent>> Bodies;
    UPROPERTY() TArray<TObjectPtr<USkinnedMeshComponent>> Armors;
    UPROPERTY() TArray<TObjectPtr<UStaticMeshComponent>> Helmets;
    UPROPERTY() TObjectPtr<UPoseableMeshComponent> PoseBody;
    UPROPERTY() TObjectPtr<UPoseableMeshComponent> PoseArmor;
    UPROPERTY() TObjectPtr<USkeletalMesh> SodeLeftMesh;
    UPROPERTY() TObjectPtr<USkeletalMesh> SodeRightMesh;
    UPROPERTY() TArray<TObjectPtr<USkinnedMeshComponent>> Sodes;
    UPROPERTY() TArray<TObjectPtr<UPoseableMeshComponent>> PoseSode;
    TArray<FTransform> BodyReferenceComponentSpace;
    FTransform SodeTarget[2];
    FVector SodeDirection[2];
    double SodeOpening[2] = {0,0};
    double MaxSodeOpening[2] = {0,0};
    double SodeLiftClearance[2] = {0,0};
    double MaxSodeLiftClearance[2] = {0,0};
    double MaxSodeBodyRotationDifference[2] = {0,0};
    int32 SuspensionSamples = 0;
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
    TArray<FName> SodeValidationBones;
    FString ContractPath;
    int32 RenderedBodies = 0;
    int32 RenderedHelmets = 0;
    int32 RenderedArmors = 0;
    int32 RenderedSode = 0;
    FString Mode = TEXT("kusazuri");
    FString Camera = TEXT("close");
    FString Animation = TEXT("idle");
    FString Pose = TEXT("animation");
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
    double MaxSodeBonePositionError = 0;
    double MaxSodeBoneRotationError = 0;
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
