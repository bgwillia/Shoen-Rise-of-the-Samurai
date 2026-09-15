#include "KusazuriReviewGameMode.h"
#include "KusazuriHinges.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "UObject/Package.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PoseableMeshComponent.h"
#include "Components/RectLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "DynamicRHI.h"
#include "Engine/DirectionalLight.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/RectLight.h"
#include "Engine/SkyLight.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/TextureCube.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMemory.h"
#include "HAL/PlatformMisc.h"
#include "HAL/PlatformProperties.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/EngineVersion.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "RenderTimer.h"
#include "RHIStats.h"
#include "Serialization/JsonSerializer.h"
#include "StaticMeshResources.h"
#include "UnrealClient.h"

#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkeletalMeshLODRenderData.h"

namespace
{
const TCHAR* KusazuriMannyAsset = TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple");
const TCHAR* KusazuriMannyAnimations = TEXT("/Game/Characters/Mannequins/Anims/Unarmed/");
const TCHAR* KusazuriExistingKabutoRoot = TEXT("/Game/Art/Characters/Samurai/Kabuto01/");
const TCHAR* KusazuriRoot = TEXT("/Game/Art/Characters/Samurai/Kusazuri01/");
const TCHAR* KusazuriExistingSodeRoot = TEXT("/Game/Art/Characters/Samurai/Sode01/");
const TCHAR* KusazuriExistingDoRoot = TEXT("/Game/Art/Characters/Samurai/Do01/");
template<typename T> T* KusazuriArt(const TCHAR* Root, const TCHAR* Name)
{
    return LoadObject<T>(nullptr, *(FString(Root) + Name));
}

double KusazuriPercentile(TArray<double> Values, double Fraction)
{
    if (Values.IsEmpty()) return 0;
    Values.Sort();
    return Values[FMath::Clamp(FMath::CeilToInt(Fraction * Values.Num()) - 1, 0, Values.Num() - 1)];
}

void KusazuriAddTiming(const TSharedRef<FJsonObject>& Json, const TCHAR* Key, const TArray<double>& Samples)
{
    const TArray<double> Values = Samples.FilterByPredicate([](double Value) { return Value > 0 && FMath::IsFinite(Value); });
    auto Timing = MakeShared<FJsonObject>();
    Timing->SetNumberField(TEXT("samples"), Values.Num());
    for (const auto& Entry : TArray<TPair<FString, double>>{
        {TEXT("median_ms"), .5}, {TEXT("p95_ms"), .95}, {TEXT("worst_ms"), 1.0}})
    {
        if (Values.IsEmpty()) Timing->SetField(Entry.Key, MakeShared<FJsonValueNull>());
        else Timing->SetNumberField(Entry.Key, KusazuriPercentile(Values, Entry.Value));
    }
    Json->SetObjectField(Key, Timing);
}

void KusazuriAddMeshInfo(const TSharedRef<FJsonObject>& Json, const TCHAR* Key, UStaticMesh* Mesh)
{
    if (!Mesh) return;
    auto Info = MakeShared<FJsonObject>();
    Info->SetStringField(TEXT("asset"), Mesh->GetPathName());
    Info->SetNumberField(TEXT("material_slots"), Mesh->GetStaticMaterials().Num());
    TArray<TSharedPtr<FJsonValue>> Lods;
    if (const auto* Data = Mesh->GetRenderData())
    {
        for (int32 Index = 0; Index < Data->LODResources.Num(); ++Index)
        {
            const auto& Lod = Data->LODResources[Index];
            auto Entry = MakeShared<FJsonObject>();
            Entry->SetNumberField(TEXT("lod"), Index);
            Entry->SetNumberField(TEXT("triangles"), Lod.GetNumTriangles());
            Entry->SetNumberField(TEXT("vertices"), Lod.GetNumVertices());
            Entry->SetNumberField(TEXT("sections"), Lod.Sections.Num());
            Lods.Add(MakeShared<FJsonValueObject>(Entry));
        }
    }
    Info->SetArrayField(TEXT("lods"), Lods);
    Json->SetObjectField(Key, Info);
}

void KusazuriConfigurePrimitive(UPrimitiveComponent* Component)
{
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCanEverAffectNavigation(false);
    Component->SetCastShadow(true);
}
}

namespace
{
bool KusazuriValidArmor(USkeletalMesh* Armor, USkeletalMesh* Body)
{
    if (!Armor || !Body || Armor->GetSkeleton() != Body->GetSkeleton() || Armor->GetMaterials().IsEmpty()) return false;
    const auto* Data = Armor->GetResourceForRendering();
    if (!Data || Data->LODRenderData.IsEmpty()) return false;
    for (const auto& Lod : Data->LODRenderData)
    {
        if (Lod.RenderSections.IsEmpty() || Lod.GetNumVertices() == 0) return false;
        for (const auto& Section : Lod.RenderSections)
            if (Section.NumTriangles == 0 || !Armor->GetMaterials().IsValidIndex(Section.MaterialIndex) || Section.MaxBoneInfluences < 1) return false;
    }
    const auto& Ref = Armor->GetRefSkeleton();
    const auto& BodyRef = Body->GetRefSkeleton();
    for (int32 Index = 0; Index < Ref.GetNum(); ++Index)
    {
        const int32 BodyIndex = BodyRef.FindBoneIndex(Ref.GetBoneName(Index));
        if (BodyIndex == INDEX_NONE || !Ref.GetRefBonePose()[Index].Equals(BodyRef.GetRefBonePose()[BodyIndex], .01)) return false;
        const int32 Parent = Ref.GetParentIndex(Index), BodyParent = BodyRef.GetParentIndex(BodyIndex);
        if ((Parent == INDEX_NONE) != (BodyParent == INDEX_NONE)) return false;
        if (Parent != INDEX_NONE && Ref.GetBoneName(Parent) != BodyRef.GetBoneName(BodyParent)) return false;
    }
    return Ref.GetNum() > 0;
}

// Exact port of SourceArt/.../Sode01/Scripts/sode_motion.py. Source bind
// geometry remains native Manny; only the separate armor component pose moves.
FVector KusazuriSodeBlenderAxes(const FVector& Native)
{
    return FVector(Native.X, -Native.Y, Native.Z);
}

bool KusazuriSodeSuspensionTarget(const FTransform& RefTorso, const FTransform& RefUpper, const FTransform& RefLower,
    const FTransform& Torso, const FTransform& Upper, const FTransform& Lower, double Sign,
    FTransform& Target, double& Opening, double& LiftClearance, FVector& Direction)
{
    if (RefTorso.ContainsNaN() || RefUpper.ContainsNaN() || RefLower.ContainsNaN() ||
        Torso.ContainsNaN() || Upper.ContainsNaN() || Lower.ContainsNaN()) return false;
    const FQuat TorsoRotation = (Torso.GetRotation()*RefTorso.GetRotation().Inverse()).GetNormalized();
    const FVector RestDown = KusazuriSodeBlenderAxes(RefLower.GetLocation()-RefUpper.GetLocation()).GetSafeNormal();
    const FVector RestOut = FVector(Sign*FMath::Abs(RestDown.Z), 0, FMath::Abs(RestDown.X)).GetSafeNormal();
    FVector RestAcross = FVector::CrossProduct(RestDown, RestOut).GetSafeNormal();
    if (RestAcross.Y < 0) RestAcross *= -1;
    Direction = KusazuriSodeBlenderAxes(TorsoRotation.UnrotateVector((Lower.GetLocation()-Upper.GetLocation()).GetSafeNormal()));
    double Elevation = FMath::Clamp((Sign*Direction.X-.85)/.10,0.0,1.0);
    Elevation = Elevation*Elevation*(3-2*Elevation);
    const FVector Hanging = FVector(Direction.X,Direction.Y,FMath::Min(-.12,Direction.Z)).GetSafeNormal();
    const FVector Down = (Hanging*(1-Elevation)+Direction*Elevation).GetSafeNormal();
    const FVector Axis(Sign,0,0);
    FVector Out = (Axis-Down*FVector::DotProduct(Axis,Down)).GetSafeNormal();
    double Lift = FMath::Clamp((Direction.Z+.30)/.30,0.0,1.0)*Elevation;
    Lift = Lift*Lift*(3-2*Lift);
    const FVector Over = FVector(-Sign*Down.Z,0,Sign*Down.X).GetSafeNormal();
    if (Out.IsNearlyZero()) Out = Over;
    Out = (Out*(1-Lift)+Over*Lift).GetSafeNormal();
    FVector Across = FVector::CrossProduct(Down,Out).GetSafeNormal();
    if (Sign > 0) Across *= -1;
    LiftClearance = 4*Lift;
    if (RestDown.IsNearlyZero() || RestOut.IsNearlyZero() || RestAcross.IsNearlyZero() ||
        Direction.IsNearlyZero() || Down.IsNearlyZero() || Out.IsNearlyZero() || Across.IsNearlyZero()) return false;
    // old/new frames are orthonormal, possibly reflected. Their product is a
    // proper rotation. Reflect input/output Y to implement native C*R*C.
    auto RotateNative = [&](const FVector& Native)
    {
        const FVector V = KusazuriSodeBlenderAxes(Native);
        return KusazuriSodeBlenderAxes(Out*FVector::DotProduct(RestOut,V) + Across*FVector::DotProduct(RestAcross,V) +
            Down*FVector::DotProduct(RestDown,V));
    };
    FMatrix Relative = FMatrix::Identity;
    Relative.SetAxis(0, RotateNative(FVector::ForwardVector));
    Relative.SetAxis(1, RotateNative(FVector::RightVector));
    Relative.SetAxis(2, RotateNative(FVector::UpVector));
    if (!FMath::IsNearlyEqual(Relative.Determinant(), 1.0, .0001)) return false;
    const FQuat Rotation = (TorsoRotation*FQuat(Relative)).GetNormalized();
    Opening = 8*FMath::Max(0.0,(Sign*Direction.X-.576)/.364) + 9*FMath::Max(0.0,-Sign*Direction.X) +
        2*FMath::Abs(Direction.Y) + 7*FMath::Max(0.0,Direction.Z);
    Target = FTransform((Rotation*RefUpper.GetRotation()).GetNormalized(),
        Upper.GetLocation()+TorsoRotation.RotateVector(KusazuriSodeBlenderAxes(FVector(Sign*Opening,0,0)+Out*LiftClearance)), RefUpper.GetScale3D());
    return !Target.ContainsNaN() && FMath::IsFinite(Opening);
}

void KusazuriAddSkeletalInfo(const TSharedRef<FJsonObject>& Json, const TCHAR* Key, USkeletalMesh* Mesh)
{
    if (!Mesh) return;
    auto Info = MakeShared<FJsonObject>();
    Info->SetStringField(TEXT("asset"), Mesh->GetPathName());
    Info->SetNumberField(TEXT("material_slots"), Mesh->GetMaterials().Num());
    Info->SetNumberField(TEXT("bones"), Mesh->GetRefSkeleton().GetNum());
    TArray<TSharedPtr<FJsonValue>> Lods;
    if (const auto* Data = Mesh->GetResourceForRendering())
        for (int32 Index = 0; Index < Data->LODRenderData.Num(); ++Index)
        {
            const auto& Lod = Data->LODRenderData[Index];
            auto Entry = MakeShared<FJsonObject>();
            int64 Triangles = 0;
            int32 Influences = 0;
            TArray<TSharedPtr<FJsonValue>> Materials;
            for (const auto& Section : Lod.RenderSections)
            {
                Triangles += Section.NumTriangles;
                Influences = FMath::Max(Influences, Section.MaxBoneInfluences);
                Materials.Add(MakeShared<FJsonValueNumber>(Section.MaterialIndex));
            }
            Entry->SetNumberField(TEXT("lod"), Index);
            Entry->SetNumberField(TEXT("triangles"), Triangles);
            Entry->SetNumberField(TEXT("vertices"), Lod.GetNumVertices());
            Entry->SetNumberField(TEXT("sections"), Lod.RenderSections.Num());
            Entry->SetNumberField(TEXT("uv_channels"), Lod.StaticVertexBuffers.StaticMeshVertexBuffer.GetNumTexCoords());
            Entry->SetNumberField(TEXT("max_bone_influences"), Influences);
            Entry->SetArrayField(TEXT("section_material_slots"), Materials);
            Lods.Add(MakeShared<FJsonValueObject>(Entry));
        }
    Info->SetArrayField(TEXT("lods"), Lods);
    Json->SetObjectField(Key, Info);
}
}

