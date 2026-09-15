#include "SodeReviewGameMode.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "UObject/Package.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/DirectionalLightComponent.h"
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
const TCHAR* SodeMannyAsset = TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple");
const TCHAR* SodeMannyAnimations = TEXT("/Game/Characters/Mannequins/Anims/Unarmed/");
const TCHAR* KabutoRoot = TEXT("/Game/Art/Characters/Samurai/Kabuto01/");
const TCHAR* SodeRoot = TEXT("/Game/Art/Characters/Samurai/Sode01/");
const TCHAR* DoRoot = TEXT("/Game/Art/Characters/Samurai/Do01/");
template<typename T> T* SodeArt(const TCHAR* Root, const TCHAR* Name)
{
    return LoadObject<T>(nullptr, *(FString(Root) + Name));
}

double SodePercentile(TArray<double> Values, double Fraction)
{
    if (Values.IsEmpty()) return 0;
    Values.Sort();
    return Values[FMath::Clamp(FMath::CeilToInt(Fraction * Values.Num()) - 1, 0, Values.Num() - 1)];
}

void SodeAddTiming(const TSharedRef<FJsonObject>& Json, const TCHAR* Key, const TArray<double>& Samples)
{
    const TArray<double> Values = Samples.FilterByPredicate([](double Value) { return Value > 0 && FMath::IsFinite(Value); });
    auto Timing = MakeShared<FJsonObject>();
    Timing->SetNumberField(TEXT("samples"), Values.Num());
    for (const auto& Entry : TArray<TPair<FString, double>>{
        {TEXT("median_ms"), .5}, {TEXT("p95_ms"), .95}, {TEXT("worst_ms"), 1.0}})
    {
        if (Values.IsEmpty()) Timing->SetField(Entry.Key, MakeShared<FJsonValueNull>());
        else Timing->SetNumberField(Entry.Key, SodePercentile(Values, Entry.Value));
    }
    Json->SetObjectField(Key, Timing);
}

void SodeAddMeshInfo(const TSharedRef<FJsonObject>& Json, const TCHAR* Key, UStaticMesh* Mesh)
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

void SodeConfigurePrimitive(UPrimitiveComponent* Component)
{
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCanEverAffectNavigation(false);
    Component->SetCastShadow(true);
}
}

namespace
{
bool ValidArmor(USkeletalMesh* Armor, USkeletalMesh* Body)
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
FVector SodeBlenderAxes(const FVector& Native)
{
    return FVector(Native.X, -Native.Y, Native.Z);
}

bool SodeSuspensionTarget(const FTransform& RefTorso, const FTransform& RefUpper, const FTransform& RefLower,
    const FTransform& Torso, const FTransform& Upper, const FTransform& Lower, double Sign,
    FTransform& Target, double& Opening, double& LiftClearance, FVector& Direction)
{
    if (RefTorso.ContainsNaN() || RefUpper.ContainsNaN() || RefLower.ContainsNaN() ||
        Torso.ContainsNaN() || Upper.ContainsNaN() || Lower.ContainsNaN()) return false;
    const FQuat TorsoRotation = (Torso.GetRotation()*RefTorso.GetRotation().Inverse()).GetNormalized();
    const FVector RestDown = SodeBlenderAxes(RefLower.GetLocation()-RefUpper.GetLocation()).GetSafeNormal();
    const FVector RestOut = FVector(Sign*FMath::Abs(RestDown.Z), 0, FMath::Abs(RestDown.X)).GetSafeNormal();
    FVector RestAcross = FVector::CrossProduct(RestDown, RestOut).GetSafeNormal();
    if (RestAcross.Y < 0) RestAcross *= -1;
    Direction = SodeBlenderAxes(TorsoRotation.UnrotateVector((Lower.GetLocation()-Upper.GetLocation()).GetSafeNormal()));
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
        const FVector V = SodeBlenderAxes(Native);
        return SodeBlenderAxes(Out*FVector::DotProduct(RestOut,V) + Across*FVector::DotProduct(RestAcross,V) +
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
        Upper.GetLocation()+TorsoRotation.RotateVector(SodeBlenderAxes(FVector(Sign*Opening,0,0)+Out*LiftClearance)), RefUpper.GetScale3D());
    return !Target.ContainsNaN() && FMath::IsFinite(Opening);
}

void AddSkeletalInfo(const TSharedRef<FJsonObject>& Json, const TCHAR* Key, USkeletalMesh* Mesh)
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

ASodeReviewGameMode::ASodeReviewGameMode()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickGroup = TG_PostUpdateWork;
    DefaultPawnClass = nullptr;
    HUDClass = nullptr;
}

