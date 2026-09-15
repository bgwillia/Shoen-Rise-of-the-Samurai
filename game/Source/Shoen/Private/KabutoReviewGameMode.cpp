#include "KabutoReviewGameMode.h"
#include "Animation/AnimSequence.h"
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

namespace
{
constexpr double HeadHeight = 157.0;
const TCHAR* ArtRoot = TEXT("/Game/Art/Characters/Samurai/Kabuto01/");

template<typename T> T* Art(const TCHAR* Name)
{
    return LoadObject<T>(nullptr, *(FString(ArtRoot) + Name));
}

double Percentile(TArray<double> Values, double Fraction)
{
    if (Values.IsEmpty()) return 0;
    Values.Sort();
    return Values[FMath::Clamp(FMath::CeilToInt(Fraction * Values.Num()) - 1, 0, Values.Num() - 1)];
}

void AddTiming(const TSharedRef<FJsonObject>& Json, const TCHAR* Key, const TArray<double>& Samples)
{
    const TArray<double> Values = Samples.FilterByPredicate([](double Value) { return Value > 0 && FMath::IsFinite(Value); });
    auto Timing = MakeShared<FJsonObject>();
    Timing->SetNumberField(TEXT("samples"), Values.Num());
    for (const auto& Entry : TArray<TPair<FString, double>>{
        {TEXT("median_ms"), .5}, {TEXT("p95_ms"), .95}, {TEXT("worst_ms"), 1.0}})
    {
        if (Values.IsEmpty()) Timing->SetField(Entry.Key, MakeShared<FJsonValueNull>());
        else Timing->SetNumberField(Entry.Key, Percentile(Values, Entry.Value));
    }
    Json->SetObjectField(Key, Timing);
}

void AddMeshInfo(const TSharedRef<FJsonObject>& Json, const TCHAR* Key, UStaticMesh* Mesh)
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

void ConfigurePrimitive(UPrimitiveComponent* Component)
{
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCanEverAffectNavigation(false);
    Component->SetCastShadow(true);
}
}

AKabutoReviewGameMode::AKabutoReviewGameMode()
{
    PrimaryActorTick.bCanEverTick = true;
    DefaultPawnClass = nullptr;
    HUDClass = nullptr;
}

void AKabutoReviewGameMode::Fail(const FString& Reason)
{
    bFailed = true;
    UE_LOG(LogTemp, Error, TEXT("KABUTO_REVIEW_FAILED: %s"), *Reason);
    FPlatformMisc::RequestExitWithStatus(false, 1);
}

void AKabutoReviewGameMode::BeginPlay()
{
    Super::BeginPlay();
    FParse::Value(FCommandLine::Get(), TEXT("KabutoCount="), Count);
    FParse::Value(FCommandLine::Get(), TEXT("KabutoMode="), Mode);
    FParse::Value(FCommandLine::Get(), TEXT("KabutoCamera="), Camera);
    FParse::Value(FCommandLine::Get(), TEXT("KabutoAnimation="), Animation);
    FParse::Value(FCommandLine::Get(), TEXT("KabutoSeconds="), Seconds);
    FParse::Value(FCommandLine::Get(), TEXT("KabutoOutput="), Output);
    FParse::Value(FCommandLine::Get(), TEXT("KabutoScreenshot="), Screenshot);
    if (Camera == TEXT("wide")) Camera = TEXT("far");
    if (!FApp::CanEverRender()) { Fail(TEXT("Requires an actual rendered viewport; NullRHI is not a benchmark.")); return; }
    if (Count != 100 && Count != 500 && Count != 1000) { Fail(TEXT("Count must be 100, 500 or 1000.")); return; }
    if (Mode != TEXT("placeholder") && Mode != TEXT("mannequin") && Mode != TEXT("helmet")) { Fail(TEXT("Unknown comparison mode.")); return; }
    if (Camera != TEXT("close") && Camera != TEXT("front") && Camera != TEXT("side") && Camera != TEXT("rear") && Camera != TEXT("tactical") && Camera != TEXT("far")) { Fail(TEXT("Unknown camera.")); return; }
    if (Animation != TEXT("idle") && Animation != TEXT("walk") && Animation != TEXT("head") && Animation != TEXT("none")) { Fail(TEXT("Unknown animation.")); return; }
    if (!FMath::IsFinite(Seconds) || Seconds < 0 || Seconds > 600 || (Seconds > 0 && Output.IsEmpty())) { Fail(TEXT("Timed runs need an output path and duration at most 600 seconds.")); return; }
    bClose = Camera != TEXT("tactical") && Camera != TEXT("far");
    if (!CreateReview()) { Fail(TEXT("Required art, head bone, animation, or player camera is missing.")); return; }
    GEngine->Exec(GetWorld(), TEXT("t.MaxFPS 0"));
    GEngine->Exec(GetWorld(), TEXT("r.VSync 0"));
    WarmupUntil = FPlatformTime::Seconds() + 3;
    if (!Screenshot.IsEmpty())
    {
        Screenshot = FPaths::ConvertRelativePathToFull(Screenshot);
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(Screenshot), true);
        IFileManager::Get().Delete(*Screenshot);
    }
    UE_LOG(LogTemp, Display, TEXT("KABUTO_REVIEW_READY mode=%s camera=%s bodies=%d helmets=%d"), *Mode, *Camera, RenderedBodies, RenderedHelmets);
}

