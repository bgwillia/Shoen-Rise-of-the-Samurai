#include "DoReviewGameMode.h"
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
const TCHAR* DoMannyAsset = TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple");
const TCHAR* DoMannyAnimations = TEXT("/Game/Characters/Mannequins/Anims/Unarmed/");
const TCHAR* KabutoRoot = TEXT("/Game/Art/Characters/Samurai/Kabuto01/");
const TCHAR* DoRoot = TEXT("/Game/Art/Characters/Samurai/Do01/");
template<typename T> T* DoArt(const TCHAR* Root, const TCHAR* Name)
{
    return LoadObject<T>(nullptr, *(FString(Root) + Name));
}

double DoPercentile(TArray<double> Values, double Fraction)
{
    if (Values.IsEmpty()) return 0;
    Values.Sort();
    return Values[FMath::Clamp(FMath::CeilToInt(Fraction * Values.Num()) - 1, 0, Values.Num() - 1)];
}

void DoAddTiming(const TSharedRef<FJsonObject>& Json, const TCHAR* Key, const TArray<double>& Samples)
{
    const TArray<double> Values = Samples.FilterByPredicate([](double Value) { return Value > 0 && FMath::IsFinite(Value); });
    auto Timing = MakeShared<FJsonObject>();
    Timing->SetNumberField(TEXT("samples"), Values.Num());
    for (const auto& Entry : TArray<TPair<FString, double>>{
        {TEXT("median_ms"), .5}, {TEXT("p95_ms"), .95}, {TEXT("worst_ms"), 1.0}})
    {
        if (Values.IsEmpty()) Timing->SetField(Entry.Key, MakeShared<FJsonValueNull>());
        else Timing->SetNumberField(Entry.Key, DoPercentile(Values, Entry.Value));
    }
    Json->SetObjectField(Key, Timing);
}

void DoAddMeshInfo(const TSharedRef<FJsonObject>& Json, const TCHAR* Key, UStaticMesh* Mesh)
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

void DoConfigurePrimitive(UPrimitiveComponent* Component)
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

ADoReviewGameMode::ADoReviewGameMode()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickGroup = TG_PostUpdateWork;
    DefaultPawnClass = nullptr;
    HUDClass = nullptr;
}

void ADoReviewGameMode::Fail(const FString& Reason)
{
    bFailed = true;
    UE_LOG(LogTemp, Error, TEXT("DO_REVIEW_FAILED: %s"), *Reason);
    FPlatformMisc::RequestExitWithStatus(false, 1);
}

