#include "FoundationGameMode.h"
#include "FoundationPlayerController.h"
#include "ShoenSimulationSubsystem.h"
#include "Engine/GameInstance.h"
#include "Engine/Engine.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/App.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "HAL/PlatformMemory.h"
#include "Serialization/JsonSerializer.h"
#include "domain/Battle.h"

void AFoundationGameMode::BeginCombatBenchmark()
{
    FParse::Value(FCommandLine::Get(),TEXT("ShoenCombatSoldiersPerSide="),CombatPerSide);
    FParse::Value(FCommandLine::Get(),TEXT("ShoenCombatBenchmarkSeconds="),CombatSeconds);
    FParse::Value(FCommandLine::Get(),TEXT("ShoenCombatBenchmarkOutput="),CombatOutput);
    if (CombatPerSide==0 || CombatSeconds<=0 || CombatOutput.IsEmpty()) return;
    auto* Sim=GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    if (!FApp::CanEverRender() || !Sim->ResetCombatFixture(CombatPerSide))
    { UE_LOG(LogTemp,Error,TEXT("Combat benchmark needs rendered gameplay and a valid fixture.")); FPlatformMisc::RequestExit(false); return; }
    bCombatBenchmark=true;
    CombatRuns=1;
    CombatWarmupUntil=FPlatformTime::Seconds()+3;
    CombatLastFrameTime=0;
    GEngine->Exec(GetWorld(),TEXT("t.MaxFPS 0"));
}
void AFoundationGameMode::CombatBenchmarkTick(float)
{
    const double Now=FPlatformTime::Seconds();
    auto* Sim=GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    if (Now<CombatWarmupUntil) return;
    if (CombatLastFrameTime==0)
    {
        // Start from full armies after startup warmup. Reset/rebuild frames are not timing samples.
        if (CombatFrameTimes.IsEmpty()) { Sim->ResetCombatFixture(CombatPerSide); RebuildViews(); }
        CombatLastFrameTime=FPlatformTime::Seconds();
        return;
    }
    const double FrameMs=(Now-CombatLastFrameTime)*1000;
    CombatLastFrameTime=Now;
    CombatCaptureSeconds+=FrameMs/1000;
    CombatFrameTimes.Add(FrameMs); CombatSimulationTimes.Add(LastSimulationMs);
    PeakMemoryBytes=FMath::Max(PeakMemoryBytes,FPlatformMemory::GetStats().UsedPhysical);
    CombatPeakCongestion=FMath::Max(CombatPeakCongestion,int32(Sim->Prototype.battle.peak_congestion_pairs));
    // Exercise formation selection, group membership and actual command dispatch during combat.
    if (CombatCaptureSeconds>=CombatNextOrder && Sim->Prototype.phase==domain::BattlePhase::Fighting)
    {
        CombatNextOrder+=6;
        auto* PC=Cast<AFoundationPlayerController>(GetWorld()->GetFirstPlayerController());
        std::vector<domain::EntityId> SelectedIds;
        if (PC) PC->Selected.Reset();
        for (const auto& [Id,U] : Sim->Prototype.player_units)
        {
            if (U.alive==0 || U.routed) continue;
            SelectedIds.push_back(Id);
            if (PC) PC->Selected.Add(Id);
            if (SelectedIds.size()==4) break;
        }
        const double Start=FPlatformTime::Seconds();
        if (!SelectedIds.empty()) domain::AssignGroup(Sim->State,SelectedIds,1);
        const auto Before=Sim->Prototype.battle.commands;
        Sim->OrderPrototypeAttack();
        CombatOrders+=int32(Sim->Prototype.battle.commands-Before);
        CombatCommandTimes.Add((FPlatformTime::Seconds()-Start)*1000);
    }
    if (CombatCaptureSeconds>=CombatSeconds) { FinishCombatBenchmark(); return; }
    if (Sim->Prototype.phase!=domain::BattlePhase::Fighting)
    {
        const auto& R=Sim->Prototype.battle;
        CombatContactEvents+=R.contact_events; CombatRangedAttacks+=R.ranged_attacks;
        CombatPlayerCasualties+=R.player_dead+R.player_wounded; CombatEnemyCasualties+=R.enemy_dead+R.enemy_wounded;
        Sim->ResetCombatFixture(CombatPerSide); RebuildViews(); ++CombatRuns;
        CombatLastFrameTime=0;
    }
}
void AFoundationGameMode::FinishCombatBenchmark()
{
    bCombatBenchmark=false;
    auto* Sim=GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    const auto& R=Sim->Prototype.battle;
    CombatContactEvents+=R.contact_events; CombatRangedAttacks+=R.ranged_attacks;
    CombatPlayerCasualties+=R.player_dead+R.player_wounded; CombatEnemyCasualties+=R.enemy_dead+R.enemy_wounded;
    if (CombatFrameTimes.IsEmpty() || !FApp::CanEverRender()) { FPlatformMisc::RequestExit(false); return; }
    CombatFrameTimes.Sort(); CombatSimulationTimes.Sort(); CombatCommandTimes.Sort();
    auto Percentile=[](const TArray<double>& Values,double P) { return Values.IsEmpty()?0.0:Values[FMath::Min(Values.Num()-1,FMath::FloorToInt(Values.Num()*P))]; };
    auto Json=MakeShared<FJsonObject>();
    Json->SetStringField(TEXT("mode"),TEXT("actual_contact_combat"));
    Json->SetNumberField(TEXT("requested_soldiers_per_side"),CombatPerSide);
    Json->SetNumberField(TEXT("seconds"),CombatCaptureSeconds);
    Json->SetNumberField(TEXT("warmup_seconds"),3);
    Json->SetNumberField(TEXT("battle_runs"),CombatRuns);
    Json->SetNumberField(TEXT("frames"),CombatFrameTimes.Num());
    Json->SetNumberField(TEXT("median_frame_ms"),Percentile(CombatFrameTimes,.5));
    Json->SetNumberField(TEXT("p95_frame_ms"),Percentile(CombatFrameTimes,.95));
    Json->SetNumberField(TEXT("worst_frame_ms"),CombatFrameTimes.Last());
    Json->SetNumberField(TEXT("median_fps"),1000/Percentile(CombatFrameTimes,.5));
    Json->SetNumberField(TEXT("simulation_cpu_median_ms"),Percentile(CombatSimulationTimes,.5));
    Json->SetNumberField(TEXT("simulation_cpu_p95_ms"),Percentile(CombatSimulationTimes,.95));
    Json->SetNumberField(TEXT("simulation_cpu_worst_ms"),CombatSimulationTimes.Last());
    Json->SetNumberField(TEXT("contact_events"),double(CombatContactEvents));
    Json->SetNumberField(TEXT("ranged_attacks"),double(CombatRangedAttacks));
    Json->SetNumberField(TEXT("casualties_side_a"),double(CombatPlayerCasualties));
    Json->SetNumberField(TEXT("casualties_side_b"),double(CombatEnemyCasualties));
    Json->SetNumberField(TEXT("peak_friendly_overlap_pairs"),CombatPeakCongestion);
    Json->SetNumberField(TEXT("command_orders_accepted"),CombatOrders);
    Json->SetNumberField(TEXT("command_batch_p95_ms"),Percentile(CombatCommandTimes,.95));
    Json->SetNumberField(TEXT("formation_actors"),LiveFormations());
    Json->SetNumberField(TEXT("soldier_actors"),0);
    Json->SetNumberField(TEXT("standing_instances_at_end"),LiveInstances());
    Json->SetNumberField(TEXT("peak_process_memory_bytes"),double(PeakMemoryBytes));
    int32 Width=0,Height=0; GetWorld()->GetFirstPlayerController()->GetViewportSize(Width,Height);
    Json->SetNumberField(TEXT("viewport_width"),Width); Json->SetNumberField(TEXT("viewport_height"),Height);
    Json->SetStringField(TEXT("limits"),TEXT("Mac Development editor/game, Metal primitive instancing, formation-level combat on open ground; no obstacles/navmesh/individual collision or animation. Completed battles restart; setup frames excluded. Simulation CPU samples are per rendered game tick, including ticks without a 20Hz step. Contact/ranged counters count formation attack ticks. Commands are scripted, not physical latency measurements."));
    FString Text; FJsonSerializer::Serialize(Json,TJsonWriterFactory<>::Create(&Text));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(CombatOutput),true);
    if (FFileHelper::SaveStringToFile(Text,*CombatOutput)) { UE_LOG(LogTemp,Display,TEXT("SHOEN_COMBAT_BENCHMARK_WRITTEN %s"),*CombatOutput); }
    FPlatformMisc::RequestExit(false);
}