bool AKabutoReviewGameMode::CreateReview()
{
    auto* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto* Basic = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    if (!Cube || !Basic) return false;
    if (Mode != TEXT("placeholder"))
    {
        MannequinMesh = Art<UStaticMesh>(TEXT("Review/SM_FitMannequin"));
        if (!MannequinMesh) return false;
    }
    if (Mode == TEXT("helmet"))
    {
        HelmetMesh = Art<UStaticMesh>(TEXT("SM_Kabuto01"));
        if (!HelmetMesh || HelmetMesh->GetStaticMaterials().Num() != 1) return false;
    }
    auto* Ground = GetWorld()->SpawnActor<AStaticMeshActor>(FVector(0, 0, -8), FRotator::ZeroRotator);
    auto* GroundMesh = Ground->GetStaticMeshComponent();
    ConfigurePrimitive(GroundMesh);
    GroundMesh->SetStaticMesh(Cube);
    GroundMesh->SetWorldScale3D(FVector(5000, 5000, .15));
    GroundMesh->SetMaterial(0, Basic);
    if (auto* Mat = GroundMesh->CreateDynamicMaterialInstance(0)) Mat->SetVectorParameterValue(TEXT("Color"), FLinearColor(.22, .24, .22));
    auto* Light = GetWorld()->SpawnActor<ADirectionalLight>(FVector(0, 0, 1000), FRotator(-48, 155, 0));
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
    {
        // Broad inspection lights make lacquer and brass readable with gameplay's
        // auto-exposure and reflection features disabled. Crowds retain one sun.
        for (const auto& Position : {FVector(160,-130,245), FVector(80,160,220)})
        {
            auto* Lamp = GetWorld()->SpawnActor<ARectLight>(Position, (FVector(0,0,170)-Position).Rotation());
            Lamp->SetMobility(EComponentMobility::Movable);
            auto* Rect = Cast<URectLightComponent>(Lamp->GetLightComponent());
            Rect->SetIntensity(Position.Y < 0 ? 3500 : 1000);
            if (Position.Y > 0) Rect->SetCastShadows(false);
            Rect->SetAttenuationRadius(800);
            Rect->SetSourceWidth(120);
            Rect->SetSourceHeight(120);
        }
    }

    auto* Owner = GetWorld()->SpawnActor<AActor>();
    auto* Root = NewObject<USceneComponent>(Owner);
    Owner->SetRootComponent(Root);
    Owner->AddInstanceComponent(Root);
    Root->RegisterComponent();
    if (bClose && Mode != TEXT("placeholder"))
    {
        auto* Body = Art<USkeletalMesh>(TEXT("Review/SK_FitMannequin"));
        if (!Body) return false;
        const auto& Skeleton = Body->GetRefSkeleton();
        const int32 HeadIndex = Skeleton.FindBoneIndex(TEXT("head"));
        if (HeadIndex == INDEX_NONE) return false;
        HeadReference = Skeleton.GetRefBonePose()[HeadIndex];
        for (int32 Parent = Skeleton.GetParentIndex(HeadIndex); Parent != INDEX_NONE; Parent = Skeleton.GetParentIndex(Parent))
            HeadReference = HeadReference * Skeleton.GetRefBonePose()[Parent];
        if (!HeadReference.GetLocation().Equals(FVector(0, 0, HeadHeight), .25)) return false;
        USkinnedMeshComponent* Preview = nullptr;
        if (Animation == TEXT("head"))
        {
            HeadPreview = NewObject<UPoseableMeshComponent>(Owner);
            HeadPreview->SetSkinnedAssetAndUpdate(Body);
            Preview = HeadPreview;
        }
        else
        {
            AnimatedPreview = NewObject<USkeletalMeshComponent>(Owner);
            AnimatedPreview->SetSkeletalMesh(Body);
            AnimatedPreview->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
            Preview = AnimatedPreview;
        }
        ConfigurePrimitive(Preview);
        Owner->AddInstanceComponent(Preview);
        Preview->SetupAttachment(Root);
        Preview->SetRelativeRotation(FRotator(0, -90, 0));
        Preview->RegisterComponent();
        if (AnimatedPreview && Animation != TEXT("none"))
        {
            auto* Clip = Art<UAnimSequence>(Animation == TEXT("walk") ? TEXT("Review/A_Walk") : TEXT("Review/A_Idle"));
            if (!Clip || Clip->GetSkeleton() != Body->GetSkeleton()) return false;
            AnimatedPreview->PlayAnimation(Clip, true);
        }
        if (HelmetMesh)
        {
            AttachedHelmet = NewObject<UStaticMeshComponent>(Owner);
            Owner->AddInstanceComponent(AttachedHelmet);
            ConfigurePrimitive(AttachedHelmet);
            AttachedHelmet->SetStaticMesh(HelmetMesh);
            AttachedHelmet->SetupAttachment(Preview, TEXT("head"));
            // The FBX helmet is authored in raw mesh axes, with its pivot at the head.
            // FBX can retain the metres-to-centimetres scale on the rig root.
            // Helmet vertices are already centimetres, so cancel reference scale
            // as well as orientation, retaining the bone's animated rigid pose.
            AttachedHelmet->SetRelativeTransform(FTransform(HeadReference.GetRotation().Inverse(), FVector::ZeroVector, FTransform::GetSafeScaleReciprocal(HeadReference.GetScale3D())));
            AttachedHelmet->RegisterComponent();
            RenderedHelmets = 1;
        }
        RenderedBodies = 1;
    }
    else
    {
        auto Instances = [&](UStaticMesh* Mesh)
        {
            auto* Component = NewObject<UInstancedStaticMeshComponent>(Owner);
            Owner->AddInstanceComponent(Component);
            ConfigurePrimitive(Component);
            Component->SetupAttachment(Root);
            Component->SetStaticMesh(Mesh);
            Component->RegisterComponent();
            ++InstanceComponents;
            return Component;
        };
        const int32 Total = bClose ? 1 : Count;
        const int32 FormationCount = (Total + 99) / 100;
        const int32 Across = FMath::Min(5, FormationCount);
        const int32 Rows = (FormationCount + Across - 1) / Across;
        for (int32 Formation = 0; Formation < FormationCount; ++Formation)
        {
            auto* Bodies = Instances(Mode == TEXT("placeholder") ? Cube : MannequinMesh.Get());
            auto* Helmets = HelmetMesh ? Instances(HelmetMesh) : nullptr;
            if (Mode == TEXT("placeholder"))
            {
                Bodies->SetMaterial(0, Basic);
                if (auto* Mat = Bodies->CreateDynamicMaterialInstance(0)) Mat->SetVectorParameterValue(TEXT("Color"), FLinearColor(.28, .45, .55));
            }
            // The crowd camera looks along Y: lay the five columns across X
            // so all ten formations fit the tactical viewport.
            const FVector FormationPosition((Formation % Across - (Across - 1) * .5) * 1400, (Formation / Across - (Rows - 1) * .5) * 1400, 0);
            for (int32 Slot = 0; Slot < FMath::Min(100, Total - Formation * 100); ++Slot)
            {
                const FVector Position = bClose ? FVector::ZeroVector : FormationPosition + FVector((Slot % 10 - 4.5) * 110, (Slot / 10 - 4.5) * 110, 0);
                const bool Placeholder = Mode == TEXT("placeholder");
                Bodies->AddInstance(FTransform(FRotator(0, Placeholder ? 0 : -90, 0), Position + FVector(0, 0, Placeholder ? 90 : 0), Placeholder ? FVector(.35, .35, 1.8) : FVector::OneVector));
                ++RenderedBodies;
                if (Helmets)
                {
                    Helmets->AddInstance(FTransform(FRotator(0, -90, 0), Position + FVector(0, 0, HeadHeight), FVector::OneVector));
                    ++RenderedHelmets;
                }
            }
        }
    }
    FVector Focus(0, 0, bClose ? 170 : 0);
    CameraDistance = bClose ? 130 : Camera == TEXT("far") ? 31000 : 11000;
    const double Yaw = Camera == TEXT("front") ? 0 : Camera == TEXT("side") ? 90 : Camera == TEXT("rear") ? 180 : bClose ? 32 : 90;
    const double Elevation = bClose ? 15 : 60;
    const FVector Offset = FRotator(Elevation, Yaw, 0).Vector() * CameraDistance;
    auto* View = GetWorld()->SpawnActor<ACameraActor>(Focus + Offset, (-Offset).Rotation());
    View->GetCameraComponent()->SetFieldOfView(bClose ? 40 : 55);
    auto* Player = GetWorld()->GetFirstPlayerController();
    if (!Player) return false;
    Player->SetViewTarget(View);
    Player->bShowMouseCursor = false;
    return true;
}