void ADoReviewGameMode::BeginPlay()
{
    Super::BeginPlay();
    FParse::Value(FCommandLine::Get(), TEXT("DoContract="), ContractPath);
    FParse::Value(FCommandLine::Get(), TEXT("DoCount="), Count);
    FParse::Value(FCommandLine::Get(), TEXT("DoMode="), Mode);
    FParse::Value(FCommandLine::Get(), TEXT("DoCamera="), Camera);
    FParse::Value(FCommandLine::Get(), TEXT("DoAnimation="), Animation);
    FParse::Value(FCommandLine::Get(), TEXT("DoPose="), Pose);
    FParse::Value(FCommandLine::Get(), TEXT("DoCrowd="), Crowd);
    FParse::Value(FCommandLine::Get(), TEXT("DoSeconds="), Seconds);
    FParse::Value(FCommandLine::Get(), TEXT("DoOutput="), Output);
    FParse::Value(FCommandLine::Get(), TEXT("DoScreenshot="), Screenshot);
    if (!FApp::CanEverRender()) { Fail(TEXT("Requires an actual rendered viewport; NullRHI is not a benchmark.")); return; }
    if (Count != 100 && Count != 500 && Count != 1000) { Fail(TEXT("Count must be 100, 500 or 1000.")); return; }
    if (Mode != TEXT("mannequin") && Mode != TEXT("helmet") && Mode != TEXT("armor")) { Fail(TEXT("Unknown comparison mode.")); return; }
    if (!TArray<FString>{TEXT("close"),TEXT("front"),TEXT("rear"),TEXT("left"),TEXT("right"),TEXT("tactical"),TEXT("far")}.Contains(Camera)) { Fail(TEXT("Unknown camera.")); return; }
    if (!TArray<FString>{TEXT("idle"),TEXT("walk"),TEXT("run"),TEXT("attack"),TEXT("none")}.Contains(Animation)) { Fail(TEXT("Unknown animation.")); return; }
    if (!TArray<FString>{TEXT("animation"),TEXT("neutral"),TEXT("arms-forward"),TEXT("arms-raised"),TEXT("turn"),TEXT("bend"),TEXT("head")}.Contains(Pose)) { Fail(TEXT("Unknown inspection pose.")); return; }
    if (Crowd != TEXT("static") && Crowd != TEXT("skeletal")) { Fail(TEXT("Unknown crowd representation.")); return; }
    bClose = Camera != TEXT("tactical") && Camera != TEXT("far");
    if (Crowd == TEXT("skeletal") && (bClose || Count != 100 || Pose != TEXT("animation") || Animation == TEXT("none"))) { Fail(TEXT("Skeletal crowd probe requires tactical/far, count 100 and a real animation.")); return; }
    if (!bClose && Pose != TEXT("animation")) { Fail(TEXT("Inspection poses require a close camera.")); return; }
    if (!FMath::IsFinite(Seconds) || Seconds < 0 || Seconds > 600 || (Seconds > 0 && (Output.IsEmpty() || Screenshot.IsEmpty()))) { Fail(TEXT("Timed runs need output and screenshot paths, duration at most 600 seconds.")); return; }
    if (!ReadReviewContract()) { Fail(TEXT("Missing/invalid Manny review_contract in the Dō manifest.")); return; }
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
    UE_LOG(LogTemp, Display, TEXT("DO_REVIEW_READY mode=%s camera=%s crowd=%s bodies=%d helmets=%d armors=%d"), *Mode, *Camera, *Crowd, RenderedBodies, RenderedHelmets, RenderedArmors);
}

