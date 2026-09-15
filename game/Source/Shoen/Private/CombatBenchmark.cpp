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
#include "domain/Terrain.h"

namespace
{
TArray<double> TerrainNavigationTimes;

void RecordTerrainNavigationTime(double Milliseconds)
{
    TerrainNavigationTimes.Add(Milliseconds);
}

struct FTerrainBenchmarkOrders
{
    int32 Accepted = 0;
    double Milliseconds = 0;
};

FTerrainBenchmarkOrders IssueTerrainBenchmarkOrders(UShoenSimulationSubsystem& Sim, UWorld* World)
{
    FTerrainBenchmarkOrders Result;
    auto* PC=World ? Cast<AFoundationPlayerController>(World->GetFirstPlayerController()) : nullptr;
    if (!PC) return Result;

    std::vector<domain::EntityId> Main;
    std::vector<domain::EntityId> Elite;
    for (const auto& [Id,Unit] : Sim.Prototype.player_units)
    {
        if (Unit.alive==0 || Unit.routed) continue;
        const auto Formation=Sim.State.formations.find(Id);
        if (Formation==Sim.State.formations.end()) continue;
        const auto Role=Formation->second.role;
        if (Role==domain::TroopRole::RetainerInfantry || Role==domain::TroopRole::SamuraiFoot || Role==domain::TroopRole::MountedSamurai)
            Elite.push_back(Id);
        else
            Main.push_back(Id);
    }

    const auto Before=Sim.Prototype.battle.commands;
    const double Start=FPlatformTime::Seconds();
    auto Issue=[&](const std::vector<domain::EntityId>& Ids,uint8 Group,bool bFord)
    {
        if (Ids.empty()) return;
        if (!domain::AssignGroup(Sim.State,Ids,Group)) return;
        PC->Selected.Reset();
        for (const auto Id : Ids) PC->Selected.Add(Id);
        Sim.OrderTerrainCrossing(bFord);
    };
    Issue(Main,1,false);
    Issue(Elite,2,true);
    PC->Selected.Reset();
    Result.Milliseconds=(FPlatformTime::Seconds()-Start)*1000;
    Result.Accepted=int32(Sim.Prototype.battle.commands-Before);
    return Result;
}
}