AKusazuriReviewGameMode::AKusazuriReviewGameMode()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickGroup = TG_PostUpdateWork;
    DefaultPawnClass = nullptr;
    HUDClass = nullptr;
}

void AKusazuriReviewGameMode::Fail(const FString& Reason)
{
    bFailed = true;
    UE_LOG(LogTemp, Error, TEXT("KUSAZURI_REVIEW_FAILED: %s"), *Reason);
    FPlatformMisc::RequestExitWithStatus(false, 1);
}

void AKusazuriReviewGameMode::BeginPlay()
{
    Super::BeginPlay();
    FParse::Value(FCommandLine::Get(), TEXT("KusazuriContract="), ContractPath);
    FParse::Value(FCommandLine::Get(), TEXT("KusazuriMode="), Mode);
    FParse::Value(FCommandLine::Get(), TEXT("KusazuriCount="), Count);
    FParse::Value(FCommandLine::Get(), TEXT("KusazuriCamera="), Camera);
    FParse::Value(FCommandLine::Get(), TEXT("KusazuriAnimation="), Animation);
    FParse::Value(FCommandLine::Get(), TEXT("KusazuriPose="), Pose);
    FParse::Value(FCommandLine::Get(), TEXT("KusazuriSeconds="), Seconds);
    FParse::Value(FCommandLine::Get(), TEXT("KusazuriOutput="), Output);
    FParse::Value(FCommandLine::Get(), TEXT("KusazuriScreenshot="), Screenshot);
    if (!FApp::CanEverRender()) { Fail(TEXT("Requires an actual rendered viewport; NullRHI is not a benchmark.")); return; }
    if (Mode != TEXT("existing") && Mode != TEXT("kusazuri")) { Fail(TEXT("Unknown comparison mode.")); return; }
    if (!TArray<FString>{TEXT("close"),TEXT("front"),TEXT("back"),TEXT("rear"),TEXT("left"),TEXT("right"),TEXT("detail"),TEXT("top"),TEXT("interior"),TEXT("tactical")}.Contains(Camera)) { Fail(TEXT("Unknown camera.")); return; }
    if (!TArray<FString>{TEXT("idle"),TEXT("walk"),TEXT("run"),TEXT("attack"),TEXT("none")}.Contains(Animation)) { Fail(TEXT("Unknown animation.")); return; }
    if (!TArray<FString>{TEXT("animation"),TEXT("neutral"),TEXT("arms-forward"),TEXT("arms-raised"),TEXT("turn"),TEXT("bend"),TEXT("head"),TEXT("bow"),TEXT("crouch"),TEXT("wide-step"),TEXT("knee-lift"),TEXT("wide-stance"),TEXT("combat-stance"),TEXT("hip-rotation"),TEXT("torso-turn")}.Contains(Pose)) { Fail(TEXT("Unknown inspection pose.")); return; }
    bClose = Camera != TEXT("tactical");
    if ((Count != 1 && Count != 100 && Count != 500) || bClose != (Count == 1) || (!bClose && Pose != TEXT("animation")))
    { Fail(TEXT("Close review requires count 1; static tactical probe requires count 100/500 and no diagnostic pose.")); return; }
    if (!FMath::IsFinite(Seconds) || Seconds < 0 || Seconds > 600 || (Seconds > 0 && (Output.IsEmpty() || Screenshot.IsEmpty()))) { Fail(TEXT("Timed runs need output and screenshot paths, duration at most 600 seconds.")); return; }
    if (!ReadReviewContract()) { Fail(TEXT("Missing/invalid native Manny review_contract in the Kusazuri manifest.")); return; }
    if (!CreateReview()) { Fail(TEXT("Required art, matching skeleton/reference bones, requested animation or player camera is missing.")); return; }
    GEngine->Exec(GetWorld(), TEXT("t.MaxFPS 0"));
    GEngine->Exec(GetWorld(), TEXT("r.VSync 0"));
    WarmupUntil = FPlatformTime::Seconds() + 3;
    if (!Screenshot.IsEmpty())
    {
        Screenshot = FPaths::ConvertRelativePathToFull(Screenshot);
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(Screenshot), true);
        IFileManager::Get().Delete(*Screenshot);
    }
    UE_LOG(LogTemp, Display, TEXT("KUSAZURI_REVIEW_READY mode=%s camera=%s bodies=%d helmets=%d armors=%d sode=%d"), *Mode, *Camera, RenderedBodies, RenderedHelmets, RenderedArmors, RenderedSode);
}

bool AKusazuriReviewGameMode::ReadReviewContract()
{
    if (ContractPath.IsEmpty()) ContractPath = FPaths::Combine(FPaths::ProjectDir(), TEXT("../SourceArt/Characters/Samurai/Kusazuri01/asset-manifest.json"));
    FString Text;
    TSharedPtr<FJsonObject> Manifest;
    if (!FFileHelper::LoadFileToString(Text, *ContractPath) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Manifest) || !Manifest.IsValid() || !Manifest->HasTypedField<EJson::Object>(TEXT("review_contract"))) return false;
    const auto Contract = Manifest->GetObjectField(TEXT("review_contract"));
    auto VectorField = [&](const TCHAR* Key, FVector& Value)
    {
        const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
        if (!Contract->TryGetArrayField(Key, Values) || Values->Num() != 3) return false;
        for (int32 Index = 0; Index < 3; ++Index)
            if (!(*Values)[Index]->TryGetNumber(Value[Index]) || !FMath::IsFinite(Value[Index])) return false;
        return true;
    };
    FVector Rotation;
    FString Turn, Bend;
    if (!Contract->TryGetNumberField(TEXT("body_component_yaw_degrees"), ComponentYaw) || !FMath::IsFinite(ComponentYaw) ||
        !VectorField(TEXT("helmet_offset_from_head_cm"), HelmetOffset) || !VectorField(TEXT("helmet_rotation_degrees"), Rotation) ||
        !VectorField(TEXT("helmet_scale"), HelmetScale) || HelmetScale.GetMin() <= 0 ||
        !Contract->TryGetStringField(TEXT("pose_turn_bone"), Turn) || !Contract->TryGetStringField(TEXT("pose_bend_bone"), Bend)) return false;
    HelmetRotation = FRotator(Rotation.X, Rotation.Y, Rotation.Z);
    TurnBone = FName(*Turn);
    BendBone = FName(*Bend);
    return !TurnBone.IsNone() && !BendBone.IsNone();
}

bool AKusazuriReviewGameMode::CreateCharacter(AActor* Owner, USceneComponent* Root, const FVector& Position)
{
    USkinnedMeshComponent* Body = nullptr;
    USkinnedMeshComponent* Armor = nullptr;
    UAnimSequence* Clip = nullptr;
    if (Pose != TEXT("animation"))
    {
        PoseBody = NewObject<UPoseableMeshComponent>(Owner);
        PoseBody->SetSkinnedAssetAndUpdate(BodyMesh);
        Body = PoseBody;
        if (ArmorMesh)
        {
            PoseArmor = NewObject<UPoseableMeshComponent>(Owner);
            PoseArmor->SetSkinnedAssetAndUpdate(ArmorMesh);
            Armor = PoseArmor;
        }
    }
    else
    {
        auto* Animated = NewObject<USkeletalMeshComponent>(Owner);
        Animated->SetSkeletalMesh(BodyMesh);
        Animated->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
        Body = Animated;
        if (Animation != TEXT("none"))
        {
            if (Animation == TEXT("idle")) Clip = KusazuriArt<UAnimSequence>(KusazuriMannyAnimations, TEXT("MM_Idle"));
            else if (Animation == TEXT("walk")) Clip = KusazuriArt<UAnimSequence>(KusazuriMannyAnimations, TEXT("Walk/MF_Unarmed_Walk_Fwd"));
            else if (Animation == TEXT("run")) Clip = KusazuriArt<UAnimSequence>(KusazuriMannyAnimations, TEXT("Jog/MF_Unarmed_Jog_Fwd"));
            else if (Animation == TEXT("attack")) Clip = KusazuriArt<UAnimSequence>(KusazuriMannyAnimations, TEXT("Attack/MM_Attack_01"));
            if (!Clip || Clip->GetSkeleton() != BodyMesh->GetSkeleton() || Clip->GetPlayLength() <= 0) return false;
            AnimationAsset = Clip->GetPathName();
            if (!ReviewClip)
            {
                // Preview only: retain the native clip and all non-root animation data.
                // Single-node extraction reads sequence flags, so lock a transient copy.
                ReviewClip = DuplicateObject<UAnimSequence>(Clip, GetTransientPackage());
                ReviewClip->SetFlags(RF_Transient);
                ReviewClip->ClearFlags(RF_Public | RF_Standalone);
                ReviewClip->bEnableRootMotion = false;
                ReviewClip->bForceRootLock = true;
                ReviewClip->RootMotionRootLock = ERootMotionRootLock::RefPose;
            }
            Clip = ReviewClip;
        }
        if (ArmorMesh)
        {
            auto* Follower = NewObject<USkeletalMeshComponent>(Owner);
            Follower->SetSkeletalMesh(ArmorMesh);
            Follower->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
            Follower->SetLeaderPoseComponent(Body, true, false);
            Armor = Follower;
        }
    }
    TArray<USkinnedMeshComponent*> CharacterSode;
    for (auto* Mesh : {SodeLeftMesh.Get(), SodeRightMesh.Get()})
    {
        if (!Mesh) continue;
        auto* Shoulder = NewObject<UPoseableMeshComponent>(Owner);
        Shoulder->SetSkinnedAssetAndUpdate(Mesh);
        PoseSode.Add(Shoulder);
        CharacterSode.Add(Shoulder);
        Sodes.Add(Shoulder);
        ++RenderedSode;
    }
    if (KusazuriMesh)
    {
        PoseKusazuri = NewObject<UPoseableMeshComponent>(Owner);
        PoseKusazuri->SetSkinnedAssetAndUpdate(KusazuriMesh);
        ++RenderedKusazuri;
    }
    TArray<USkinnedMeshComponent*> Components = {Body, Armor, PoseKusazuri.Get()};
    Components.Append(CharacterSode);
    for (auto* Component : Components)
    {
        if (!Component) continue;
        KusazuriConfigurePrimitive(Component);
        Owner->AddInstanceComponent(Component);
        Component->SetupAttachment(Root);
        Component->SetRelativeTransform(FTransform(FRotator(0,ComponentYaw,0), Position, FVector::OneVector));
        Component->RegisterComponent();
        AddTickPrerequisiteComponent(Component);
    }
    if (Clip)
    {
        auto* Animated = CastChecked<USkeletalMeshComponent>(Body);
        Animated->PlayAnimation(Clip, true);
        if (auto* Instance = Animated->GetSingleNodeInstance()) Instance->SetRootMotionMode(ERootMotionMode::IgnoreRootMotion);
    }
    Bodies.Add(Body);
    ++RenderedBodies;
    if (Armor) { Armors.Add(Armor); ++RenderedArmors; }
    if (HelmetMesh)
    {
        auto* Helmet = NewObject<UStaticMeshComponent>(Owner);
        Owner->AddInstanceComponent(Helmet);
        KusazuriConfigurePrimitive(Helmet);
        Helmet->SetStaticMesh(HelmetMesh);
        Helmet->SetupAttachment(Body, TEXT("head"));
        // Preserve the existing helmet geometry; fitted placement is measured against Manny.
        Helmet->SetRelativeTransform(HelmetRelative);
        Helmet->RegisterComponent();
        Helmets.Add(Helmet);
        ++RenderedHelmets;
    }
    return true;
}