void AKabutoReviewGameMode::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (bFailed || bFinished) return;
    const double Now = FPlatformTime::Seconds();
    if (HeadPreview)
    {
        FTransform Pose = HeadReference;
        const double Degrees = 38 * FMath::Sin(GetWorld()->GetTimeSeconds() * 1.1);
        Pose.SetRotation(FQuat(FVector::UpVector, FMath::DegreesToRadians(Degrees)) * HeadReference.GetRotation());
        HeadPreview->SetBoneTransformByName(TEXT("head"), Pose, EBoneSpaces::ComponentSpace);
        HeadPreview->RefreshBoneTransforms();
    }
    if (AttachedHelmet)
    {
        const auto* Parent = AttachedHelmet->GetAttachParent();
        MaxAttachmentPositionError = FMath::Max(MaxAttachmentPositionError, FVector::Distance(AttachedHelmet->GetComponentLocation(), Parent->GetSocketLocation(TEXT("head"))));
        if (!bObservedHelmetRotation) { FirstHelmetRotation = AttachedHelmet->GetComponentQuat(); bObservedHelmetRotation = true; }
        MaxHelmetRotationFromFirst = FMath::Max(MaxHelmetRotationFromFirst, FMath::RadiansToDegrees(FirstHelmetRotation.AngularDistance(AttachedHelmet->GetComponentQuat())));
    }
    if (Now < WarmupUntil) return;
    if (bSamplingComplete)
    {
        if (Screenshot.IsEmpty() || (!FScreenshotRequest::IsScreenshotRequested() && IFileManager::Get().FileSize(*Screenshot) > 0)) CompleteReview();
        else if (Now - ScreenshotRequestedAt > 15) Fail(TEXT("Timed out waiting for the rendered screenshot file."));
        return;
    }
    if (Seconds == 0) return;
    if (LastFrame == 0) { LastFrame = Now; return; }
    const double FrameMs = (Now - LastFrame) * 1000;
    LastFrame = Now;
    FrameTimes.Add(FrameMs);
    CaptureElapsed += FrameMs / 1000;
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
        if (!Screenshot.IsEmpty()) FScreenshotRequest::RequestScreenshot(Screenshot, false, false);
    }
}

