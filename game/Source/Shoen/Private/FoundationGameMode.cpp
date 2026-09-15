#include "FoundationGameMode.h"
#include "FormationView.h"
#include "SettlementView.h"
#include "FoundationPlayerController.h"
#include "FoundationHUD.h"
#include "StrategyCameraPawn.h"
#include "ShoenSimulationSubsystem.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/DirectionalLight.h"
#include "Engine/SkyLight.h"
#include "Components/StaticMeshComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/App.h"
#include "HAL/PlatformMemory.h"
#include "HAL/PlatformMisc.h"
#include "HAL/FileManager.h"
#include "Serialization/JsonSerializer.h"
#include "domain/Battle.h"
#include "InteractionProfiler.h"

AFoundationGameMode::AFoundationGameMode()
{
    PrimaryActorTick.bCanEverTick = true;
    DefaultPawnClass = AStrategyCameraPawn::StaticClass();
    PlayerControllerClass = AFoundationPlayerController::StaticClass();
    HUDClass = AFoundationHUD::StaticClass();
}
void AFoundationGameMode::BeginPlay()
{
    Super::BeginPlay();
    CreateEnvironment();
    FParse::Value(FCommandLine::Get(),TEXT("ShoenSoldiers="),RequestedSoldiers);
    if (RequestedSoldiers != 0 && RequestedSoldiers != 1000 && RequestedSoldiers != 4000 && RequestedSoldiers != 8000 && RequestedSoldiers != 20000)
        RequestedSoldiers = 0;
    FParse::Value(FCommandLine::Get(),TEXT("ShoenBenchmarkSeconds="),BenchmarkSeconds);
    FParse::Value(FCommandLine::Get(),TEXT("ShoenBenchmarkOutput="),BenchmarkOutput);
    bBenchmark = BenchmarkSeconds > 0 && !BenchmarkOutput.IsEmpty();
    if (bBenchmark) GEngine->Exec(GetWorld(), TEXT("t.MaxFPS 0"));
    auto* Sim = GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    FString Scenario;
    FParse::Value(FCommandLine::Get(),TEXT("ShoenScenario="),Scenario);
    if (Scenario==TEXT("settlement")) Sim->PrepareSettlementForLevel();
    else Sim->PrepareForLevel(RequestedSoldiers);
    RebuildViews();
    if (auto* PC = GetWorld()->GetFirstPlayerController())
        if (auto* Camera = Cast<AStrategyCameraPawn>(PC->GetPawn()))
        { if (Sim->IsSettlement()) Camera->FrameSettlement(); else Camera->FrameScenario(Views.Num()); Camera->bBenchmarkMotion = bBenchmark; }
    BenchmarkStart = FPlatformTime::Seconds();
    LastFrameWallTime = BenchmarkStart;
}
void AFoundationGameMode::CreateEnvironment()
{
    auto* Mesh = LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto Block = [&](FVector Location,FVector Scale,FLinearColor Color)
    {
        auto* Actor = GetWorld()->SpawnActor<AStaticMeshActor>(Location,FRotator::ZeroRotator);
        Actor->SetMobility(EComponentMobility::Movable);
        auto* Component = Actor->GetStaticMeshComponent();
        Component->SetStaticMesh(Mesh);
        Component->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")));
        Component->SetWorldScale3D(Scale);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCanEverAffectNavigation(false);
        auto* Material = Component->CreateDynamicMaterialInstance(0);
        if (Material) Material->SetVectorParameterValue(TEXT("Color"),Color);
        return Actor;
    };
    Block(FVector(0,0,-90),FVector(1700,1700,1.5),FLinearColor(.25,.30,.22));
    LabDecorations.Add(Block(FVector(-3400,-700,150),FVector(7,10,3),FLinearColor(.48,.39,.28)));
    LabDecorations.Add(Block(FVector(-3400,700,100),FVector(5,6,2),FLinearColor(.48,.39,.28)));
    LabDecorations.Add(Block(FVector(-2300,0,4),FVector(6,35,.08),FLinearColor(.44,.40,.30)));
    auto* Light = GetWorld()->SpawnActor<ADirectionalLight>(FVector(0,0,6000),FRotator(-55,-30,0));
    Light->SetMobility(EComponentMobility::Movable);
    Light->GetLightComponent()->SetIntensity(3.0f);
    auto* Sky = GetWorld()->SpawnActor<ASkyLight>();
    Sky->GetLightComponent()->SetMobility(EComponentMobility::Movable);
    Sky->GetLightComponent()->SetIntensity(0.8f);
}
void AFoundationGameMode::NewScenario(int32 Soldiers)
{
    auto* Sim = GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    Sim->ResetScenario(Soldiers);
    RebuildViews();
    auto* PC = Cast<AFoundationPlayerController>(GetWorld()->GetFirstPlayerController());
    if (PC)
    {
        PC->Selected.Reset();
        if (auto* Pawn = Cast<AStrategyCameraPawn>(PC->GetPawn())) Pawn->FrameScenario(Views.Num());
    }
}
void AFoundationGameMode::NewSettlement()
{
    auto* Sim=GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    if (!Sim->ResetSettlement()) return;
    RebuildViews();
    if (auto* PC=Cast<AFoundationPlayerController>(GetWorld()->GetFirstPlayerController()))
    {
        PC->CancelPlacement();
        if (auto* Camera=Cast<AStrategyCameraPawn>(PC->GetPawn())) Camera->FrameSettlement();
    }
}
void AFoundationGameMode::RebuildViews()
{
    auto* Sim = GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    ShoenProfile::FUseEventScope Profile(Sim->PendingPlacementProfile);
    ShoenProfile::Invalidate(ShoenProfile::EVisualChannel::Buildings);
    ShoenProfile::Invalidate(ShoenProfile::EVisualChannel::Preview);
    ShoenProfile::Invalidate(ShoenProfile::EVisualChannel::Rotation);
    ShoenProfile::Mark(TEXT("view_rebuild_begin"));
    for (const auto& View : Views) if (View) View->Destroy();
    Views.Reset();
    for (const auto& [Id,F] : Sim->State.formations)
    {
        if (domain::ActiveFormationCount(Sim->State,Id) == 0) continue;
        auto* View = GetWorld()->SpawnActor<AFormationView>();
        View->Rebuild(Sim->State,F);
        Views.Add(View);
    }
    if (!IsValid(SettlementView)) SettlementView=GetWorld()->SpawnActor<ASettlementView>();
    SettlementView->Rebuild(Sim->State);
    for (const auto& Decor : LabDecorations) if (Decor) Decor->SetActorHiddenInGame(Sim->IsSettlement());
    SeenGeneration = Sim->ViewGeneration;
    if (auto* PC = Cast<AFoundationPlayerController>(GetWorld()->GetFirstPlayerController()))
    {
        PC->Selected.Reset();
        PC->RefreshInspection();
    }
    ShoenProfile::Mark(TEXT("view_rebuild_end"));
    ShoenProfile::VisualReady(ShoenProfile::CurrentEvent(),ShoenProfile::EVisualChannel::Buildings,true,true);
    Sim->PendingPlacementProfile=0;
}
void AFoundationGameMode::Tick(float Dt)
{
    Super::Tick(Dt);
    auto* Sim = GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    const double SimStart = FPlatformTime::Seconds();
    Sim->Advance(Dt);
    LastSimulationMs = (FPlatformTime::Seconds()-SimStart)*1000;
    if (SeenGeneration != Sim->ViewGeneration) RebuildViews();
    auto* PC = Cast<AFoundationPlayerController>(GetWorld()->GetFirstPlayerController());
    for (const auto& View : Views)
    {
        const auto It = Sim->State.formations.find(View->FormationId);
        if (It != Sim->State.formations.end()) View->UpdatePose(It->second,PC && PC->Selected.Contains(View->FormationId));
    }
    if (bBenchmark) BenchmarkTick(Dt);
}
int32 AFoundationGameMode::LiveInstances() const
{
    int32 Count = 0;
    for (const auto& View : Views) Count += View->InstanceCount();
    return Count;
}
void AFoundationGameMode::BenchmarkTick(float Dt)
{
    const double Elapsed = FPlatformTime::Seconds()-BenchmarkStart;
    const double Now = FPlatformTime::Seconds();
    const double WallFrameMs = (Now-LastFrameWallTime)*1000;
    LastFrameWallTime = Now;
    auto* Sim = GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    const int32 Phase = int32(Elapsed/6.0);
    if (Phase != LastOrder)
    {
        LastOrder = Phase;
        auto* PC = Cast<AFoundationPlayerController>(GetWorld()->GetFirstPlayerController());
        if (PC) PC->Selected.Reset();
        int32 Index = 0;
        const int32 Columns = FMath::CeilToInt(FMath::Sqrt(float(Views.Num())));
        for (const auto& [Id,F] : Sim->State.formations)
        {
            const double X = (Index % Columns)*1500.0 + (Phase%2 ? 1600 : 0);
            const double Y = (Index / Columns)*1500.0 + (Phase%2 ? 1000 : 0);
            domain::IssueMove(Sim->State,{Id},X,Y,Phase%2 ? 0.5 : -0.5);
            if (PC && Index%4 == Phase%4) PC->Selected.Add(Id);
            ++Index;
        }
    }
    if (Elapsed >= 10)
    {
        FrameTimes.Add(WallFrameMs);
        SimulationTimes.Add(LastSimulationMs);
        PeakMemoryBytes = FMath::Max(PeakMemoryBytes,FPlatformMemory::GetStats().UsedPhysical);
    }
    if (Elapsed >= BenchmarkSeconds+10) FinishBenchmark();
}
void AFoundationGameMode::FinishBenchmark()
{
    bBenchmark = false;
    if (FrameTimes.IsEmpty() || !FApp::CanEverRender())
    { UE_LOG(LogTemp,Error,TEXT("Benchmark requires rendered frames.")); FPlatformMisc::RequestExit(false); return; }
    FrameTimes.Sort();
    SimulationTimes.Sort();
    const double Median = FrameTimes[FrameTimes.Num()/2];
    const double P95 = FrameTimes[FMath::Min(FrameTimes.Num()-1,FMath::FloorToInt(FrameTimes.Num()*.95))];
    auto Json = MakeShared<FJsonObject>();
    Json->SetStringField(TEXT("mode"),TEXT("rendered_primitive_movement_only"));
    Json->SetNumberField(TEXT("requested_soldiers"),RequestedSoldiers);
    Json->SetNumberField(TEXT("live_soldiers"),LiveInstances());
    Json->SetNumberField(TEXT("formations"),LiveFormations());
    Json->SetNumberField(TEXT("soldier_actors"),0);
    Json->SetNumberField(TEXT("formation_actors"),LiveFormations());
    Json->SetNumberField(TEXT("seconds"),BenchmarkSeconds);
    Json->SetNumberField(TEXT("warmup_seconds"),10);
    Json->SetNumberField(TEXT("frames"),FrameTimes.Num());
    Json->SetNumberField(TEXT("median_frame_ms"),Median);
    Json->SetNumberField(TEXT("p95_frame_ms"),P95);
    Json->SetNumberField(TEXT("median_fps"),1000/Median);
    Json->SetNumberField(TEXT("simulation_cpu_median_ms"),SimulationTimes[SimulationTimes.Num()/2]);
    Json->SetNumberField(TEXT("simulation_cpu_p95_ms"),SimulationTimes[FMath::Min(SimulationTimes.Num()-1,FMath::FloorToInt(SimulationTimes.Num()*.95))]);
    Json->SetNumberField(TEXT("peak_process_memory_bytes"),double(PeakMemoryBytes));
    Json->SetStringField(TEXT("limits"),TEXT("Editor -game, primitive rigid movement, selection and camera pan/zoom. No combat, animation, pathfinding or reference-tier certification. GPU time and input latency not measured."));
    int32 Width=0,Height=0;
    GetWorld()->GetFirstPlayerController()->GetViewportSize(Width,Height);
    Json->SetNumberField(TEXT("viewport_width"),Width);
    Json->SetNumberField(TEXT("viewport_height"),Height);
    FString Text;
    FJsonSerializer::Serialize(Json,TJsonWriterFactory<>::Create(&Text));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(BenchmarkOutput),true);
    if (FFileHelper::SaveStringToFile(Text,*BenchmarkOutput)) UE_LOG(LogTemp,Display,TEXT("SHOEN_BENCHMARK_WRITTEN %s"),*BenchmarkOutput);
    FPlatformMisc::RequestExit(false);
}