void AFoundationGameMode::BeginCombatBenchmark()
{
    FParse::Value(FCommandLine::Get(),TEXT("ShoenCombatSoldiersPerSide="),CombatPerSide);
    FParse::Value(FCommandLine::Get(),TEXT("ShoenCombatBenchmarkSeconds="),CombatSeconds);
    FParse::Value(FCommandLine::Get(),TEXT("ShoenCombatBenchmarkOutput="),CombatOutput);
    if (CombatPerSide==0 || CombatSeconds<=0 || CombatOutput.IsEmpty()) return;
    FString Scenario;
    FParse::Value(FCommandLine::Get(),TEXT("ShoenScenario="),Scenario);
    bTerrainCombatBenchmark=Scenario==TEXT("terrain");
    auto* Sim=GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    const bool Reset=FApp::CanEverRender() && (bTerrainCombatBenchmark ? Sim->ResetTerrainCombatFixture(CombatPerSide) : Sim->ResetCombatFixture(CombatPerSide));
    if (!Reset)
    { UE_LOG(LogTemp,Error,TEXT("Combat benchmark needs rendered gameplay and a valid fixture.")); FPlatformMisc::RequestExit(false); return; }
    bCombatBenchmark=true;
    CombatRuns=1;
    CombatWarmupUntil=FPlatformTime::Seconds()+3;
    CombatLastFrameTime=0;
    TerrainNavigationTimes.Reset();
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
        if (CombatFrameTimes.IsEmpty())
        {
            const bool Reset=bTerrainCombatBenchmark ? Sim->ResetTerrainCombatFixture(CombatPerSide) : Sim->ResetCombatFixture(CombatPerSide);
            if (!Reset) { FPlatformMisc::RequestExit(false); return; }
            RebuildViews();
            if (bTerrainCombatBenchmark)
            {
                TerrainNavigationTimes.Reset();
                const auto Orders=IssueTerrainBenchmarkOrders(*Sim,GetWorld());
                CombatCommandTimes.Add(Orders.Milliseconds);
                CombatOrders+=Orders.Accepted;
            }
        }
        CombatLastFrameTime=FPlatformTime::Seconds();
        if (bTerrainCombatBenchmark) domain::SetTerrainTimingHook(&RecordTerrainNavigationTime);
        return;
    }
    const double FrameMs=(Now-CombatLastFrameTime)*1000;
    CombatLastFrameTime=Now;
    CombatCaptureSeconds+=FrameMs/1000;
    CombatFrameTimes.Add(FrameMs); CombatSimulationTimes.Add(LastSimulationMs);
    PeakMemoryBytes=FMath::Max(PeakMemoryBytes,FPlatformMemory::GetStats().UsedPhysical);
    CombatPeakCongestion=FMath::Max(CombatPeakCongestion,int32(Sim->Prototype.battle.peak_congestion_pairs));
    if (bTerrainCombatBenchmark)
    {
        const auto& N=Sim->Prototype.navigation;
        CombatPeakWaiting=FMath::Max(CombatPeakWaiting,static_cast<uint64>(N.waiting_formations));
        CombatPeakStuck=FMath::Max(CombatPeakStuck,static_cast<uint64>(N.stuck_formations));
        CombatPeakTerrainOverlap=FMath::Max(CombatPeakTerrainOverlap,static_cast<uint64>(N.peak_friendly_overlap_pairs));
    }
    // Exercise formation selection, group membership and actual command dispatch during combat.
    if (!bTerrainCombatBenchmark && CombatCaptureSeconds>=CombatNextOrder && Sim->Prototype.phase==domain::BattlePhase::Fighting)
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
        if (bTerrainCombatBenchmark)
        {
            const auto& N=Sim->Prototype.navigation;
            CombatPathRequests+=N.path_requests; CombatPathFailures+=N.path_failures;
            CombatCrossingCompletions+=N.crossing_completions;
            CombatBridgeCompletions+=N.bridge_completions; CombatFordCompletions+=N.ford_completions;
            CombatFlankAttackTicks+=N.flank_attack_ticks; CombatHillAttackTicks+=N.hill_attack_ticks;
            CombatPeakTerrainOverlap=FMath::Max(CombatPeakTerrainOverlap,static_cast<uint64>(N.peak_friendly_overlap_pairs));
            domain::SetTerrainTimingHook(nullptr);
        }
        const bool Reset=bTerrainCombatBenchmark ? Sim->ResetTerrainCombatFixture(CombatPerSide) : Sim->ResetCombatFixture(CombatPerSide);
        if (!Reset) { FinishCombatBenchmark(); return; }
        RebuildViews(); ++CombatRuns;
        if (bTerrainCombatBenchmark)
        {
            const auto Orders=IssueTerrainBenchmarkOrders(*Sim,GetWorld());
            CombatCommandTimes.Add(Orders.Milliseconds);
            CombatOrders+=Orders.Accepted;
        }
        CombatLastFrameTime=0;
    }
}
void AFoundationGameMode::FinishCombatBenchmark()
{
    bCombatBenchmark=false;
    domain::SetTerrainTimingHook(nullptr);
    auto* Sim=GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    const auto& R=Sim->Prototype.battle;
    CombatContactEvents+=R.contact_events; CombatRangedAttacks+=R.ranged_attacks;
    CombatPlayerCasualties+=R.player_dead+R.player_wounded; CombatEnemyCasualties+=R.enemy_dead+R.enemy_wounded;
    if (bTerrainCombatBenchmark)
    {
        const auto& N=Sim->Prototype.navigation;
        CombatPathRequests+=N.path_requests; CombatPathFailures+=N.path_failures;
        CombatCrossingCompletions+=N.crossing_completions;
        CombatBridgeCompletions+=N.bridge_completions; CombatFordCompletions+=N.ford_completions;
        CombatFlankAttackTicks+=N.flank_attack_ticks; CombatHillAttackTicks+=N.hill_attack_ticks;
        CombatPeakWaiting=FMath::Max(CombatPeakWaiting,static_cast<uint64>(N.waiting_formations));
        CombatPeakStuck=FMath::Max(CombatPeakStuck,static_cast<uint64>(N.stuck_formations));
        CombatPeakTerrainOverlap=FMath::Max(CombatPeakTerrainOverlap,static_cast<uint64>(N.peak_friendly_overlap_pairs));
    }
    if (CombatFrameTimes.IsEmpty() || !FApp::CanEverRender()) { FPlatformMisc::RequestExit(false); return; }
    CombatFrameTimes.Sort(); CombatSimulationTimes.Sort(); CombatCommandTimes.Sort(); TerrainNavigationTimes.Sort();
    auto Percentile=[](const TArray<double>& Values,double P) { return Values.IsEmpty()?0.0:Values[FMath::Min(Values.Num()-1,FMath::FloorToInt(Values.Num()*P))]; };
    auto Json=MakeShared<FJsonObject>();
    Json->SetStringField(TEXT("mode"),bTerrainCombatBenchmark ? TEXT("terrain_contact_combat") : TEXT("actual_contact_combat"));
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
    Json->SetNumberField(TEXT("peak_friendly_overlap_pairs"),bTerrainCombatBenchmark ? double(CombatPeakTerrainOverlap) : double(CombatPeakCongestion));
    Json->SetNumberField(TEXT("command_orders_accepted"),CombatOrders);
    Json->SetNumberField(TEXT("command_batch_p95_ms"),Percentile(CombatCommandTimes,.95));
    Json->SetNumberField(TEXT("formation_actors"),LiveFormations());
    Json->SetNumberField(TEXT("soldier_actors"),0);
    Json->SetNumberField(TEXT("standing_instances_at_end"),LiveInstances());
    Json->SetNumberField(TEXT("peak_process_memory_bytes"),double(PeakMemoryBytes));
    int32 Width=0,Height=0; GetWorld()->GetFirstPlayerController()->GetViewportSize(Width,Height);
    Json->SetNumberField(TEXT("viewport_width"),Width); Json->SetNumberField(TEXT("viewport_height"),Height);
    if (bTerrainCombatBenchmark)
    {
        Json->SetNumberField(TEXT("navigation_cpu_sample_count"),TerrainNavigationTimes.Num());
        Json->SetNumberField(TEXT("navigation_cpu_median_ms"),Percentile(TerrainNavigationTimes,.5));
        Json->SetNumberField(TEXT("navigation_cpu_p95_ms"),Percentile(TerrainNavigationTimes,.95));
        Json->SetNumberField(TEXT("navigation_cpu_worst_ms"),TerrainNavigationTimes.IsEmpty()?0.0:TerrainNavigationTimes.Last());
        Json->SetNumberField(TEXT("path_requests"),double(CombatPathRequests));
        Json->SetNumberField(TEXT("path_failures"),double(CombatPathFailures));
        Json->SetNumberField(TEXT("peak_waiting_formations"),double(CombatPeakWaiting));
        Json->SetNumberField(TEXT("peak_stuck_formations"),double(CombatPeakStuck));
        Json->SetNumberField(TEXT("crossing_completions"),double(CombatCrossingCompletions));
        Json->SetNumberField(TEXT("bridge_completions"),double(CombatBridgeCompletions));
        Json->SetNumberField(TEXT("ford_completions"),double(CombatFordCompletions));
        Json->SetNumberField(TEXT("flank_attack_ticks"),double(CombatFlankAttackTicks));
        Json->SetNumberField(TEXT("hill_attack_ticks"),double(CombatHillAttackTicks));
        Json->SetStringField(TEXT("limits"),TEXT("Mac Development editor/game, Metal primitive instancing, formation-level fixed terrain routing and separation; no navmesh, per-soldier collision or animation. Bridge and ford orders are issued once per fixture; completed battles restart and setup frames are excluded. Navigation CPU samples cover the core terrain movement step. Commands are scripted, not physical usability measurements."));
    }
    else Json->SetStringField(TEXT("limits"),TEXT("Mac Development editor/game, Metal primitive instancing, formation-level combat on open ground; no obstacles/navmesh/individual collision or animation. Completed battles restart; setup frames excluded. Simulation CPU samples are per rendered game tick, including ticks without a 20Hz step. Contact/ranged counters count formation attack ticks. Commands are scripted, not physical latency measurements."));
    FString Text; FJsonSerializer::Serialize(Json,TJsonWriterFactory<>::Create(&Text));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(CombatOutput),true);
    if (FFileHelper::SaveStringToFile(Text,*CombatOutput)) { UE_LOG(LogTemp,Display,TEXT("SHOEN_COMBAT_BENCHMARK_WRITTEN %s"),*CombatOutput); }
    FPlatformMisc::RequestExit(false);
}