void AKabutoReviewGameMode::CompleteReview()
{
    bFinished = true;
    auto Json = MakeShared<FJsonObject>();
    Json->SetBoolField(TEXT("rendered"), true);
    Json->SetBoolField(TEXT("validated"), !FrameTimes.IsEmpty() && RenderedBodies == (bClose ? 1 : Count) && RenderedHelmets == (Mode == TEXT("helmet") ? RenderedBodies : 0) && MaxAttachmentPositionError < .1);
    Json->SetStringField(TEXT("mode"), Mode);
    Json->SetStringField(TEXT("camera"), Camera);
    Json->SetStringField(TEXT("animation"), bClose && Mode != TEXT("placeholder") ? Animation : TEXT("static instances"));
    Json->SetStringField(TEXT("engine"), FEngineVersion::Current().ToString());
    Json->SetStringField(TEXT("platform"), ANSI_TO_TCHAR(FPlatformProperties::IniPlatformName()));
    Json->SetStringField(TEXT("rhi"), GDynamicRHI ? GDynamicRHI->GetName() : TEXT("unavailable"));
    Json->SetStringField(TEXT("build"), TEXT("Development editor game; opt-in isolated art review"));
    Json->SetNumberField(TEXT("requested_count"), Count);
    Json->SetNumberField(TEXT("rendered_bodies"), RenderedBodies);
    Json->SetNumberField(TEXT("rendered_helmets"), RenderedHelmets);
    Json->SetNumberField(TEXT("instance_components"), InstanceComponents);
    Json->SetNumberField(TEXT("skeletal_components"), (AnimatedPreview || HeadPreview) ? 1 : 0);
    Json->SetNumberField(TEXT("camera_distance_cm"), CameraDistance);
    Json->SetNumberField(TEXT("camera_horizontal_fov"), bClose ? 40 : 55);
    Json->SetNumberField(TEXT("camera_elevation_degrees"), bClose ? 15 : 60);
    Json->SetBoolField(TEXT("body_and_helmet_cast_shadows"), true);
    Json->SetNumberField(TEXT("warmup_seconds"), 3);
    Json->SetNumberField(TEXT("capture_seconds"), CaptureElapsed);
    Json->SetNumberField(TEXT("frames"), FrameTimes.Num());
    Json->SetNumberField(TEXT("median_fps"), FrameTimes.IsEmpty() ? 0 : 1000 / Percentile(FrameTimes, .5));
    Json->SetNumberField(TEXT("peak_process_physical_bytes"), double(PeakMemory));
    Json->SetNumberField(TEXT("max_attachment_position_error_cm"), MaxAttachmentPositionError);
    Json->SetNumberField(TEXT("max_helmet_rotation_from_first_degrees"), MaxHelmetRotationFromFirst);
    Json->SetStringField(TEXT("composed_head_reference_transform"), HeadReference.ToString());
    if (AttachedHelmet) Json->SetStringField(TEXT("helmet_world_scale"), AttachedHelmet->GetComponentScale().ToString());
    int32 Width = 0, Height = 0;
    GetWorld()->GetFirstPlayerController()->GetViewportSize(Width, Height);
    Json->SetNumberField(TEXT("viewport_width"), Width);
    Json->SetNumberField(TEXT("viewport_height"), Height);
    Json->SetStringField(TEXT("screenshot"), Screenshot);
    Json->SetBoolField(TEXT("screenshot_exists"), !Screenshot.IsEmpty() && IFileManager::Get().FileSize(*Screenshot) > 0);
    Json->SetStringField(TEXT("measurement_notes"), TEXT("Frame intervals use game-thread wall time. Engine game/render counters exclude their idle time and may describe earlier frames; GPU samples are provided by the RHI when positive. Missing counters remain null. Screenshot readback occurs after sampling. Mesh LOD geometry is asset inventory, not GPU draw counts. Crowd views are static and do not measure animation, combat or population simulation."));
    AddTiming(Json, TEXT("frame"), FrameTimes);
    AddTiming(Json, TEXT("game_thread"), GameTimes);
    AddTiming(Json, TEXT("render_thread"), RenderTimes);
    AddTiming(Json, TEXT("gpu"), GpuTimes);
    if (Percentile(DrawCalls, .5)>0) Json->SetNumberField(TEXT("median_rhi_draw_calls_all_passes"), Percentile(DrawCalls, .5));
    else Json->SetField(TEXT("median_rhi_draw_calls_all_passes"), MakeShared<FJsonValueNull>());
    if (Percentile(Primitives, .5)>0) Json->SetNumberField(TEXT("median_rhi_primitives_all_passes"), Percentile(Primitives, .5));
    else Json->SetField(TEXT("median_rhi_primitives_all_passes"), MakeShared<FJsonValueNull>());
    AddMeshInfo(Json, TEXT("helmet_mesh"), HelmetMesh);
    AddMeshInfo(Json, TEXT("mannequin_mesh"), MannequinMesh);
    FString Text;
    FJsonSerializer::Serialize(Json, TJsonWriterFactory<>::Create(&Text));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Output), true);
    if (!FFileHelper::SaveStringToFile(Text, *Output)) { Fail(TEXT("Could not write measurement JSON.")); return; }
    FString Csv = TEXT("frame,wall_ms,game_thread_ms,render_thread_ms,gpu_ms\n");
    auto Counter = [](double Value) { return Value > 0 ? FString::Printf(TEXT("%.6f"), Value) : FString(); };
    for (int32 Index = 0; Index < FrameTimes.Num(); ++Index)
        Csv += FString::Printf(TEXT("%d,%.6f,%s,%s,%s\n"), Index, FrameTimes[Index], *Counter(GameTimes[Index]), *Counter(RenderTimes[Index]), *Counter(GpuTimes[Index]));
    if (!FFileHelper::SaveStringToFile(Csv, *FPaths::ChangeExtension(Output, TEXT("csv")))) { Fail(TEXT("Could not write frame samples.")); return; }
    const bool Valid = Json->GetBoolField(TEXT("validated"));
    UE_LOG(LogTemp, Display, TEXT("KABUTO_REVIEW_COMPLETE frames=%d valid=%d output=%s"), FrameTimes.Num(), Valid, *Output);
    FPlatformMisc::RequestExitWithStatus(false, Valid ? 0 : 1);
}