bool AKusazuriReviewGameMode::CreateReview()
{
    auto* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto* Basic = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    BodyMesh = LoadObject<USkeletalMesh>(nullptr, KusazuriMannyAsset);
    if (!Cube || !Basic || !BodyMesh) return false;
    {
        HelmetMesh = KusazuriArt<UStaticMesh>(KusazuriExistingKabutoRoot, TEXT("SM_Kabuto01"));
        if (!HelmetMesh || HelmetMesh->GetStaticMaterials().IsEmpty()) return false;
    }
    {
        ArmorMesh = KusazuriArt<USkeletalMesh>(KusazuriExistingDoRoot, TEXT("SK_Do01"));
        ArmorStaticMesh = KusazuriArt<UStaticMesh>(KusazuriExistingDoRoot, TEXT("Review/SM_Do01"));
        if (!KusazuriValidArmor(ArmorMesh, BodyMesh) || !ArmorStaticMesh || ArmorStaticMesh->GetStaticMaterials().IsEmpty()) return false;
        for (const auto& Section : ArmorMesh->GetResourceForRendering()->LODRenderData[0].RenderSections)
            for (const auto Index : Section.BoneMap)
            {
                if (Index >= ArmorMesh->GetRefSkeleton().GetNum()) return false;
                ArmorValidationBones.AddUnique(ArmorMesh->GetRefSkeleton().GetBoneName(Index));
            }
        if (ArmorValidationBones.IsEmpty()) return false;
        const auto* StaticData = ArmorStaticMesh->GetRenderData();
        if (!StaticData || StaticData->LODResources.IsEmpty()) return false;
        for (const auto& Lod : StaticData->LODResources)
            if (Lod.GetNumTriangles() == 0 || Lod.Sections.IsEmpty()) return false;
    }
    {
        SodeLeftMesh = KusazuriArt<USkeletalMesh>(KusazuriExistingSodeRoot, TEXT("SK_Sode_L_01"));
        SodeRightMesh = KusazuriArt<USkeletalMesh>(KusazuriExistingSodeRoot, TEXT("SK_Sode_R_01"));
        if (!KusazuriValidArmor(SodeLeftMesh, BodyMesh) || !KusazuriValidArmor(SodeRightMesh, BodyMesh)) return false;
        // Native Manny faces +Y; after the unchanged -90 degree component yaw,
        // positive source X is anatomical left and negative source X is right.
        if (SodeLeftMesh->GetImportedBounds().Origin.X <= 0 || SodeRightMesh->GetImportedBounds().Origin.X >= 0) return false;
        for (auto* Mesh : {SodeLeftMesh.Get(), SodeRightMesh.Get()})
            for (const auto& Section : Mesh->GetResourceForRendering()->LODRenderData[0].RenderSections)
                for (const auto Index : Section.BoneMap)
                {
                    if (Index >= Mesh->GetRefSkeleton().GetNum()) return false;
                    SodeValidationBones.AddUnique(Mesh->GetRefSkeleton().GetBoneName(Index));
                }
        if (SodeValidationBones.IsEmpty()) return false;
    }
    if (Mode == TEXT("kusazuri"))
    {
        KusazuriMesh = KusazuriArt<USkeletalMesh>(KusazuriRoot, TEXT("SK_Kusazuri01"));
        KusazuriStaticMesh = KusazuriArt<UStaticMesh>(KusazuriRoot, TEXT("Review/SM_Kusazuri01"));
        if (!KusazuriValidArmor(KusazuriMesh, BodyMesh) || !KusazuriStaticMesh) return false;
    }
    if (!bClose)
    {
        MannequinStaticMesh = KusazuriArt<UStaticMesh>(KusazuriExistingDoRoot, TEXT("Review/SM_Manny"));
        SodeLeftStaticMesh = KusazuriArt<UStaticMesh>(KusazuriExistingSodeRoot, TEXT("Review/SM_Sode_L_01"));
        SodeRightStaticMesh = KusazuriArt<UStaticMesh>(KusazuriExistingSodeRoot, TEXT("Review/SM_Sode_R_01"));
        for (auto* Mesh : {MannequinStaticMesh.Get(), SodeLeftStaticMesh.Get(), SodeRightStaticMesh.Get()})
            if (!Mesh || !Mesh->GetRenderData() || Mesh->GetRenderData()->LODResources.IsEmpty()) return false;
    }
    const auto& Ref = BodyMesh->GetRefSkeleton();
    for (const auto* Bone : {TEXT("pelvis"), TEXT("spine_01"), TEXT("thigh_l"), TEXT("thigh_r"),
        TEXT("calf_l"), TEXT("calf_r"), TEXT("thigh_twist_01_l"), TEXT("thigh_twist_01_r"),
        TEXT("thigh_twist_02_l"), TEXT("thigh_twist_02_r")})
        if (Ref.FindBoneIndex(Bone) == INDEX_NONE) return false;
    const int32 HeadIndex = Ref.FindBoneIndex(TEXT("head"));
    const int32 RootIndex = Ref.FindBoneIndex(TEXT("root"));
    if (HeadIndex == INDEX_NONE || RootIndex != 0) return false;
    BodyReferenceComponentSpace.SetNum(Ref.GetNum());
    for (int32 Index = 0; Index < Ref.GetNum(); ++Index)
    {
        const int32 Parent = Ref.GetParentIndex(Index);
        BodyReferenceComponentSpace[Index] = Parent == INDEX_NONE ? Ref.GetRefBonePose()[Index] :
            Ref.GetRefBonePose()[Index]*BodyReferenceComponentSpace[Parent];
    }
    for (const auto* Name : {TEXT("spine_05"),TEXT("upperarm_l"),TEXT("upperarm_r"),TEXT("lowerarm_l"),TEXT("lowerarm_r")})
        if (Ref.FindBoneIndex(Name) == INDEX_NONE) return false;
    RootReference = Ref.GetRefBonePose()[RootIndex];
    HeadReference = Ref.GetRefBonePose()[HeadIndex];
    for (int32 Parent = Ref.GetParentIndex(HeadIndex); Parent != INDEX_NONE; Parent = Ref.GetParentIndex(Parent))
        HeadReference = HeadReference * Ref.GetRefBonePose()[Parent];
    if (HeadReference.ContainsNaN() || HeadReference.GetScale3D().GetAbsMin() < SMALL_NUMBER ||
        Ref.FindBoneIndex(TurnBone) == INDEX_NONE || Ref.FindBoneIndex(BendBone) == INDEX_NONE) return false;
    HelmetAtReference = FTransform(HelmetRotation, HeadReference.GetLocation()+HelmetOffset, HelmetScale);
    HelmetRelative = HelmetAtReference.GetRelativeTransform(HeadReference);

    auto* Ground = GetWorld()->SpawnActor<AStaticMeshActor>(FVector(0,0,-8), FRotator::ZeroRotator);
    auto* GroundMesh = Ground->GetStaticMeshComponent();
    KusazuriConfigurePrimitive(GroundMesh);
    GroundMesh->SetStaticMesh(Cube);
    GroundMesh->SetWorldScale3D(FVector(5000,5000,.15));
    GroundMesh->SetMaterial(0, Basic);
    if (auto* Mat = GroundMesh->CreateDynamicMaterialInstance(0)) Mat->SetVectorParameterValue(TEXT("Color"), FLinearColor(.22,.24,.22));
    auto* Light = GetWorld()->SpawnActor<ADirectionalLight>(FVector(0,0,1000), FRotator(-48,155,0));
    Light->SetMobility(EComponentMobility::Movable);
    Light->GetLightComponent()->SetIntensity(bClose ? 1 : 4);
    if (auto* Directional = Cast<UDirectionalLightComponent>(Light->GetLightComponent()))
    {
        Directional->SetDynamicShadowDistanceMovableLight(bClose ? 1500 : 45000);
        Directional->SetDynamicShadowCascades(4);
    }
    auto* Sky = GetWorld()->SpawnActor<ASkyLight>();
    Sky->GetLightComponent()->SetMobility(EComponentMobility::Movable);
    Sky->GetLightComponent()->SourceType = SLS_SpecifiedCubemap;
    Sky->GetLightComponent()->SetCubemap(LoadObject<UTextureCube>(nullptr, TEXT("/Engine/MapTemplates/Sky/DaylightAmbientCubemap.DaylightAmbientCubemap")));
    Sky->GetLightComponent()->SetIntensity(1.2);
    if (bClose)
        for (const auto& Position : {FVector(210,-150,230), FVector(100,200,200)})
        {
            auto* Lamp = GetWorld()->SpawnActor<ARectLight>(Position, (FVector(0,0,145)-Position).Rotation());
            Lamp->SetMobility(EComponentMobility::Movable);
            auto* Rect = Cast<URectLightComponent>(Lamp->GetLightComponent());
            Rect->SetIntensity(Position.Y < 0 ? 3500 : 1000);
            if (Position.Y > 0) Rect->SetCastShadows(false);
            Rect->SetAttenuationRadius(900);
            Rect->SetSourceWidth(160);
            Rect->SetSourceHeight(160);
        }
    auto* Owner = GetWorld()->SpawnActor<AActor>();
    auto* Root = NewObject<USceneComponent>(Owner);
    Owner->SetRootComponent(Root);
    Owner->AddInstanceComponent(Root);
    Root->RegisterComponent();
    if (bClose)
    {
        if (!CreateCharacter(Owner, Root, FVector::ZeroVector)) return false;
        if (PoseBody) UpdateInspectionPose();
        if (!UpdateSodeSuspension() || !UpdateKusazuriHinges()) return false;
    }
    else
    {
        auto Instances = [&](UStaticMesh* Mesh)
        {
            auto* Component = NewObject<UInstancedStaticMeshComponent>(Owner);
            Owner->AddInstanceComponent(Component);
            KusazuriConfigurePrimitive(Component);
            Component->SetupAttachment(Root);
            Component->SetStaticMesh(Mesh);
            Component->RegisterComponent();
            ++InstanceComponents;
            return Component;
        };
        const int32 FormationCount = Count/100;
        for (int32 Formation = 0; Formation < FormationCount; ++Formation)
        {
            auto* BodyInstances = Instances(MannequinStaticMesh);
            auto* HelmetInstances = Instances(HelmetMesh);
            auto* ArmorInstances = Instances(ArmorStaticMesh);
            auto* LeftInstances = Instances(SodeLeftStaticMesh);
            auto* RightInstances = Instances(SodeRightStaticMesh);
            auto* WaistInstances = KusazuriStaticMesh ? Instances(KusazuriStaticMesh) : nullptr;
            const FVector FormationPosition((Formation-(FormationCount-1)*.5)*1400,0,0);
            for (int32 Slot = 0; Slot < 100; ++Slot)
            {
                const FVector Position = FormationPosition+FVector((Slot%10-4.5)*110,(Slot/10-4.5)*110,0);
                const FTransform Transform(FRotator(0,ComponentYaw,0),Position,FVector::OneVector);
                BodyInstances->AddInstance(Transform); ++RenderedBodies;
                HelmetInstances->AddInstance(HelmetAtReference*Transform); ++RenderedHelmets;
                ArmorInstances->AddInstance(Transform); ++RenderedArmors;
                LeftInstances->AddInstance(Transform); RightInstances->AddInstance(Transform); RenderedSode += 2;
                if (WaistInstances) { WaistInstances->AddInstance(Transform); ++RenderedKusazuri; }
            }
        }
    }
    FVector Focus = FVector::ZeroVector;
    const double Yaw = Camera == TEXT("front") ? 0 : Camera == TEXT("left") ? -90 : Camera == TEXT("right") ? 90 : Camera == TEXT("back") ? 180 : Camera == TEXT("rear") ? 145 : bClose ? 32 : 90;
    // Keep the low waist view above the review floor at its fitted distance.
    CameraElevation = Camera == TEXT("top") ? 78 : Camera == TEXT("interior") ? -15 : bClose ? 15 : 60;
    const FVector Direction = FRotator(CameraElevation, Yaw, 0).Vector();
    CameraDistance = 11000;
    Focus.Z = 90;
    if (bClose)
    {
        const FTransform BodyTransform(FRotator(0,ComponentYaw,0));
        // Use the same waist-to-crest envelope in every comparison mode.
        // Manny's full arm/leg bounds otherwise push the torso too far away.
        auto* FramingArmor = KusazuriArt<USkeletalMesh>(KusazuriExistingDoRoot, TEXT("SK_Do01"));
        auto* FramingHelmet = KusazuriArt<UStaticMesh>(KusazuriExistingKabutoRoot, TEXT("SM_Kabuto01"));
        if (!FramingArmor || !FramingHelmet) return false;
        FBox Bounds = FramingArmor->GetImportedBounds().GetBox().TransformBy(BodyTransform);
        Bounds += FramingHelmet->GetBoundingBox().TransformBy(HelmetAtReference*BodyTransform);
        for (const auto* Name : {TEXT("SK_Sode_L_01"), TEXT("SK_Sode_R_01")})
        {
            auto* FramingSode = KusazuriArt<USkeletalMesh>(KusazuriExistingSodeRoot, Name);
            if (!FramingSode) return false;
            Bounds += FramingSode->GetImportedBounds().GetBox().TransformBy(BodyTransform);
        }
        auto* FramingWaist = KusazuriArt<USkeletalMesh>(KusazuriRoot, TEXT("SK_Kusazuri01"));
        if (!FramingWaist) return false;
        Bounds += FramingWaist->GetImportedBounds().GetBox().TransformBy(BodyTransform);
        if (Camera == TEXT("detail") || Camera == TEXT("top") || Camera == TEXT("interior"))
            Bounds = FramingWaist->GetImportedBounds().GetBox().TransformBy(BodyTransform);
        Bounds = Bounds.ExpandBy(FVector(4,4,3));
        Focus = Bounds.GetCenter();
        const FVector Extent = Bounds.GetExtent();
        const FVector Right = FRotator(0,Yaw+90,0).Vector();
        const FVector Up = FVector::CrossProduct(Direction,Right).GetSafeNormal();
        const double TanHorizontal = FMath::Tan(FMath::DegreesToRadians(20.0));
        const double Width = FVector::DotProduct(Extent,Right.GetAbs());
        const double Height = FVector::DotProduct(Extent,Up.GetAbs());
        CameraDistance = FVector::DotProduct(Extent,Direction.GetAbs()) + 1.05*FMath::Max(Width/TanHorizontal,Height/(TanHorizontal*9.0/16.0));
    }
    const FVector Offset = Direction*CameraDistance;
    auto* View = GetWorld()->SpawnActor<ACameraActor>(Focus+Offset, (-Offset).Rotation());
    View->GetCameraComponent()->SetFieldOfView(bClose ? 40 : 55);
    auto* Player = GetWorld()->GetFirstPlayerController();
    if (!Player) return false;
    Player->SetViewTarget(View);
    Player->bShowMouseCursor = false;
    return true;
}

