#include "StrategyCameraPawn.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/PlayerController.h"
#include "Components/SceneComponent.h"
#include "InputCoreTypes.h"
#include "TerrainSuitability.h"
#include "LandscapeProxy.h"
#include "EngineUtils.h"

AStrategyCameraPawn::AStrategyCameraPawn()
{
    PrimaryActorTick.bCanEverTick = true;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Focus"));
    Arm = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraArm"));
    Arm->SetupAttachment(RootComponent);
    Arm->bDoCollisionTest = false;
    Arm->TargetArmLength = TargetZoom;
    Arm->SetRelativeRotation(FRotator(-60, TargetYaw, 0));
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
    Camera->SetupAttachment(Arm);
    Camera->FieldOfView = 55;
}
void AStrategyCameraPawn::FrameScenario(int32 Count)
{
    bLandscapeWorld=false;
    const int32 Columns = FMath::Max(1, FMath::CeilToInt(FMath::Sqrt(float(Count))));
    TargetFocus = FVector((Columns - 1) * 750.0, (Columns - 1) * 750.0, 0);
    TargetZoom = FMath::Clamp(Columns * 2700.0f, 6000.0f, 50000.0f);
    ScenarioFocus = TargetFocus;
    ScenarioZoom = TargetZoom;
    SetActorLocation(TargetFocus);
    Arm->TargetArmLength = TargetZoom;
}
void AStrategyCameraPawn::FrameSettlement()
{
    if (ATerrainSuitability::Find(GetWorld())) { FrameLandscape(); return; }
    bLandscapeWorld=false;
    TargetFocus = FVector(-1700,0,0);
    TargetZoom = 16000;
    TargetYaw = -90;
    ScenarioFocus = TargetFocus;
    ScenarioZoom = TargetZoom;
    SetActorLocation(TargetFocus);
    Arm->TargetArmLength = TargetZoom;
    Arm->SetRelativeRotation(FRotator(-60,TargetYaw,0));
}
void AStrategyCameraPawn::FrameLandscape(bool bOverview)
{
    bLandscapeWorld=true;
    LandscapeBounds=FBox(ForceInit);
    for (TActorIterator<ALandscapeProxy> It(GetWorld()); It; ++It)
        LandscapeBounds+=It->GetComponentsBoundingBox(true);
    const float Span=LandscapeBounds.IsValid ? float(FMath::Max(LandscapeBounds.GetSize().X,LandscapeBounds.GetSize().Y)) : 150000.f;
    LandscapeMaxZoom=FMath::Max(60000.f,Span*3.2f);
    // Native TerrainBase_01's village shelf; the camera follows the queried
    // ground elevation while panning, including the higher outer ridges.
    TargetFocus=bOverview && LandscapeBounds.IsValid ? LandscapeBounds.GetCenter() : FVector(22000,-23000,1950);
    TargetFocus.X-=bOverview ? Span*.22f : 2300.f;
    if (const auto* Suitability=ATerrainSuitability::Find(GetWorld()))
    {
        FHitResult Hit;
        if (Suitability->TraceGround(TargetFocus+FVector(0,0,200000),TargetFocus-FVector(0,0,200000),Hit)) TargetFocus.Z=Hit.ImpactPoint.Z;
    }
    TargetZoom=bOverview ? Span*2.5f : 20000.f;
    TargetYaw=-90;
    ScenarioFocus=TargetFocus; ScenarioZoom=TargetZoom;
    SetActorLocation(TargetFocus);
    Arm->TargetArmLength=TargetZoom;
    Arm->SetRelativeRotation(FRotator(-60,TargetYaw,0));
}
float AStrategyCameraPawn::Zoom() const { return Arm->TargetArmLength; }
void AStrategyCameraPawn::FramePrototype(FVector Center, float Span)
{
    bLandscapeWorld=false;
    // Reserve the existing sidebar's screen space when framing either scene.
    TargetFocus = Center - FVector(Span * .23f, 0, 0);
    TargetZoom = FMath::Clamp(Span * 1.9f, 11000.0f, 58000.0f);
    TargetYaw = -90;
    ScenarioFocus = TargetFocus; ScenarioZoom = TargetZoom;
    SetActorLocation(TargetFocus);
    Arm->TargetArmLength = TargetZoom;
    Arm->SetRelativeRotation(FRotator(-60,TargetYaw,0));
}
void AStrategyCameraPawn::Tick(float Dt)
{
    Super::Tick(Dt);
    auto* PC = Cast<APlayerController>(GetController());
    if (!PC) return;
    const FVector PreviousFocus=TargetFocus;
    if (bBenchmarkMotion)
    {
        SweepTime += Dt;
        TargetFocus = ScenarioFocus + FVector(FMath::Sin(SweepTime*.18)*1500,FMath::Cos(SweepTime*.16)*1500,0);
        TargetZoom = ScenarioZoom*(0.9f+0.1f*FMath::Sin(SweepTime*.12f));
        TargetYaw = -90 + FMath::Sin(SweepTime*.08f)*16;
    }
    const FRotator Heading(0, TargetYaw, 0);
    const FVector Forward = Heading.Vector();
    const FVector Right = FRotationMatrix(Heading).GetUnitAxis(EAxis::Y);
    FVector Input = FVector::ZeroVector;
    if (PC->IsInputKeyDown(EKeys::W)) Input += Forward;
    if (PC->IsInputKeyDown(EKeys::S)) Input -= Forward;
    if (PC->IsInputKeyDown(EKeys::D)) Input += Right;
    if (PC->IsInputKeyDown(EKeys::A) && !PC->IsInputKeyDown(EKeys::LeftControl) && !PC->IsInputKeyDown(EKeys::RightControl)) Input -= Right;
    TargetFocus += Input.GetClampedToMaxSize(1) * (TargetZoom * 0.65f) * Dt;
    float DX = 0, DY = 0;
    PC->GetInputMouseDelta(DX, DY);
    if (PC->IsInputKeyDown(EKeys::MiddleMouseButton))
    {
        if (PC->IsInputKeyDown(EKeys::LeftShift) || PC->IsInputKeyDown(EKeys::RightShift))
            TargetFocus += (-Right * DX + Forward * DY) * TargetZoom * 0.0015f;
        else TargetYaw += DX * 0.45f;
    }
    if (PC->IsInputKeyDown(EKeys::Q)) TargetYaw -= 65 * Dt;
    if (PC->IsInputKeyDown(EKeys::E)) TargetYaw += 65 * Dt;
    if (PC->WasInputKeyJustPressed(EKeys::MouseScrollUp)) TargetZoom *= 0.86f;
    if (PC->WasInputKeyJustPressed(EKeys::MouseScrollDown)) TargetZoom *= 1.16f;
    TargetZoom = FMath::Clamp(TargetZoom, 1400.0f, bLandscapeWorld ? LandscapeMaxZoom : 60000.0f);
    TargetFocus.X = FMath::Clamp(TargetFocus.X, bLandscapeWorld && LandscapeBounds.IsValid ? LandscapeBounds.Min.X : -35000., bLandscapeWorld && LandscapeBounds.IsValid ? LandscapeBounds.Max.X : 50000.);
    TargetFocus.Y = FMath::Clamp(TargetFocus.Y, bLandscapeWorld && LandscapeBounds.IsValid ? LandscapeBounds.Min.Y : -35000., bLandscapeWorld && LandscapeBounds.IsValid ? LandscapeBounds.Max.Y : 50000.);
    if (bLandscapeWorld && !TargetFocus.Equals(PreviousFocus))
        if (const auto* Suitability=ATerrainSuitability::Find(GetWorld()))
        {
            FHitResult Hit;
            if (Suitability->TraceGround(TargetFocus+FVector(0,0,200000),TargetFocus-FVector(0,0,200000),Hit)) TargetFocus.Z=Hit.ImpactPoint.Z;
        }
    SetActorLocation(FMath::VInterpTo(GetActorLocation(), TargetFocus, Dt, 9));
    Arm->TargetArmLength = FMath::FInterpTo(Arm->TargetArmLength, TargetZoom, Dt, 10);
    Arm->SetRelativeRotation(FMath::RInterpTo(Arm->GetRelativeRotation(), FRotator(-60, TargetYaw, 0), Dt, 10));
}