bool ADoReviewGameMode::ReadReviewContract()
{
    if (ContractPath.IsEmpty()) ContractPath = FPaths::Combine(FPaths::ProjectDir(), TEXT("../SourceArt/Characters/Samurai/Do01/asset-manifest.json"));
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

bool ADoReviewGameMode::CreateCharacter(AActor* Owner, USceneComponent* Root, const FVector& Position)
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
            if (Animation == TEXT("idle")) Clip = DoArt<UAnimSequence>(DoMannyAnimations, TEXT("MM_Idle"));
            else if (Animation == TEXT("walk")) Clip = DoArt<UAnimSequence>(DoMannyAnimations, TEXT("Walk/MF_Unarmed_Walk_Fwd"));
            else if (Animation == TEXT("run")) Clip = DoArt<UAnimSequence>(DoMannyAnimations, TEXT("Jog/MF_Unarmed_Jog_Fwd"));
            else if (Animation == TEXT("attack")) Clip = DoArt<UAnimSequence>(DoMannyAnimations, TEXT("Attack/MM_Attack_01"));
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
    for (auto* Component : {Body, Armor})
    {
        if (!Component) continue;
        DoConfigurePrimitive(Component);
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
        DoConfigurePrimitive(Helmet);
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

bool ADoReviewGameMode::CreateReview()
{
    auto* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto* Basic = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    MannequinMesh = DoArt<UStaticMesh>(DoRoot, TEXT("Review/SM_Manny"));
    BodyMesh = LoadObject<USkeletalMesh>(nullptr, DoMannyAsset);
    if (!Cube || !Basic || !BodyMesh || (!bClose && Crowd == TEXT("static") && !MannequinMesh)) return false;
    if (Mode != TEXT("mannequin"))
    {
        HelmetMesh = DoArt<UStaticMesh>(KabutoRoot, TEXT("SM_Kabuto01"));
        if (!HelmetMesh || HelmetMesh->GetStaticMaterials().IsEmpty()) return false;
    }
    if (Mode == TEXT("armor"))
    {
        ArmorMesh = DoArt<USkeletalMesh>(DoRoot, TEXT("SK_Do01"));
        ArmorStaticMesh = DoArt<UStaticMesh>(DoRoot, TEXT("Review/SM_Do01"));
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
    const auto& Ref = BodyMesh->GetRefSkeleton();
    const int32 HeadIndex = Ref.FindBoneIndex(TEXT("head"));
    const int32 RootIndex = Ref.FindBoneIndex(TEXT("root"));
    if (HeadIndex == INDEX_NONE || RootIndex != 0) return false;
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
    DoConfigurePrimitive(GroundMesh);
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
    }
    else
    {
        auto Instances = [&](UStaticMesh* Mesh)
        {
            auto* Component = NewObject<UInstancedStaticMeshComponent>(Owner);
            Owner->AddInstanceComponent(Component);
            DoConfigurePrimitive(Component);
            Component->SetupAttachment(Root);
            Component->SetStaticMesh(Mesh);
            Component->RegisterComponent();
            ++InstanceComponents;
            return Component;
        };
        const int32 FormationCount = Count / 100;
        const int32 Across = FMath::Min(5, FormationCount);
        const int32 Rows = (FormationCount + Across - 1) / Across;
        for (int32 Formation = 0; Formation < FormationCount; ++Formation)
        {
            const bool bStatic = Crowd == TEXT("static");
            auto* BodyInstances = bStatic ? Instances(MannequinMesh) : nullptr;
            auto* HelmetInstances = bStatic && HelmetMesh ? Instances(HelmetMesh) : nullptr;
            auto* ArmorInstances = bStatic && ArmorStaticMesh ? Instances(ArmorStaticMesh) : nullptr;
            const FVector FormationPosition((Formation % Across - (Across-1)*.5)*1400, (Formation / Across - (Rows-1)*.5)*1400, 0);
            for (int32 Slot = 0; Slot < 100; ++Slot)
            {
                const FVector Position = FormationPosition + FVector((Slot%10-4.5)*110, (Slot/10-4.5)*110, 0);
                if (!bStatic) { if (!CreateCharacter(Owner, Root, Position)) return false; continue; }
                const FTransform Transform(FRotator(0,ComponentYaw,0), Position, FVector::OneVector);
                BodyInstances->AddInstance(Transform);
                ++RenderedBodies;
                if (HelmetInstances)
                {
                    HelmetInstances->AddInstance(HelmetAtReference * Transform);
                    ++RenderedHelmets;
                }
                if (ArmorInstances) { ArmorInstances->AddInstance(Transform); ++RenderedArmors; }
            }
        }
    }
    FVector Focus = FVector::ZeroVector;
    const double Yaw = Camera == TEXT("front") ? 0 : Camera == TEXT("left") ? -90 : Camera == TEXT("right") ? 90 : Camera == TEXT("rear") ? 180 : bClose ? 32 : 90;
    const FVector Direction = FRotator(bClose ? 15 : 60, Yaw, 0).Vector();
    CameraDistance = Camera == TEXT("far") ? 31000 : 11000;
    if (bClose)
    {
        const FTransform BodyTransform(FRotator(0,ComponentYaw,0));
        // Use the same waist-to-crest envelope in every comparison mode.
        // Manny's full arm/leg bounds otherwise push the torso too far away.
        auto* FramingArmor = DoArt<USkeletalMesh>(DoRoot, TEXT("SK_Do01"));
        auto* FramingHelmet = DoArt<UStaticMesh>(KabutoRoot, TEXT("SM_Kabuto01"));
        if (!FramingArmor || !FramingHelmet) return false;
        FBox Bounds = FramingArmor->GetImportedBounds().GetBox().TransformBy(BodyTransform);
        Bounds += FramingHelmet->GetBoundingBox().TransformBy(HelmetAtReference*BodyTransform);
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

void ADoReviewGameMode::UpdateInspectionPose()
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
        if ((Pose == TEXT("arms-forward") || Pose == TEXT("arms-raised")) && (Name == TEXT("upperarm_l") || Name == TEXT("upperarm_r")))
        {
            const bool bLeft = Name == TEXT("upperarm_l");
            const int32 Elbow = Ref.FindBoneIndex(bLeft ? TEXT("lowerarm_l") : TEXT("lowerarm_r"));
            if (Elbow != INDEX_NONE)
            {
                const FVector Rest = ((Ref.GetRefBonePose()[Elbow]*Transform).GetLocation()-Transform.GetLocation()).GetSafeNormal();
                const FVector Target = (Pose == TEXT("arms-forward") ? Left*(bLeft ? .12 : -.12)+Forward-FVector::UpVector*.1 : Left*(bLeft ? 1 : -1)+FVector::UpVector*.25).GetSafeNormal();
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

void ADoReviewGameMode::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (bFailed || bFinished) return;
    const double Now = FPlatformTime::Seconds();
    UpdateInspectionPose();
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

void ADoReviewGameMode::CompleteReview()
{
    bFinished = true;
    auto Json = MakeShared<FJsonObject>();
    int32 Width = 0, Height = 0;
    GetWorld()->GetFirstPlayerController()->GetViewportSize(Width, Height);
    const bool bScreenshot = IFileManager::Get().FileSize(*Screenshot) > 0;
    const bool bAnimationRequired = !Bodies.IsEmpty() && Pose == TEXT("animation") && Animation != TEXT("none");
    const bool bAnimationAdvanced = MaxAnimationPosition-MinAnimationPosition > .001;
    const bool bValid = (!bAnimationRequired || bAnimationAdvanced) && !FrameTimes.IsEmpty() && Width > 0 && Height > 0 && bScreenshot &&
        RenderedBodies == (bClose ? 1 : Count) && RenderedHelmets == (Mode != TEXT("mannequin") ? RenderedBodies : 0) &&
        RenderedArmors == (Mode == TEXT("armor") ? RenderedBodies : 0) && MaxAttachmentPositionError < .1 &&
        MaxArmorBonePositionError < .1 && MaxArmorBoneRotationError < .1 && MaxWorldScaleError < .001 &&
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
    Json->SetStringField(TEXT("animation"), !bClose && Crowd == TEXT("static") ? TEXT("static instances") : Pose == TEXT("animation") ? Animation : TEXT("component-space inspection pose"));
    Json->SetStringField(TEXT("crowd_representation"), bClose ? TEXT("single skeletal/poseable fixture") : Crowd);
    Json->SetStringField(TEXT("armor_pose_method"), Armors.IsEmpty() ? TEXT("static reference-pose instances or absent") : PoseArmor ? TEXT("copied component-space body bones") : TEXT("SetLeaderPoseComponent(body)"));
    Json->SetStringField(TEXT("engine"), FEngineVersion::Current().ToString());
    Json->SetStringField(TEXT("platform"), ANSI_TO_TCHAR(FPlatformProperties::IniPlatformName()));
    Json->SetStringField(TEXT("rhi"), GDynamicRHI ? GDynamicRHI->GetName() : TEXT("unavailable"));
    Json->SetStringField(TEXT("build"), TEXT("Development editor game; opt-in isolated Dō art review"));
    Json->SetNumberField(TEXT("requested_count"), Count);
    Json->SetNumberField(TEXT("rendered_bodies"), RenderedBodies);
    Json->SetNumberField(TEXT("rendered_helmets"), RenderedHelmets);
    Json->SetNumberField(TEXT("rendered_armors"), RenderedArmors);
    Json->SetNumberField(TEXT("instance_components"), InstanceComponents);
    Json->SetNumberField(TEXT("skeletal_components"), Bodies.Num()+Armors.Num());
    Json->SetNumberField(TEXT("camera_distance_cm"), CameraDistance);
    Json->SetNumberField(TEXT("camera_horizontal_fov"), bClose ? 40 : 55);
    Json->SetNumberField(TEXT("camera_elevation_degrees"), bClose ? 15 : 60);
    Json->SetBoolField(TEXT("body_helmet_armor_cast_shadows"), true);
    Json->SetNumberField(TEXT("warmup_seconds"), 3);
    Json->SetNumberField(TEXT("capture_seconds"), CaptureElapsed);
    Json->SetNumberField(TEXT("frames"), FrameTimes.Num());
    Json->SetNumberField(TEXT("median_fps"), FrameTimes.IsEmpty() ? 0 : 1000/DoPercentile(FrameTimes,.5));
    Json->SetNumberField(TEXT("interval_fps"), CaptureElapsed > 0 ? FrameTimes.Num()/CaptureElapsed : 0);
    Json->SetNumberField(TEXT("peak_process_physical_bytes"), double(PeakMemory));
    Json->SetNumberField(TEXT("max_attachment_position_error_cm"), MaxAttachmentPositionError);
    Json->SetNumberField(TEXT("max_armor_bone_position_error_cm"), MaxArmorBonePositionError);
    Json->SetNumberField(TEXT("max_armor_bone_rotation_error_degrees"), MaxArmorBoneRotationError);
    Json->SetNumberField(TEXT("max_component_world_scale_error"), MaxWorldScaleError);
    Json->SetBoolField(TEXT("armor_skeleton_compatible"), !ArmorMesh || ValidArmor(ArmorMesh,BodyMesh));
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
    Json->SetStringField(TEXT("measurement_notes"), TEXT("Wall frame intervals include review validation overhead. Engine CPU counters exclude idle time and may describe earlier frames; positive RHI GPU samples only, unavailable counters null. Screenshot readback follows sampling. Mesh LOD inventory is not GPU draw counts. Static crowds do not measure skinning; the optional 100-body skeletal probe includes animation/skinning and validation, not combat or population simulation. Matching bones/scale do not certify surface clearance or visual quality."));
    DoAddTiming(Json,TEXT("frame"),FrameTimes);
    DoAddTiming(Json,TEXT("game_thread"),GameTimes);
    DoAddTiming(Json,TEXT("render_thread"),RenderTimes);
    DoAddTiming(Json,TEXT("gpu"),GpuTimes);
    if (DoPercentile(DrawCalls,.5)>0) Json->SetNumberField(TEXT("median_rhi_draw_calls_all_passes"),DoPercentile(DrawCalls,.5));
    else Json->SetField(TEXT("median_rhi_draw_calls_all_passes"),MakeShared<FJsonValueNull>());
    if (DoPercentile(Primitives,.5)>0) Json->SetNumberField(TEXT("median_rhi_primitives_all_passes"),DoPercentile(Primitives,.5));
    else Json->SetField(TEXT("median_rhi_primitives_all_passes"),MakeShared<FJsonValueNull>());
    DoAddMeshInfo(Json,TEXT("helmet_mesh"),HelmetMesh);
    DoAddMeshInfo(Json,TEXT("mannequin_static_mesh"),MannequinMesh);
    DoAddMeshInfo(Json,TEXT("armor_static_mesh"),ArmorStaticMesh);
    AddSkeletalInfo(Json,TEXT("body_skeletal_mesh"),BodyMesh);
    AddSkeletalInfo(Json,TEXT("armor_skeletal_mesh"),ArmorMesh);
    FString Text;
    FJsonSerializer::Serialize(Json,TJsonWriterFactory<>::Create(&Text));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Output),true);
    if (!FFileHelper::SaveStringToFile(Text,*Output,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)) { Fail(TEXT("Could not write review JSON.")); return; }
    FString Csv = TEXT("frame,wall_ms,game_thread_ms,render_thread_ms,gpu_ms\n");
    auto Counter = [](double Value) { return Value > 0 ? FString::Printf(TEXT("%.6f"),Value) : FString(); };
    for (int32 Index=0; Index<FrameTimes.Num(); ++Index)
        Csv += FString::Printf(TEXT("%d,%.6f,%s,%s,%s\n"),Index,FrameTimes[Index],*Counter(GameTimes[Index]),*Counter(RenderTimes[Index]),*Counter(GpuTimes[Index]));
    if (!FFileHelper::SaveStringToFile(Csv,*FPaths::ChangeExtension(Output,TEXT("csv")),FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)) { Fail(TEXT("Could not write frame samples.")); return; }
    UE_LOG(LogTemp,Display,TEXT("DO_REVIEW_COMPLETE frames=%d valid=%d output=%s"),FrameTimes.Num(),bValid,*Output);
    FPlatformMisc::RequestExitWithStatus(false,bValid ? 0 : 1);
}