void AKusazuriReviewGameMode::UpdateInspectionPose()
{
    if (!PoseBody) return;
    const auto& Ref = BodyMesh->GetRefSkeleton();
    const FQuat Facing = FRotator(0,ComponentYaw,0).Quaternion();
    const FVector Forward = Facing.Inverse().RotateVector(FVector::ForwardVector);
    const FVector Left = Facing.Inverse().RotateVector(-FVector::RightVector);
    TArray<FTransform> Composed;
    Composed.SetNum(Ref.GetNum());
    for (int32 Index = 0; Index < Ref.GetNum(); ++Index)
    {
        const FName Name = Ref.GetBoneName(Index);
        const int32 Parent = Ref.GetParentIndex(Index);
        FTransform Transform = Ref.GetRefBonePose()[Index];
        if (Parent != INDEX_NONE) Transform = Transform * Composed[Parent];
        FVector Axis = FVector::UpVector;
        double Degrees = 0;
        if ((Pose == TEXT("arms-forward") || Pose == TEXT("arms-raised") || Pose == TEXT("bow")) && (Name == TEXT("upperarm_l") || Name == TEXT("upperarm_r")))
        {
            const bool bLeft = Name == TEXT("upperarm_l");
            const int32 Elbow = Ref.FindBoneIndex(bLeft ? TEXT("lowerarm_l") : TEXT("lowerarm_r"));
            if (Elbow != INDEX_NONE)
            {
                const FVector Rest = ((Ref.GetRefBonePose()[Elbow]*Transform).GetLocation()-Transform.GetLocation()).GetSafeNormal();
                const FVector Target = (Pose == TEXT("bow") ? (bLeft ? KusazuriHinges::ReflectY(FVector(.18,-1,.08)) : KusazuriHinges::ReflectY(FVector(-.75,.6,.12))) : Pose == TEXT("arms-forward") ? Left*(bLeft ? .12 : -.12)+Forward-FVector::UpVector*.1 : Left*(bLeft ? 1 : -1)+FVector::UpVector*.25).GetSafeNormal();
                Transform.SetRotation(FQuat::FindBetweenNormals(Rest,Target)*Transform.GetRotation());
            }
        }
        if (Pose == TEXT("bow") && Name == TEXT("lowerarm_r"))
        {
            const int32 Wrist = Ref.FindBoneIndex(TEXT("hand_r"));
            if (Wrist != INDEX_NONE)
            {
                const FVector Rest = ((Ref.GetRefBonePose()[Wrist]*Transform).GetLocation()-Transform.GetLocation()).GetSafeNormal();
                const FVector Target = (FVector(0,4,157)-Transform.GetLocation()).GetSafeNormal();
                Transform.SetRotation(FQuat::FindBetweenNormals(Rest,Target)*Transform.GetRotation());
            }
        }
        const bool bCombatPose = Pose == TEXT("combat-stance") || Pose == TEXT("bow");
        if (Name == TEXT("pelvis"))
        {
            if (Pose == TEXT("crouch")) Transform.AddToTranslation(FVector(0,0,-14));
            if (Pose == TEXT("wide-stance")) Transform.AddToTranslation(FVector(0,0,-7));
            if (bCombatPose) Transform.AddToTranslation(FVector(0,0,-5));
            if (Pose == TEXT("hip-rotation"))
                Transform.SetRotation(FQuat(FVector::YAxisVector,FMath::DegreesToRadians(12.0))*
                    FQuat(FVector::ZAxisVector,FMath::DegreesToRadians(-35.0))*Transform.GetRotation());
        }
        const bool bLeftLeg = Name == TEXT("thigh_l") || Name == TEXT("calf_l");
        const bool bThigh = Name == TEXT("thigh_l") || Name == TEXT("thigh_r");
        const bool bCalf = Name == TEXT("calf_l") || Name == TEXT("calf_r");
        if (bThigh || bCalf)
        {
            const FName Child = bThigh ? (bLeftLeg ? TEXT("calf_l") : TEXT("calf_r")) :
                (bLeftLeg ? TEXT("foot_l") : TEXT("foot_r"));
            const int32 ChildIndex = Ref.FindBoneIndex(Child);
            FVector Target = FVector::ZeroVector;
            const double Sign = bLeftLeg ? 1 : -1;
            if (Pose == TEXT("crouch")) Target = bThigh ? FVector(Sign*.15,-.60,-.80) : FVector(Sign*.06,.58,-.82);
            if (Pose == TEXT("wide-stance")) Target = bThigh ? FVector(Sign*.52,-.10,-.85) : FVector(Sign*.10,.10,-.99);
            if (Pose == TEXT("wide-step")) Target = bThigh ? (bLeftLeg ? FVector(.12,-.80,-.59) : FVector(-.10,.48,-.87)) :
                (bLeftLeg ? FVector(.02,-.08,-1) : FVector(-.02,.35,-.94));
            if (Pose == TEXT("knee-lift") && bLeftLeg) Target = bThigh ? FVector(.08,-.98,-.15) : FVector(0,.10,-.99);
            if (bCombatPose) Target = bThigh ? (bLeftLeg ? FVector(.30,-.48,-.83) : FVector(-.40,.18,-.90)) : FVector(Sign*.08,.35,-.94);
            if (ChildIndex != INDEX_NONE && !Target.IsNearlyZero())
            {
                const FVector Rest = ((Ref.GetRefBonePose()[ChildIndex]*Transform).GetLocation()-Transform.GetLocation()).GetSafeNormal();
                Transform.SetRotation(FQuat::FindBetweenNormals(Rest,KusazuriHinges::ReflectY(Target).GetSafeNormal())*Transform.GetRotation());
            }
        }
        if (Name == TEXT("spine_01"))
        {
            if (Pose == TEXT("crouch")) { Axis = FVector::XAxisVector; Degrees = -12; }
            if (Pose == TEXT("torso-turn")) Degrees = -35;
            if (bCombatPose) Degrees = 12;
        }
        if (Pose == TEXT("turn") && Name == TurnBone) Degrees = 25;
        if (Pose == TEXT("bend") && Name == BendBone) { Axis = FVector::CrossProduct(Forward,FVector::UpVector).GetSafeNormal(); Degrees = -20; }
        if (Pose == TEXT("head") && Name == TEXT("head")) Degrees = 30*FMath::Sin(GetWorld()->GetTimeSeconds()*1.1);
        Transform.SetRotation(FQuat(Axis, FMath::DegreesToRadians(Degrees))*Transform.GetRotation());
        Composed[Index] = Transform;
        PoseBody->SetBoneTransformByName(Name, Transform, EBoneSpaces::ComponentSpace);
        if (PoseArmor && ArmorMesh->GetRefSkeleton().FindBoneIndex(Name) != INDEX_NONE)
            PoseArmor->SetBoneTransformByName(Name, Transform, EBoneSpaces::ComponentSpace);
    }
    PoseBody->RefreshBoneTransforms();
    if (PoseArmor) PoseArmor->RefreshBoneTransforms();
}