void ASodeReviewGameMode::Fail(const FString& Reason)
{
    bFailed = true;
    UE_LOG(LogTemp, Error, TEXT("SODE_REVIEW_FAILED: %s"), *Reason);
    FPlatformMisc::RequestExitWithStatus(false, 1);
}

void ASodeReviewGameMode::BeginPlay()
{
    Super::BeginPlay();
    FParse::Value(FCommandLine::Get(), TEXT("SodeContract="), ContractPath);
    FParse::Value(FCommandLine::Get(), TEXT("SodeMode="), Mode);
    FParse::Value(FCommandLine::Get(), TEXT("SodeCamera="), Camera);
    FParse::Value(FCommandLine::Get(), TEXT("SodeAnimation="), Animation);
    FParse::Value(FCommandLine::Get(), TEXT("SodePose="), Pose);
    FParse::Value(FCommandLine::Get(), TEXT("SodeSeconds="), Seconds);
    FParse::Value(FCommandLine::Get(), TEXT("SodeOutput="), Output);
    FParse::Value(FCommandLine::Get(), TEXT("SodeScreenshot="), Screenshot);
    if (!FApp::CanEverRender()) { Fail(TEXT("Requires an actual rendered viewport; NullRHI is not a benchmark.")); return; }
    if (Mode != TEXT("mannequin") && Mode != TEXT("sode") && Mode != TEXT("armor")) { Fail(TEXT("Unknown comparison mode.")); return; }
    if (!TArray<FString>{TEXT("close"),TEXT("front"),TEXT("back"),TEXT("rear"),TEXT("left"),TEXT("right"),TEXT("detail"),TEXT("tactical")}.Contains(Camera)) { Fail(TEXT("Unknown camera.")); return; }
    if (!TArray<FString>{TEXT("idle"),TEXT("walk"),TEXT("run"),TEXT("attack"),TEXT("none")}.Contains(Animation)) { Fail(TEXT("Unknown animation.")); return; }
    if (!TArray<FString>{TEXT("animation"),TEXT("neutral"),TEXT("arms-forward"),TEXT("arms-raised"),TEXT("turn"),TEXT("bend"),TEXT("head"),TEXT("bow")}.Contains(Pose)) { Fail(TEXT("Unknown inspection pose.")); return; }
    bClose = Camera != TEXT("tactical");
    if (!FMath::IsFinite(Seconds) || Seconds < 0 || Seconds > 600 || (Seconds > 0 && (Output.IsEmpty() || Screenshot.IsEmpty()))) { Fail(TEXT("Timed runs need output and screenshot paths, duration at most 600 seconds.")); return; }
    if (!ReadReviewContract()) { Fail(TEXT("Missing/invalid native Manny review_contract in the Sode manifest.")); return; }
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
    UE_LOG(LogTemp, Display, TEXT("SODE_REVIEW_READY mode=%s camera=%s bodies=%d helmets=%d armors=%d sode=%d"), *Mode, *Camera, RenderedBodies, RenderedHelmets, RenderedArmors, RenderedSode);
}