bool AKusazuriReviewGameMode::UpdateSodeSuspension()
{
    if (PoseSode.IsEmpty()) return true;
    if (PoseSode.Num() != 2 || Bodies.Num() != 1) return false;
    auto* Body = Bodies[0].Get();
    const auto& Ref = BodyMesh->GetRefSkeleton();
    const int32 TorsoIndex = Ref.FindBoneIndex(TEXT("spine_05"));
    const FTransform Torso = Body->GetSocketTransform(TEXT("spine_05"),RTS_Component);
    for (int32 Side = 0; Side < 2; ++Side)
    {
        auto* Shoulder = PoseSode[Side].Get();
        const FName UpperName(Side == 0 ? TEXT("upperarm_l") : TEXT("upperarm_r"));
        const FName LowerName(Side == 0 ? TEXT("lowerarm_l") : TEXT("lowerarm_r"));
        const int32 UpperIndex = Ref.FindBoneIndex(UpperName), LowerIndex = Ref.FindBoneIndex(LowerName);
        // Copy the COMPLETE local pose first, then update component matrices.
        // Interleaving a parent override with child pose copies causes stale
        // parent-space conversions and undoes the intended rigid suspension.
        if (auto* Animated = Cast<USkeletalMeshComponent>(Body)) Shoulder->CopyPoseFromSkeletalComponent(Animated);
        else if (PoseBody)
        {
            if (Shoulder->BoneSpaceTransforms.Num() != PoseBody->GetBoneSpaceTransforms().Num()) return false;
            Shoulder->BoneSpaceTransforms = PoseBody->GetBoneSpaceTransforms();
            Shoulder->MarkRefreshTransformDirty();
        }
        else return false;
        Shoulder->RefreshBoneTransforms();
        const FTransform Upper = Body->GetSocketTransform(UpperName,RTS_Component);
        const FTransform Lower = Body->GetSocketTransform(LowerName,RTS_Component);
        if (!KusazuriSodeSuspensionTarget(BodyReferenceComponentSpace[TorsoIndex], BodyReferenceComponentSpace[UpperIndex],
            BodyReferenceComponentSpace[LowerIndex], Torso, Upper, Lower, Side == 0 ? 1.0 : -1.0,
            SodeTarget[Side], SodeOpening[Side], SodeLiftClearance[Side], SodeDirection[Side])) return false;
        Shoulder->SetBoneTransformByName(UpperName,SodeTarget[Side],EBoneSpaces::ComponentSpace);
        Shoulder->RefreshBoneTransforms();
        MaxSodeOpening[Side] = FMath::Max(MaxSodeOpening[Side],SodeOpening[Side]);
        MaxSodeLiftClearance[Side] = FMath::Max(MaxSodeLiftClearance[Side],SodeLiftClearance[Side]);
        MaxSodeBodyRotationDifference[Side] = FMath::Max(MaxSodeBodyRotationDifference[Side],
            FMath::RadiansToDegrees(SodeTarget[Side].GetRotation().AngularDistance(Upper.GetRotation())));
    }
    ++SuspensionSamples;
    return true;
}

bool AKusazuriReviewGameMode::UpdateKusazuriHinges()
{
    if (!PoseKusazuri) return true;
    if (Bodies.Num() != 1 || !KusazuriMesh) return false;
    auto* Body = Bodies[0].Get();
    if (auto* Animated = Cast<USkeletalMeshComponent>(Body)) PoseKusazuri->CopyPoseFromSkeletalComponent(Animated);
    else if (PoseBody)
    {
        if (PoseKusazuri->BoneSpaceTransforms.Num() != PoseBody->GetBoneSpaceTransforms().Num()) return false;
        PoseKusazuri->BoneSpaceTransforms = PoseBody->GetBoneSpaceTransforms();
        PoseKusazuri->MarkRefreshTransformDirty();
    }
    else return false;
    PoseKusazuri->RefreshBoneTransforms();
    const auto& Ref = BodyMesh->GetRefSkeleton();
    const int32 PelvisIndex = Ref.FindBoneIndex(TEXT("pelvis"));
    const FTransform Pelvis = Body->GetSocketTransform(TEXT("pelvis"),RTS_Component);
    const FVector LeftThigh = Body->GetSocketTransform(TEXT("thigh_l"),RTS_Component).GetLocation();
    const FVector LeftCalf = Body->GetSocketTransform(TEXT("calf_l"),RTS_Component).GetLocation();
    const FVector RightThigh = Body->GetSocketTransform(TEXT("thigh_r"),RTS_Component).GetLocation();
    const FVector RightCalf = Body->GetSocketTransform(TEXT("calf_r"),RTS_Component).GetLocation();
    TArray<TPair<int32,int32>> Ordered;
    for (int32 Index=0; Index<7; ++Index)
    {
        const int32 BoneIndex = Ref.FindBoneIndex(KusazuriHinges::Panels[Index].Bone);
        if (BoneIndex == INDEX_NONE || !KusazuriHinges::Target(Index,BodyReferenceComponentSpace[BoneIndex],
            BodyReferenceComponentSpace[PelvisIndex],Pelvis,LeftThigh,LeftCalf,RightThigh,RightCalf,
            PanelTargets[Index],PanelAngles[Index])) return false;
        MaxPanelAngles[Index] = FMath::Max(MaxPanelAngles[Index],PanelAngles[Index]);
        Ordered.Add({BoneIndex,Index});
    }
    // Native hierarchy order ensures parent edits cannot undo independent twist
    // targets. Refresh before every child conversion to local bone space.
    Ordered.Sort([](const auto& A, const auto& B) { return A.Key < B.Key; });
    for (const auto& Entry : Ordered)
    {
        PoseKusazuri->SetBoneTransformByName(KusazuriHinges::Panels[Entry.Value].Bone,
            PanelTargets[Entry.Value],EBoneSpaces::ComponentSpace);
        PoseKusazuri->RefreshBoneTransforms();
    }
    for (int32 Index=0; Index<7; ++Index)
    {
        const FTransform Actual = PoseKusazuri->GetSocketTransform(KusazuriHinges::Panels[Index].Bone,RTS_Component);
        MaxKusazuriBonePositionError = FMath::Max(MaxKusazuriBonePositionError,FVector::Distance(Actual.GetLocation(),PanelTargets[Index].GetLocation()));
        MaxKusazuriBoneRotationError = FMath::Max(MaxKusazuriBoneRotationError,
            FMath::RadiansToDegrees(Actual.GetRotation().AngularDistance(PanelTargets[Index].GetRotation())));
    }
    const FTransform Belt = PoseKusazuri->GetSocketTransform(TEXT("pelvis"),RTS_Component);
    MaxKusazuriBonePositionError = FMath::Max(MaxKusazuriBonePositionError,FVector::Distance(Belt.GetLocation(),Pelvis.GetLocation()));
    MaxWorldScaleError = FMath::Max(MaxWorldScaleError,(PoseKusazuri->GetComponentScale()-FVector::OneVector).GetAbsMax());
    ++KusazuriControllerSamples;
    return true;
}

void AKusazuriReviewGameMode::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (bFailed || bFinished) return;
    const double Now = FPlatformTime::Seconds();
    UpdateInspectionPose();
    if (!UpdateSodeSuspension()) { Fail(TEXT("Invalid Sode suspension pose.")); return; }
    if (!UpdateKusazuriHinges()) { Fail(TEXT("Invalid Kusazuri panel pose.")); return; }
    if (!Bodies.IsEmpty() && Pose == TEXT("animation") && Animation != TEXT("none"))
        if (const auto* Animated = Cast<USkeletalMeshComponent>(Bodies[0].Get()))
        {
            const double Position = Animated->GetPosition();
            MinAnimationPosition = FMath::Min(MinAnimationPosition, Position);
            MaxAnimationPosition = FMath::Max(MaxAnimationPosition, Position);
        }
    for (int32 Index = 0; Index < Bodies.Num(); ++Index)
    {
        auto* Body = Bodies[Index].Get();
        const FTransform RootPose = Body->GetSocketTransform(TEXT("root"), RTS_Component);
        MaxRootPositionError = FMath::Max(MaxRootPositionError, FVector::Distance(RootPose.GetLocation(),RootReference.GetLocation()));
        MaxRootRotationError = FMath::Max(MaxRootRotationError, FMath::RadiansToDegrees(RootPose.GetRotation().AngularDistance(RootReference.GetRotation())));
        MaxWorldScaleError = FMath::Max(MaxWorldScaleError, (Body->GetComponentScale()-FVector::OneVector).GetAbsMax());
        if (Helmets.IsValidIndex(Index))
        {
            auto* Helmet = Helmets[Index].Get();
            MaxAttachmentPositionError = FMath::Max(MaxAttachmentPositionError, FVector::Distance(Helmet->GetComponentLocation(), (HelmetRelative*Body->GetSocketTransform(TEXT("head"))).GetLocation()));
            MaxWorldScaleError = FMath::Max(MaxWorldScaleError, (Helmet->GetComponentScale()-HelmetScale).GetAbsMax());
        }
        if (Armors.IsValidIndex(Index))
        {
            auto* Armor = Armors[Index].Get();
            MaxWorldScaleError = FMath::Max(MaxWorldScaleError, (Armor->GetComponentScale()-FVector::OneVector).GetAbsMax());
            for (const FName Bone : ArmorValidationBones)
            {
                const auto A = Armor->GetSocketTransform(Bone), B = Body->GetSocketTransform(Bone);
                MaxArmorBonePositionError = FMath::Max(MaxArmorBonePositionError, FVector::Distance(A.GetLocation(), B.GetLocation()));
                MaxArmorBoneRotationError = FMath::Max(MaxArmorBoneRotationError, FMath::RadiansToDegrees(A.GetRotation().AngularDistance(B.GetRotation())));
            }
        }
    }
    const auto& BodyRef = BodyMesh->GetRefSkeleton();
    for (int32 Side = 0; Side < Sodes.Num(); ++Side)
    {
        auto* Shoulder = Sodes[Side].Get();
        const FName UpperName(Side == 0 ? TEXT("upperarm_l") : TEXT("upperarm_r"));
        const int32 UpperIndex = BodyRef.FindBoneIndex(UpperName);
        const FTransform BodyUpper = Bodies[0]->GetSocketTransform(UpperName,RTS_Component);
        MaxWorldScaleError = FMath::Max(MaxWorldScaleError, (Shoulder->GetComponentScale()-FVector::OneVector).GetAbsMax());
        for (const FName Bone : SodeValidationBones)
        {
            FTransform Expected = Bodies[0]->GetSocketTransform(Bone,RTS_Component);
            for (int32 Index = BodyRef.FindBoneIndex(Bone); Index != INDEX_NONE; Index = BodyRef.GetParentIndex(Index))
                if (Index == UpperIndex)
                {
                    Expected = Expected.GetRelativeTransform(BodyUpper)*SodeTarget[Side];
                    break;
                }
            const FTransform Actual = Shoulder->GetSocketTransform(Bone,RTS_Component);
            if (Actual.ContainsNaN() || Expected.ContainsNaN()) { Fail(TEXT("Nonfinite Sode bone pose.")); return; }
            MaxSodeBonePositionError = FMath::Max(MaxSodeBonePositionError, FVector::Distance(Actual.GetLocation(), Expected.GetLocation()));
            MaxSodeBoneRotationError = FMath::Max(MaxSodeBoneRotationError, FMath::RadiansToDegrees(Actual.GetRotation().AngularDistance(Expected.GetRotation())));
        }
    }
    if (Now < WarmupUntil) return;
    if (bSamplingComplete)
    {
        if (!FScreenshotRequest::IsScreenshotRequested() && IFileManager::Get().FileSize(*Screenshot) > 0) CompleteReview();
        else if (Now-ScreenshotRequestedAt > 15) Fail(TEXT("Timed out waiting for rendered screenshot."));
        return;
    }
    if (Seconds == 0) return;
    if (LastFrame == 0) { LastFrame = Now; return; }
    const double FrameMs = (Now-LastFrame)*1000;
    LastFrame = Now;
    FrameTimes.Add(FrameMs);
    CaptureElapsed += FrameMs/1000;
    GameTimes.Add(GGameThreadTime ? FPlatformTime::ToMilliseconds(GGameThreadTime) : 0);
    RenderTimes.Add(GRenderThreadTime ? FPlatformTime::ToMilliseconds(GRenderThreadTime) : 0);
    const uint32 GpuCycles = RHIGetGPUFrameCycles();
    GpuTimes.Add(GpuCycles ? FPlatformTime::ToMilliseconds(GpuCycles) : 0);
    DrawCalls.Add(GNumDrawCallsRHI[0]);
    Primitives.Add(GNumPrimitivesDrawnRHI[0]);
    PeakMemory = FMath::Max(PeakMemory, FPlatformMemory::GetStats().UsedPhysical);
    if (CaptureElapsed >= Seconds)
    {
        bSamplingComplete = true;
        ScreenshotRequestedAt = Now;
        FScreenshotRequest::RequestScreenshot(Screenshot, false, false);
    }
}