bool ASodeReviewGameMode::ReadReviewContract()
{
    if (ContractPath.IsEmpty()) ContractPath = FPaths::Combine(FPaths::ProjectDir(), TEXT("../SourceArt/Characters/Samurai/Sode01/asset-manifest.json"));
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

bool ASodeReviewGameMode::CreateCharacter(AActor* Owner, USceneComponent* Root, const FVector& Position)
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
            if (Animation == TEXT("idle")) Clip = SodeArt<UAnimSequence>(SodeMannyAnimations, TEXT("MM_Idle"));
            else if (Animation == TEXT("walk")) Clip = SodeArt<UAnimSequence>(SodeMannyAnimations, TEXT("Walk/MF_Unarmed_Walk_Fwd"));
            else if (Animation == TEXT("run")) Clip = SodeArt<UAnimSequence>(SodeMannyAnimations, TEXT("Jog/MF_Unarmed_Jog_Fwd"));
            else if (Animation == TEXT("attack")) Clip = SodeArt<UAnimSequence>(SodeMannyAnimations, TEXT("Attack/MM_Attack_01"));
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
    TArray<USkinnedMeshComponent*> Components = {Body, Armor};
    Components.Append(CharacterSode);
    for (auto* Component : Components)
    {
        if (!Component) continue;
        SodeConfigurePrimitive(Component);
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
        SodeConfigurePrimitive(Helmet);
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

bool ASodeReviewGameMode::CreateReview()
{
    auto* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto* Basic = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    BodyMesh = LoadObject<USkeletalMesh>(nullptr, SodeMannyAsset);
    if (!Cube || !Basic || !BodyMesh) return false;
    if (Mode != TEXT("mannequin"))
    {
        HelmetMesh = SodeArt<UStaticMesh>(KabutoRoot, TEXT("SM_Kabuto01"));
        if (!HelmetMesh || HelmetMesh->GetStaticMaterials().IsEmpty()) return false;
    }
    if (Mode == TEXT("armor") || Mode == TEXT("sode"))
    {
        ArmorMesh = SodeArt<USkeletalMesh>(DoRoot, TEXT("SK_Do01"));
        ArmorStaticMesh = SodeArt<UStaticMesh>(DoRoot, TEXT("Review/SM_Do01"));
        if (!ValidArmor(ArmorMesh, BodyMesh) || !ArmorStaticMesh || ArmorStaticMesh->GetStaticMaterials().IsEmpty()) return false;
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
    if (Mode == TEXT("sode"))
    {
        SodeLeftMesh = SodeArt<USkeletalMesh>(SodeRoot, TEXT("SK_Sode_L_01"));
        SodeRightMesh = SodeArt<USkeletalMesh>(SodeRoot, TEXT("SK_Sode_R_01"));
        if (!ValidArmor(SodeLeftMesh, BodyMesh) || !ValidArmor(SodeRightMesh, BodyMesh)) return false;
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
    const auto& Ref = BodyMesh->GetRefSkeleton();
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
    SodeConfigurePrimitive(GroundMesh);
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
    if (!CreateCharacter(Owner, Root, FVector::ZeroVector)) return false;
    if (PoseBody) UpdateInspectionPose();
    if (!UpdateSodeSuspension()) return false;
    FVector Focus = FVector::ZeroVector;
    const double Yaw = Camera == TEXT("front") ? 0 : Camera == TEXT("left") ? -90 : Camera == TEXT("right") ? 90 : Camera == TEXT("back") ? 180 : Camera == TEXT("rear") ? 145 : bClose ? 32 : 32;
    const FVector Direction = FRotator(bClose ? 15 : 38, Yaw, 0).Vector();
    CameraDistance = 1500;
    Focus.Z = 90;
    if (bClose)
    {
        const FTransform BodyTransform(FRotator(0,ComponentYaw,0));
        // Use the same waist-to-crest envelope in every comparison mode.
        // Manny's full arm/leg bounds otherwise push the torso too far away.
        auto* FramingArmor = SodeArt<USkeletalMesh>(DoRoot, TEXT("SK_Do01"));
        auto* FramingHelmet = SodeArt<UStaticMesh>(KabutoRoot, TEXT("SM_Kabuto01"));
        if (!FramingArmor || !FramingHelmet) return false;
        FBox Bounds = FramingArmor->GetImportedBounds().GetBox().TransformBy(BodyTransform);
        Bounds += FramingHelmet->GetBoundingBox().TransformBy(HelmetAtReference*BodyTransform);
        for (const auto* Name : {TEXT("SK_Sode_L_01"), TEXT("SK_Sode_R_01")})
        {
            auto* FramingSode = SodeArt<USkeletalMesh>(SodeRoot, Name);
            if (!FramingSode) return false;
            Bounds += FramingSode->GetImportedBounds().GetBox().TransformBy(BodyTransform);
        }
        if (Camera == TEXT("detail"))
        {
            auto* DetailSode = SodeArt<USkeletalMesh>(SodeRoot, TEXT("SK_Sode_R_01"));
            Bounds = DetailSode->GetImportedBounds().GetBox().TransformBy(BodyTransform);
        }
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

void ASodeReviewGameMode::UpdateInspectionPose()
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
                const FVector Target = (Pose == TEXT("bow") ? (bLeft ? Left+Forward*.25 : -Left-Forward*.30) : Pose == TEXT("arms-forward") ? Left*(bLeft ? .12 : -.12)+Forward-FVector::UpVector*.1 : Left*(bLeft ? 1 : -1)+FVector::UpVector*.25).GetSafeNormal();
                Transform.SetRotation(FQuat::FindBetweenNormals(Rest,Target)*Transform.GetRotation());
            }
        }
        if (Pose == TEXT("bow") && Name == TEXT("lowerarm_r"))
        {
            const int32 Wrist = Ref.FindBoneIndex(TEXT("hand_r"));
            if (Wrist != INDEX_NONE)
            {
                const FVector Rest = ((Ref.GetRefBonePose()[Wrist]*Transform).GetLocation()-Transform.GetLocation()).GetSafeNormal();
                const FVector Target = (Left+Forward*.15+FVector::UpVector*.20).GetSafeNormal();
                Transform.SetRotation(FQuat::FindBetweenNormals(Rest,Target)*Transform.GetRotation());
            }
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

bool ASodeReviewGameMode::UpdateSodeSuspension()
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
        if (!SodeSuspensionTarget(BodyReferenceComponentSpace[TorsoIndex], BodyReferenceComponentSpace[UpperIndex],
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

void ASodeReviewGameMode::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (bFailed || bFinished) return;
    const double Now = FPlatformTime::Seconds();
    UpdateInspectionPose();
    if (!UpdateSodeSuspension()) { Fail(TEXT("Invalid Sode suspension pose.")); return; }
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

void ASodeReviewGameMode::CompleteReview()
{
    bFinished = true;
    auto Json = MakeShared<FJsonObject>();
    int32 Width = 0, Height = 0;
    GetWorld()->GetFirstPlayerController()->GetViewportSize(Width, Height);
    const bool bScreenshot = IFileManager::Get().FileSize(*Screenshot) > 0;
    const bool bAnimationRequired = !Bodies.IsEmpty() && Pose == TEXT("animation") && Animation != TEXT("none");
    const bool bAnimationAdvanced = MaxAnimationPosition-MinAnimationPosition > .001;
    const bool bValid = (!bAnimationRequired || bAnimationAdvanced) && !FrameTimes.IsEmpty() && Width > 0 && Height > 0 && bScreenshot &&
        RenderedBodies == 1 && RenderedHelmets == (Mode != TEXT("mannequin") ? RenderedBodies : 0) &&
        RenderedArmors == (Mode != TEXT("mannequin") ? 1 : 0) && RenderedSode == (Mode == TEXT("sode") ? 2 : 0) && MaxAttachmentPositionError < .1 &&
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
    Json->SetStringField(TEXT("animation"), Pose == TEXT("animation") ? Animation : TEXT("component-space inspection pose"));
    Json->SetStringField(TEXT("crowd_representation"), TEXT("single skeletal/poseable fixture"));
    Json->SetStringField(TEXT("armor_pose_method"), Armors.IsEmpty() ? TEXT("absent") : PoseArmor ? TEXT("copied component-space body bones") : TEXT("SetLeaderPoseComponent(body)"));
    Json->SetStringField(TEXT("engine"), FEngineVersion::Current().ToString());
    Json->SetStringField(TEXT("platform"), ANSI_TO_TCHAR(FPlatformProperties::IniPlatformName()));
    Json->SetStringField(TEXT("rhi"), GDynamicRHI ? GDynamicRHI->GetName() : TEXT("unavailable"));
    Json->SetStringField(TEXT("build"), TEXT("Development editor game; opt-in isolated Sode pair art review"));
    Json->SetNumberField(TEXT("requested_count"), 1);
    Json->SetNumberField(TEXT("rendered_bodies"), RenderedBodies);
    Json->SetNumberField(TEXT("rendered_helmets"), RenderedHelmets);
    Json->SetNumberField(TEXT("rendered_armors"), RenderedArmors);
    Json->SetNumberField(TEXT("rendered_sode_left"), SodeLeftMesh ? 1 : 0);
    Json->SetNumberField(TEXT("rendered_sode_right"), SodeRightMesh ? 1 : 0);
    Json->SetNumberField(TEXT("rendered_sode"), RenderedSode);
    Json->SetNumberField(TEXT("skeletal_components"), Bodies.Num()+Armors.Num()+Sodes.Num());
    Json->SetNumberField(TEXT("camera_distance_cm"), CameraDistance);
    Json->SetNumberField(TEXT("camera_horizontal_fov"), bClose ? 40 : 55);
    Json->SetNumberField(TEXT("camera_elevation_degrees"), bClose ? 15 : 38);
    Json->SetBoolField(TEXT("body_helmet_armor_cast_shadows"), true);
    Json->SetNumberField(TEXT("warmup_seconds"), 3);
    Json->SetNumberField(TEXT("capture_seconds"), CaptureElapsed);
    Json->SetNumberField(TEXT("frames"), FrameTimes.Num());
    Json->SetNumberField(TEXT("median_fps"), FrameTimes.IsEmpty() ? 0 : 1000/SodePercentile(FrameTimes,.5));
    Json->SetNumberField(TEXT("interval_fps"), CaptureElapsed > 0 ? FrameTimes.Num()/CaptureElapsed : 0);
    Json->SetNumberField(TEXT("peak_process_physical_bytes"), double(PeakMemory));
    Json->SetNumberField(TEXT("max_attachment_position_error_cm"), MaxAttachmentPositionError);
    Json->SetNumberField(TEXT("max_armor_bone_position_error_cm"), MaxArmorBonePositionError);
    Json->SetNumberField(TEXT("max_armor_bone_rotation_error_degrees"), MaxArmorBoneRotationError);
    Json->SetNumberField(TEXT("max_component_world_scale_error"), MaxWorldScaleError);
    Json->SetBoolField(TEXT("armor_skeleton_compatible"), !ArmorMesh || ValidArmor(ArmorMesh,BodyMesh));
    Json->SetNumberField(TEXT("max_sode_bone_position_error_cm"), MaxSodeBonePositionError);
    Json->SetNumberField(TEXT("max_sode_bone_rotation_error_degrees"), MaxSodeBoneRotationError);
    Json->SetBoolField(TEXT("sode_skeleton_compatible"), !SodeLeftMesh || (ValidArmor(SodeLeftMesh, BodyMesh) && ValidArmor(SodeRightMesh, BodyMesh)));
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
    if (SodeLeftMesh && SodeRightMesh)
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
    Json->SetStringField(TEXT("measurement_notes"), TEXT("Wall frame intervals include review validation overhead. Engine CPU counters exclude idle time and may describe earlier frames; positive RHI GPU samples only, unavailable counters null. Screenshot readback follows sampling. Mesh LOD inventory is not GPU draw counts. Single-body incremental art cost only; includes animation/skinning and validation, no combat or population simulation. Matching bones/scale do not certify surface clearance or visual quality."));
    SodeAddTiming(Json,TEXT("frame"),FrameTimes);
    SodeAddTiming(Json,TEXT("game_thread"),GameTimes);
    SodeAddTiming(Json,TEXT("render_thread"),RenderTimes);
    SodeAddTiming(Json,TEXT("gpu"),GpuTimes);
    if (SodePercentile(DrawCalls,.5)>0) Json->SetNumberField(TEXT("median_rhi_draw_calls_all_passes"),SodePercentile(DrawCalls,.5));
    else Json->SetField(TEXT("median_rhi_draw_calls_all_passes"),MakeShared<FJsonValueNull>());
    if (SodePercentile(Primitives,.5)>0) Json->SetNumberField(TEXT("median_rhi_primitives_all_passes"),SodePercentile(Primitives,.5));
    else Json->SetField(TEXT("median_rhi_primitives_all_passes"),MakeShared<FJsonValueNull>());
    SodeAddMeshInfo(Json,TEXT("helmet_mesh"),HelmetMesh);
    SodeAddMeshInfo(Json,TEXT("armor_static_mesh"),ArmorStaticMesh);
    AddSkeletalInfo(Json,TEXT("body_skeletal_mesh"),BodyMesh);
    AddSkeletalInfo(Json,TEXT("armor_skeletal_mesh"),ArmorMesh);
    AddSkeletalInfo(Json,TEXT("sode_left_skeletal_mesh"),SodeLeftMesh);
    AddSkeletalInfo(Json,TEXT("sode_right_skeletal_mesh"),SodeRightMesh);
    FString Text;
    FJsonSerializer::Serialize(Json,TJsonWriterFactory<>::Create(&Text));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Output),true);
    if (!FFileHelper::SaveStringToFile(Text,*Output,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)) { Fail(TEXT("Could not write review JSON.")); return; }
    FString Csv = TEXT("frame,wall_ms,game_thread_ms,render_thread_ms,gpu_ms\n");
    auto Counter = [](double Value) { return Value > 0 ? FString::Printf(TEXT("%.6f"),Value) : FString(); };
    for (int32 Index=0; Index<FrameTimes.Num(); ++Index)
        Csv += FString::Printf(TEXT("%d,%.6f,%s,%s,%s\n"),Index,FrameTimes[Index],*Counter(GameTimes[Index]),*Counter(RenderTimes[Index]),*Counter(GpuTimes[Index]));
    if (!FFileHelper::SaveStringToFile(Csv,*FPaths::ChangeExtension(Output,TEXT("csv")),FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)) { Fail(TEXT("Could not write frame samples.")); return; }
    UE_LOG(LogTemp,Display,TEXT("SODE_REVIEW_COMPLETE frames=%d valid=%d output=%s"),FrameTimes.Num(),bValid,*Output);
    FPlatformMisc::RequestExitWithStatus(false,bValid ? 0 : 1);
}

#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenSodeSuspensionReference, "Shoen.Art.Sode.SuspensionMatchesBlender",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenSodeSuspensionReference::RunTest(const FString& Parameters)
{
    FString Text;
    TSharedPtr<FJsonObject> Fixture;
    const FString Path = FPaths::Combine(FPaths::ProjectDir(),TEXT("../SourceArt/Characters/Samurai/Sode01/Scripts/suspension-reference-poses.json"));
    if (!TestTrue(TEXT("frozen Blender reference fixture is readable"),FFileHelper::LoadFileToString(Text,*Path)) ||
        !TestTrue(TEXT("fixture is valid JSON"),FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Fixture))) return false;
    auto Vector = [](const TArray<TSharedPtr<FJsonValue>>& Values)
    {
        return SodeBlenderAxes(FVector(Values[0]->AsNumber(),Values[1]->AsNumber(),Values[2]->AsNumber()));
    };
    auto Matrix = [](const TArray<TSharedPtr<FJsonValue>>& Rows)
    {
        // Blender uses column vectors; Unreal stores basis axes in matrix rows.
        FMatrix Native = FMatrix::Identity;
        const double Reflection[4] = {1,-1,1,1};
        for (int32 Row = 0; Row < 4; ++Row)
            for (int32 Col = 0; Col < 4; ++Col)
                Native.M[Row][Col] = Reflection[Row]*Reflection[Col]*Rows[Col]->AsArray()[Row]->AsNumber();
        return FTransform(Native);
    };
    const auto& Samples = Fixture->GetArrayField(TEXT("samples"));
    TestEqual(TEXT("sixteen source poses include both anatomical sides"),Samples.Num(),32);
    for (const auto& Value : Samples)
    {
        const auto Sample = Value->AsObject();
        const bool bLeft = Sample->GetStringField(TEXT("side")) == TEXT("l");
        const FTransform RefUpper = Matrix(Sample->GetArrayField(TEXT("upper_reference_blender_cm")));
        const FTransform RefLower(Vector(Sample->GetArrayField(TEXT("elbow_reference_blender_cm"))));
        const FTransform Torso = Matrix(Sample->GetArrayField(TEXT("torso_delta_blender_cm")));
        FTransform Upper(RefUpper.GetRotation(),Vector(Sample->GetArrayField(TEXT("shoulder_blender_cm"))));
        const FTransform Lower(Vector(Sample->GetArrayField(TEXT("elbow_blender_cm"))));
        const FTransform Expected = Matrix(Sample->GetArrayField(TEXT("target_blender_cm")));
        FTransform Target;
        double Opening = 0, Lift = 0;
        FVector Direction;
        if (!TestTrue(TEXT("finite suspension target"),SodeSuspensionTarget(FTransform::Identity,RefUpper,RefLower,
            Torso,Upper,Lower,bLeft ? 1.0 : -1.0,Target,Opening,Lift,Direction))) return false;
        const FString Label = Sample->GetStringField(TEXT("pose"))+TEXT(" ")+Sample->GetStringField(TEXT("side"));
        TestTrue(Label+TEXT(" target translation matches Blender within 0.002 cm"),FVector::Distance(Target.GetLocation(),Expected.GetLocation()) < .002);
        TestTrue(Label+TEXT(" target rotation matches Blender within 0.005 degrees"),
            FMath::RadiansToDegrees(Target.GetRotation().AngularDistance(Expected.GetRotation())) < .005);
        TestTrue(Label+TEXT(" opening matches Blender"),FMath::Abs(Opening-Sample->GetNumberField(TEXT("opening_cm"))) < .002);
        TestTrue(Label+TEXT(" lift clearance matches Blender"),FMath::Abs(Lift-Sample->GetNumberField(TEXT("lift_clearance_cm"))) < .002);
        TestTrue(Label+TEXT(" preserves unit rigid scale"),(Target.GetScale3D()-FVector::OneVector).GetAbsMax() < .00001);
        // Changing only the upper-arm axial rotation cannot twist the shield.
        Upper.SetRotation(FQuat((Lower.GetLocation()-Upper.GetLocation()).GetSafeNormal(),1.2)*Upper.GetRotation());
        FTransform Untwisted;
        double OtherOpening = 0, OtherLift = 0;
        FVector OtherDirection;
        TestTrue(Label+TEXT(" axial-twist input accepted"),SodeSuspensionTarget(FTransform::Identity,RefUpper,RefLower,
            Torso,Upper,Lower,bLeft ? 1.0 : -1.0,Untwisted,OtherOpening,OtherLift,OtherDirection));
        TestTrue(Label+TEXT(" ignores axial twist"),Untwisted.Equals(Target,.000001));
    }
    for (const double Sign : {1.0,-1.0})
    {
        const FVector ReferenceDirection(Sign*.576,0,-FMath::Sqrt(1-.576*.576));
        FTransform Lateral;
        double Opening = 0, Lift = 0;
        FVector Direction;
        TestTrue(TEXT("exactly lateral arm has a nonsingular target"),SodeSuspensionTarget(FTransform::Identity,
            FTransform::Identity,FTransform(ReferenceDirection),FTransform::Identity,FTransform::Identity,
            FTransform(FVector(Sign*30,0,0)),Sign,Lateral,Opening,Lift,Direction));
        TestTrue(TEXT("lateral target keeps its rigid down axis along the arm"),
            Lateral.GetRotation().RotateVector(ReferenceDirection).Equals(FVector(Sign,0,0),.000001));
        TestTrue(TEXT("lateral lift has four centimetres of clearance"),FMath::IsNearlyEqual(Lift,4.0,.000001));
        TestTrue(TEXT("lateral offset follows its anatomical side"),
            Lateral.GetLocation().Equals(FVector(Sign*Opening,0,4),.000001));
    }
    FTransform Invalid;
    double Opening = 0, Lift = 0;
    FVector Direction;
    TestFalse(TEXT("zero-length shoulder/elbow vector is rejected"),SodeSuspensionTarget(FTransform::Identity,
        FTransform::Identity,FTransform(FVector(1,0,-1)),FTransform::Identity,FTransform::Identity,FTransform::Identity,
        1,Invalid,Opening,Lift,Direction));
    return true;
}
#endif