void AKusazuriReviewGameMode::CompleteReview()
{
    bFinished = true;
    auto Json = MakeShared<FJsonObject>();
    int32 Width = 0, Height = 0;
    GetWorld()->GetFirstPlayerController()->GetViewportSize(Width, Height);
    const bool bScreenshot = IFileManager::Get().FileSize(*Screenshot) > 0;
    const bool bAnimationRequired = !Bodies.IsEmpty() && Pose == TEXT("animation") && Animation != TEXT("none");
    const bool bAnimationAdvanced = MaxAnimationPosition-MinAnimationPosition > .001;
    const bool bValid = (!bAnimationRequired || bAnimationAdvanced) && !FrameTimes.IsEmpty() && Width > 0 && Height > 0 && bScreenshot &&
        RenderedBodies == Count && RenderedHelmets == Count && RenderedArmors == Count && RenderedSode == 2*Count &&
        RenderedKusazuri == (Mode == TEXT("kusazuri") ? Count : 0) &&
        MaxKusazuriBonePositionError < .1 && MaxKusazuriBoneRotationError < .1 && MaxAttachmentPositionError < .1 &&
        MaxArmorBonePositionError < .1 && MaxArmorBoneRotationError < .1 && MaxSodeBonePositionError < .1 && MaxSodeBoneRotationError < .1 && MaxWorldScaleError < .001 &&
        MaxRootPositionError < .1 && MaxRootRotationError < .1;
    Json->SetBoolField(TEXT("rendered"), true);
    Json->SetBoolField(TEXT("validated"), bValid);
    Json->SetStringField(TEXT("mode"), Mode);
    Json->SetStringField(TEXT("camera"), Camera);
    Json->SetStringField(TEXT("pose"), Pose);
    Json->SetStringField(TEXT("requested_animation"), Animation);
    Json->SetStringField(TEXT("animation_asset"), AnimationAsset);
    Json->SetStringField(TEXT("root_motion_handling"), ReviewClip ? TEXT("One transient native-clip duplicate shared by review bodies; force root lock to reference pose, no locomotion applied; saved Epic clip unchanged") : TEXT("Reference pose; no locomotion animation"));
    Json->SetNumberField(TEXT("max_root_position_error_cm"), MaxRootPositionError);
    Json->SetNumberField(TEXT("max_root_rotation_error_degrees"), MaxRootRotationError);
    Json->SetBoolField(TEXT("animation_advanced"), bAnimationAdvanced);
    if (bAnimationRequired) Json->SetNumberField(TEXT("observed_animation_position_range_seconds"), MaxAnimationPosition-MinAnimationPosition);
    else Json->SetField(TEXT("observed_animation_position_range_seconds"), MakeShared<FJsonValueNull>());
    Json->SetNumberField(TEXT("animation_play_rate"), 1.0);
    Json->SetStringField(TEXT("animation"), !bClose ? TEXT("static instances") : Pose == TEXT("animation") ? Animation : TEXT("component-space inspection pose"));
    Json->SetStringField(TEXT("crowd_representation"), bClose ? TEXT("single skeletal/poseable fixture") : TEXT("static"));
    Json->SetStringField(TEXT("armor_pose_method"), Armors.IsEmpty() ? TEXT("absent") : PoseArmor ? TEXT("copied component-space body bones") : TEXT("SetLeaderPoseComponent(body)"));
    Json->SetStringField(TEXT("engine"), FEngineVersion::Current().ToString());
    Json->SetStringField(TEXT("platform"), ANSI_TO_TCHAR(FPlatformProperties::IniPlatformName()));
    Json->SetStringField(TEXT("rhi"), GDynamicRHI ? GDynamicRHI->GetName() : TEXT("unavailable"));
    Json->SetStringField(TEXT("build"), TEXT("Development editor game; opt-in isolated Kusazuri art review/static incremental cost probe"));
    Json->SetNumberField(TEXT("requested_count"), Count);
    Json->SetNumberField(TEXT("rendered_bodies"), RenderedBodies);
    Json->SetNumberField(TEXT("rendered_helmets"), RenderedHelmets);
    Json->SetNumberField(TEXT("rendered_armors"), RenderedArmors);
    Json->SetNumberField(TEXT("rendered_sode_left"), SodeLeftMesh ? Count : 0);
    Json->SetNumberField(TEXT("rendered_sode_right"), SodeRightMesh ? Count : 0);
    Json->SetNumberField(TEXT("rendered_sode"), RenderedSode);
    Json->SetNumberField(TEXT("skeletal_components"), Bodies.Num()+Armors.Num()+Sodes.Num()+(PoseKusazuri ? 1 : 0));
    Json->SetNumberField(TEXT("camera_distance_cm"), CameraDistance);
    Json->SetNumberField(TEXT("camera_horizontal_fov"), bClose ? 40 : 55);
    Json->SetNumberField(TEXT("camera_elevation_degrees"), CameraElevation);
    Json->SetBoolField(TEXT("body_helmet_armor_cast_shadows"), true);
    Json->SetNumberField(TEXT("warmup_seconds"), 3);
    Json->SetNumberField(TEXT("capture_seconds"), CaptureElapsed);
    Json->SetNumberField(TEXT("frames"), FrameTimes.Num());
    Json->SetNumberField(TEXT("median_fps"), FrameTimes.IsEmpty() ? 0 : 1000/KusazuriPercentile(FrameTimes,.5));
    Json->SetNumberField(TEXT("interval_fps"), CaptureElapsed > 0 ? FrameTimes.Num()/CaptureElapsed : 0);
    Json->SetNumberField(TEXT("peak_process_physical_bytes"), double(PeakMemory));
    Json->SetNumberField(TEXT("max_attachment_position_error_cm"), MaxAttachmentPositionError);
    Json->SetNumberField(TEXT("max_armor_bone_position_error_cm"), MaxArmorBonePositionError);
    Json->SetNumberField(TEXT("max_armor_bone_rotation_error_degrees"), MaxArmorBoneRotationError);
    Json->SetNumberField(TEXT("max_component_world_scale_error"), MaxWorldScaleError);
    Json->SetBoolField(TEXT("armor_skeleton_compatible"), !ArmorMesh || KusazuriValidArmor(ArmorMesh,BodyMesh));
    Json->SetNumberField(TEXT("max_sode_bone_position_error_cm"), MaxSodeBonePositionError);
    Json->SetNumberField(TEXT("max_sode_bone_rotation_error_degrees"), MaxSodeBoneRotationError);
    Json->SetBoolField(TEXT("sode_skeleton_compatible"), !SodeLeftMesh || (KusazuriValidArmor(SodeLeftMesh, BodyMesh) && KusazuriValidArmor(SodeRightMesh, BodyMesh)));
    Json->SetStringField(TEXT("sode_pose_method"), Sodes.IsEmpty() ? TEXT("absent") : TEXT("copied native local pose, then stateless rigid suspension override on the same upperarm bone"));
    Json->SetNumberField(TEXT("sode_suspension_samples"),SuspensionSamples);
    Json->SetStringField(TEXT("sode_error_reference"),TEXT("Copied body pose with intended controlled upperarm and propagated child transforms; raw body/armor upperarm differences are expected suspension motion"));
    Json->SetStringField(TEXT("sode_motion_source"),TEXT("SourceArt/Characters/Samurai/Sode01/Scripts/sode_motion.py"));
    TArray<TSharedPtr<FJsonValue>> Suspension;
    for (int32 Side = 0; Side < Sodes.Num(); ++Side)
    {
        auto Info = MakeShared<FJsonObject>();
        Info->SetStringField(TEXT("side"),Side == 0 ? TEXT("left") : TEXT("right"));
        Info->SetNumberField(TEXT("opening_at_capture_cm"),SodeOpening[Side]);
        Info->SetNumberField(TEXT("maximum_opening_cm"),MaxSodeOpening[Side]);
        Info->SetNumberField(TEXT("lift_clearance_at_capture_cm"),SodeLiftClearance[Side]);
        Info->SetNumberField(TEXT("maximum_lift_clearance_cm"),MaxSodeLiftClearance[Side]);
        Info->SetNumberField(TEXT("maximum_body_rotation_difference_degrees"),MaxSodeBodyRotationDifference[Side]);
        Info->SetStringField(TEXT("direction_in_blender_torso_axes"),SodeDirection[Side].ToString());
        Info->SetStringField(TEXT("controlled_upperarm_component_transform"),SodeTarget[Side].ToString());
        Suspension.Add(MakeShared<FJsonValueObject>(Info));
    }
    Json->SetArrayField(TEXT("sode_suspension"),Suspension);
    Json->SetStringField(TEXT("handedness"), TEXT("Sode_L_01 = anatomical left, native +X; Sode_R_01 = anatomical right, native -X; component yaw -90 degrees"));
    Json->SetStringField(TEXT("bow_pose_limit"), Pose == TEXT("bow") ? TEXT("Diagnostic shoulder/elbow bow-use approximation on existing Manny bones; no native bow clip or weapon; not animation validation") : TEXT("not requested"));
    Json->SetStringField(TEXT("body_standard"), TEXT("Epic Unreal Manny — SKM_Manny_Simple"));
    Json->SetStringField(TEXT("review_contract_file"), ContractPath);
    Json->SetNumberField(TEXT("body_component_yaw_degrees"), ComponentYaw);
    Json->SetStringField(TEXT("composed_head_reference_transform"), HeadReference.ToString());
    Json->SetStringField(TEXT("helmet_reference_transform"), HelmetAtReference.ToString());
    Json->SetStringField(TEXT("helmet_relative_transform"), HelmetRelative.ToString());
    Json->SetStringField(TEXT("expected_helmet_world_scale"), HelmetScale.ToString());
    TArray<TSharedPtr<FJsonValue>> CheckedBones;
    for (const auto Bone : ArmorValidationBones) CheckedBones.Add(MakeShared<FJsonValueString>(Bone.ToString()));
    Json->SetArrayField(TEXT("armor_bones_checked"), CheckedBones);
    TArray<TSharedPtr<FJsonValue>> ShoulderBones;
    for (const auto Bone : SodeValidationBones) ShoulderBones.Add(MakeShared<FJsonValueString>(Bone.ToString()));
    Json->SetArrayField(TEXT("sode_bones_checked"), ShoulderBones);
    if (Sodes.Num() == 2)
    {
        Json->SetStringField(TEXT("sode_left_world_scale"), Sodes[0]->GetComponentScale().ToString());
        Json->SetStringField(TEXT("sode_right_world_scale"), Sodes[1]->GetComponentScale().ToString());
        Json->SetStringField(TEXT("sode_left_native_bounds_center_cm"), SodeLeftMesh->GetImportedBounds().Origin.ToString());
        Json->SetStringField(TEXT("sode_right_native_bounds_center_cm"), SodeRightMesh->GetImportedBounds().Origin.ToString());
    }
    if (!Armors.IsEmpty()) Json->SetStringField(TEXT("armor_world_scale"), Armors[0]->GetComponentScale().ToString());
    if (!Helmets.IsEmpty()) Json->SetStringField(TEXT("helmet_world_scale"), Helmets[0]->GetComponentScale().ToString());
    if (!Bodies.IsEmpty())
    {
        auto Bones = MakeShared<FJsonObject>();
        for (const FName Bone : {TurnBone,BendBone,FName(TEXT("head")),FName(TEXT("upperarm_l")),FName(TEXT("upperarm_r"))})
            Bones->SetStringField(Bone.ToString(), Bodies[0]->GetSocketTransform(Bone).ToString());
        Json->SetObjectField(TEXT("body_bones_world_at_capture"), Bones);
    }
    Json->SetNumberField(TEXT("viewport_width"), Width);
    Json->SetNumberField(TEXT("viewport_height"), Height);
    Json->SetStringField(TEXT("screenshot"), Screenshot);
    Json->SetBoolField(TEXT("screenshot_exists"), bScreenshot);
    Json->SetStringField(TEXT("measurement_notes"), TEXT("Wall frame intervals include review validation overhead. Engine CPU counters exclude idle time and may describe earlier frames; positive RHI GPU samples only, unavailable counters null. Screenshot readback follows sampling. Mesh LOD inventory is not GPU draw counts. Single-body fit review or static crowd incremental art cost; static probes include no animation or skinning. No combat or population simulation. Matching bones/scale do not certify surface clearance or visual quality."));
    KusazuriAddTiming(Json,TEXT("frame"),FrameTimes);
    KusazuriAddTiming(Json,TEXT("game_thread"),GameTimes);
    KusazuriAddTiming(Json,TEXT("render_thread"),RenderTimes);
    KusazuriAddTiming(Json,TEXT("gpu"),GpuTimes);
    if (KusazuriPercentile(DrawCalls,.5)>0) Json->SetNumberField(TEXT("median_rhi_draw_calls_all_passes"),KusazuriPercentile(DrawCalls,.5));
    else Json->SetField(TEXT("median_rhi_draw_calls_all_passes"),MakeShared<FJsonValueNull>());
    if (KusazuriPercentile(Primitives,.5)>0) Json->SetNumberField(TEXT("median_rhi_primitives_all_passes"),KusazuriPercentile(Primitives,.5));
    else Json->SetField(TEXT("median_rhi_primitives_all_passes"),MakeShared<FJsonValueNull>());
    KusazuriAddMeshInfo(Json,TEXT("helmet_mesh"),HelmetMesh);
    KusazuriAddMeshInfo(Json,TEXT("armor_static_mesh"),ArmorStaticMesh);
    KusazuriAddMeshInfo(Json,TEXT("kusazuri_static_mesh"),KusazuriStaticMesh);
    KusazuriAddMeshInfo(Json,TEXT("sode_left_static_mesh"),SodeLeftStaticMesh);
    KusazuriAddMeshInfo(Json,TEXT("sode_right_static_mesh"),SodeRightStaticMesh);
    KusazuriAddMeshInfo(Json,TEXT("mannequin_static_mesh"),MannequinStaticMesh);
    KusazuriAddSkeletalInfo(Json,TEXT("kusazuri_skeletal_mesh"),KusazuriMesh);
    Json->SetNumberField(TEXT("rendered_kusazuri"), RenderedKusazuri);
    Json->SetNumberField(TEXT("instance_components"), InstanceComponents);
    Json->SetNumberField(TEXT("max_kusazuri_bone_position_error_cm"), MaxKusazuriBonePositionError);
    Json->SetNumberField(TEXT("max_kusazuri_bone_rotation_error_degrees"), MaxKusazuriBoneRotationError);
    Json->SetBoolField(TEXT("kusazuri_skeleton_compatible"), !KusazuriMesh || KusazuriValidArmor(KusazuriMesh,BodyMesh));
    Json->SetNumberField(TEXT("kusazuri_controller_samples"), KusazuriControllerSamples);
    Json->SetNumberField(TEXT("kusazuri_panel_count"), KusazuriMesh ? 7 : 0);
    Json->SetStringField(TEXT("kusazuri_pose_method"), !bClose ? TEXT("static reference-pose ISM") :
        TEXT("same native bone set; pelvis belt plus seven independent rigid panel hinge overrides on armor component only"));
    TArray<TSharedPtr<FJsonValue>> PanelMeasurements;
    for (int32 Index=0; Index<7 && KusazuriMesh; ++Index)
    {
        auto Panel = MakeShared<FJsonObject>();
        Panel->SetNumberField(TEXT("index"),Index);
        Panel->SetStringField(TEXT("name"),KusazuriHinges::Panels[Index].Name);
        Panel->SetStringField(TEXT("bone"),KusazuriHinges::Panels[Index].Bone);
        Panel->SetNumberField(TEXT("hinge_at_capture_degrees"),FMath::RadiansToDegrees(PanelAngles[Index]));
        Panel->SetNumberField(TEXT("maximum_hinge_degrees"),FMath::RadiansToDegrees(MaxPanelAngles[Index]));
        PanelMeasurements.Add(MakeShared<FJsonValueObject>(Panel));
    }
    Json->SetArrayField(TEXT("kusazuri_panels"),PanelMeasurements);
    KusazuriAddSkeletalInfo(Json,TEXT("body_skeletal_mesh"),BodyMesh);
    KusazuriAddSkeletalInfo(Json,TEXT("armor_skeletal_mesh"),ArmorMesh);
    KusazuriAddSkeletalInfo(Json,TEXT("sode_left_skeletal_mesh"),SodeLeftMesh);
    KusazuriAddSkeletalInfo(Json,TEXT("sode_right_skeletal_mesh"),SodeRightMesh);
    FString Text;
    FJsonSerializer::Serialize(Json,TJsonWriterFactory<>::Create(&Text));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Output),true);
    if (!FFileHelper::SaveStringToFile(Text,*Output,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)) { Fail(TEXT("Could not write review JSON.")); return; }
    FString Csv = TEXT("frame,wall_ms,game_thread_ms,render_thread_ms,gpu_ms\n");
    auto Counter = [](double Value) { return Value > 0 ? FString::Printf(TEXT("%.6f"),Value) : FString(); };
    for (int32 Index=0; Index<FrameTimes.Num(); ++Index)
        Csv += FString::Printf(TEXT("%d,%.6f,%s,%s,%s\n"),Index,FrameTimes[Index],*Counter(GameTimes[Index]),*Counter(RenderTimes[Index]),*Counter(GpuTimes[Index]));
    if (!FFileHelper::SaveStringToFile(Csv,*FPaths::ChangeExtension(Output,TEXT("csv")),FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)) { Fail(TEXT("Could not write frame samples.")); return; }
    UE_LOG(LogTemp,Display,TEXT("KUSAZURI_REVIEW_COMPLETE frames=%d valid=%d output=%s"),FrameTimes.Num(),bValid,*Output);
    FPlatformMisc::RequestExitWithStatus(false,bValid ? 0 : 1);
}

#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenKusazuriHingeMath, "Shoen.Art.Kusazuri.HingeMath",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenKusazuriHingeMath::RunTest(const FString& Parameters)
{
    const FVector LeftHip(10,0,100), LeftKnee(10,0,60), RightHip(-10,0,100), RightKnee(-10,0,60);
    const FTransform Reference(FQuat::Identity,FVector(11,2,80));
    const FTransform Moved(FRotator(0,35,0),FVector(20,-30,12),FVector::OneVector);
    for (int32 Panel=0; Panel<7; ++Panel)
    {
        FTransform Target;
        double Angle = -1;
        TestTrue(TEXT("rest pose input accepted"),KusazuriHinges::Target(Panel,Reference,FTransform::Identity,
            FTransform::Identity,LeftHip,LeftKnee,RightHip,RightKnee,Target,Angle));
        TestTrue(TEXT("hanging legs retain reference panel pose"),Target.Equals(Reference,.000001));
        TestEqual(TEXT("hanging legs cause no opening"),Angle,0.0);
        TestTrue(TEXT("rigid pelvis motion accepted"),KusazuriHinges::Target(Panel,Reference,FTransform::Identity,
            Moved,Moved.TransformPosition(LeftHip),Moved.TransformPosition(LeftKnee),Moved.TransformPosition(RightHip),
            Moved.TransformPosition(RightKnee),Target,Angle));
        TestTrue(TEXT("pelvis movement preserves local hanging pose"),Target.Equals(Reference*Moved,.000001));
    }
    FTransform Target;
    double Angle = 0;
    TestTrue(TEXT("forward raised knee accepted"),KusazuriHinges::Target(0,FTransform::Identity,FTransform::Identity,
        FTransform::Identity,LeftHip,LeftHip+FVector(0,40,0),RightHip,RightKnee,Target,Angle));
    const double ExpectedAngle = FMath::Atan2(1.0,.08)-.02;
    TestTrue(TEXT("front center responds to raised leg"),FMath::Abs(Angle-ExpectedAngle) < .000001);
    const FVector Pivot(0,16.2,100.6);
    const FVector HangingPoint = Pivot+FVector(0,0,-30);
    const FVector ExpectedPoint = Pivot+FVector(0,30*FMath::Sin(ExpectedAngle),-30*FMath::Cos(ExpectedAngle));
    TestTrue(TEXT("native reflection opens panel forward around fixed waist hinge"),
        Target.TransformPosition(HangingPoint).Equals(ExpectedPoint,.000001));
    TestTrue(TEXT("hinge pivot stays attached"),Target.TransformPosition(Pivot).Equals(Pivot,.000001));
    for (const int32 PanelIndex : {1,2})
    {
        const double High = FMath::DegreesToRadians(80.0);
        const FVector Raised(0,40*FMath::Sin(High),-40*FMath::Cos(High));
        TestTrue(TEXT("high flexion front panel accepted"),KusazuriHinges::Target(PanelIndex,FTransform::Identity,
            FTransform::Identity,FTransform::Identity,LeftHip,LeftHip+Raised,RightHip,RightHip+Raised,Target,Angle));
        TestTrue(TEXT("above 75 degrees front panel opens sagittally"),
            Target.GetRotation().AngularDistance(FQuat(FVector::XAxisVector,High-.02)) < .000001);
        const double Low = FMath::DegreesToRadians(45.0);
        const FVector Walking(0,40*FMath::Sin(Low),-40*FMath::Cos(Low));
        TestTrue(TEXT("ordinary flexion front panel accepted"),KusazuriHinges::Target(PanelIndex,FTransform::Identity,
            FTransform::Identity,FTransform::Identity,LeftHip,LeftHip+Walking,RightHip,RightHip+Walking,Target,Angle));
        const double Theta = KusazuriHinges::Panels[PanelIndex].Theta;
        const double RadialAngle = FMath::Atan2(FMath::Sin(Low)*FMath::Cos(Theta),FMath::Cos(Low))-.02;
        const FQuat RadialRotation(FVector(-FMath::Cos(Theta),FMath::Sin(Theta),0),-RadialAngle);
        TestTrue(TEXT("below 50 degrees front panel keeps its authored radial hinge"),
            Target.GetRotation().AngularDistance(RadialRotation) < .000001);
        const double SideSign = PanelIndex == 1 ? 1.0 : -1.0;
        const FVector LateralAttack(SideSign*.60,.78,-.17);
        TestTrue(TEXT("high lateral attack sample accepted"),KusazuriHinges::Target(PanelIndex,FTransform::Identity,
            FTransform::Identity,FTransform::Identity,LeftHip,LeftHip+40*LateralAttack,
            RightHip,RightHip+40*LateralAttack,Target,Angle));
        const FVector AttackDirection = LateralAttack.GetSafeNormal();
        const FVector NativeRadial(FMath::Sin(Theta),FMath::Cos(Theta),0);
        const double AttackAngle = FMath::Atan2(FVector::DotProduct(AttackDirection,NativeRadial),-AttackDirection.Z)-.02;
        TestTrue(TEXT("lateral attack beyond 35 degree azimuth retains radial hinge"),
            Target.GetRotation().AngularDistance(FQuat(FVector(-FMath::Cos(Theta),FMath::Sin(Theta),0),-AttackAngle)) < .000001);
        const double Azimuth = FMath::DegreesToRadians(10.0);
        const FVector NearForward(SideSign*FMath::Sin(Azimuth)*FMath::Sin(High),
            FMath::Cos(Azimuth)*FMath::Sin(High),-FMath::Cos(High));
        TestTrue(TEXT("near-forward raised knee accepted"),KusazuriHinges::Target(PanelIndex,FTransform::Identity,
            FTransform::Identity,FTransform::Identity,LeftHip,LeftHip+40*NearForward,
            RightHip,RightHip+40*NearForward,Target,Angle));
        const FQuat DirectedRotation(FVector(-FMath::Cos(Azimuth),SideSign*FMath::Sin(Azimuth),0),-(High-.02));
        TestTrue(TEXT("near-forward high knee hinge follows horizontal thigh direction"),
            Target.GetRotation().AngularDistance(DirectedRotation) < .000001);
        for (const double Threshold : {50.0,75.0})
        {
            FTransform Before, After;
            for (const double Offset : {-.001,.001})
            {
                const double Flex = FMath::DegreesToRadians(Threshold+Offset);
                const FVector Direction(0,40*FMath::Sin(Flex),-40*FMath::Cos(Flex));
                FTransform& Result = Offset < 0 ? Before : After;
                TestTrue(TEXT("threshold sample accepted"),KusazuriHinges::Target(PanelIndex,FTransform::Identity,
                    FTransform::Identity,FTransform::Identity,LeftHip,LeftHip+Direction,RightHip,RightHip+Direction,Result,Angle));
            }
            TestTrue(TEXT("threshold does not snap the panel"),FVector::Distance(Before.GetLocation(),After.GetLocation()) < .02 &&
                FMath::RadiansToDegrees(Before.GetRotation().AngularDistance(After.GetRotation())) < .01);
        }
    }
    for (const int32 PanelIndex : {3,4})
    {
        const double Sagittal = FMath::DegreesToRadians(45.0);
        const FVector Walking(0,40*FMath::Sin(Sagittal),-40*FMath::Cos(Sagittal));
        TestTrue(TEXT("side panel forward walking accepted"),KusazuriHinges::Target(PanelIndex,FTransform::Identity,
            FTransform::Identity,FTransform::Identity,LeftHip,LeftHip+Walking,RightHip,RightHip+Walking,Target,Angle));
        TestTrue(TEXT("side panel opens by the sagittal floor when radial opening is zero"),
            FMath::Abs(Angle-.08*Sagittal) < .000001);
    }
    TestFalse(TEXT("degenerate thigh/knee input is rejected"),KusazuriHinges::Target(0,FTransform::Identity,
        FTransform::Identity,FTransform::Identity,LeftHip,LeftHip,RightHip,RightKnee,Target,Angle));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenKusazuriHingeBlender, "Shoen.Art.Kusazuri.HingesMatchBlender",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenKusazuriHingeBlender::RunTest(const FString& Parameters)
{
    const FString Path = FPaths::Combine(FPaths::ProjectDir(),TEXT("../artifacts/kusazuri01/hinge-reference-poses.json"));
    FString Text;
    TSharedPtr<FJsonObject> Fixture;
    if (!TestTrue(TEXT("frozen Blender hinge fixture is readable"),FFileHelper::LoadFileToString(Text,*Path)) ||
        !TestTrue(TEXT("fixture is valid JSON"),FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Fixture))) return false;
    TestEqual(TEXT("fixture schema version"),Fixture->GetIntegerField(TEXT("schema_version")),1);
    auto Matrix = [](const TArray<TSharedPtr<FJsonValue>>& Rows)
    {
        FMatrix Native = FMatrix::Identity;
        const double Reflection[4] = {1,-1,1,1};
        for (int32 Row=0; Row<4; ++Row)
            for (int32 Column=0; Column<4; ++Column)
                Native.M[Row][Column] = Reflection[Row]*Reflection[Column]*Rows[Column]->AsArray()[Row]->AsNumber();
        return FTransform(Native);
    };
    const auto& Poses = Fixture->GetArrayField(TEXT("poses"));
    if (!TestTrue(TEXT("fixture covers at least five independent poses"),Poses.Num() >= 5)) return false;
    for (const auto& Value : Poses)
    {
        const auto Pose = Value->AsObject();
        const FString Name = Pose->GetStringField(TEXT("pose"));
        const FTransform RefPelvis = Matrix(Pose->GetArrayField(TEXT("pelvis_reference_blender_cm")));
        const FTransform Pelvis = Matrix(Pose->GetArrayField(TEXT("pelvis_pose_blender_cm")));
        const auto Bones = Pose->GetObjectField(TEXT("posed_bones_blender_cm"));
        const FVector LeftThigh = Matrix(Bones->GetArrayField(TEXT("thigh_l"))).GetLocation();
        const FVector RightThigh = Matrix(Bones->GetArrayField(TEXT("thigh_r"))).GetLocation();
        const FVector LeftCalf = Matrix(Bones->GetArrayField(TEXT("calf_l"))).GetLocation();
        const FVector RightCalf = Matrix(Bones->GetArrayField(TEXT("calf_r"))).GetLocation();
        const auto& Panels = Pose->GetArrayField(TEXT("panels"));
        if (!TestEqual(Name+TEXT(" includes all seven rigid panels"),Panels.Num(),7)) return false;
        TSet<int32> Seen;
        for (const auto& Entry : Panels)
        {
            const auto Panel = Entry->AsObject();
            const FString Bone = Panel->GetStringField(TEXT("bone"));
            int32 Index = INDEX_NONE;
            for (int32 Candidate=0; Candidate<7; ++Candidate)
                if (Bone == KusazuriHinges::Panels[Candidate].Bone) Index = Candidate;
            if (!TestTrue(Name+TEXT(" known panel channel ")+Bone,Index != INDEX_NONE && !Seen.Contains(Index))) return false;
            Seen.Add(Index);
            const FTransform Reference = Matrix(Panel->GetArrayField(TEXT("reference_blender_cm")));
            const FTransform Expected = Matrix(Panel->GetArrayField(TEXT("target_blender_cm")));
            FTransform Target;
            double Angle = -1;
            if (!TestTrue(Name+TEXT(" finite hinge ")+Bone,KusazuriHinges::Target(Index,Reference,RefPelvis,Pelvis,
                LeftThigh,LeftCalf,RightThigh,RightCalf,Target,Angle))) return false;
            const FString Label = Name+TEXT(" ")+Bone;
            TestTrue(Label+TEXT(" translation matches Blender within 0.002 cm"),FVector::Distance(Target.GetLocation(),Expected.GetLocation()) < .002);
            TestTrue(Label+TEXT(" rotation matches Blender within 0.005 degrees"),
                FMath::RadiansToDegrees(Target.GetRotation().AngularDistance(Expected.GetRotation())) < .005);
            TestTrue(Label+TEXT(" hinge angle matches Blender"),FMath::Abs(Angle-Panel->GetNumberField(TEXT("angle_radians"))) < .00001);
            TestTrue(Label+TEXT(" scale preserved"),(Target.GetScale3D()-Expected.GetScale3D()).GetAbsMax() < .00001);
        }
    }
    return true;
}

#endif
