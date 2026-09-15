#include "ShoenSimulationSubsystem.h"
#include "FoundationPlayerController.h"
#include "domain/Terrain.h"
#include <cmath>

namespace
{
std::vector<domain::EntityId> OrderedSelection(UShoenSimulationSubsystem& Sim)
{
    std::vector<domain::EntityId> Ids;
    const auto* PC=Sim.GetWorld() ? Cast<AFoundationPlayerController>(Sim.GetWorld()->GetFirstPlayerController()) : nullptr;
    for (const auto& [Id,U] : Sim.Prototype.player_units)
        if (U.alive>0 && !U.routed && (!PC || PC->Selected.IsEmpty() || PC->Selected.Contains(Id))) Ids.push_back(Id);
    return Ids;
}
}
bool UShoenSimulationSubsystem::ResetTerrainPrototype()
{
    if (IsProfilingFixture()) return false;
    domain::World Candidate;
    domain::PrototypeState Runtime;
    const auto Result=domain::MakeTerrainPrototype(Candidate,Runtime);
    if (!Result.ok) return Report(Result,TEXT(""));
    State=std::move(Candidate); Prototype=std::move(Runtime);
    BuildingCatalog=Prototype.catalog;
    ++ViewGeneration; ++WorldGeneration;
    Message=TEXT("Prototype B. U musters available workers and elite; F deploys. Wars share this settlement until N resets.");
    return true;
}
bool UShoenSimulationSubsystem::MusterTerrainArmy()
{
    const auto Result=domain::MusterTerrainArmy(State,Prototype);
    if (!Report(Result,TEXT("Available army mustered from remaining people and gear. F deploys; P advances recovery."))) return false;
    ++ViewGeneration;
    return true;
}
void UShoenSimulationSubsystem::OrderTerrainCrossing(bool bFord)
{
    if (!Prototype.terrain_enabled || Prototype.phase!=domain::BattlePhase::Fighting) return;
    const auto& Terrain=domain::PrototypeTerrain();
    const auto& Crossing=bFord ? Terrain.ford : Terrain.bridge;
    const double Y=(Crossing.min_y+Crossing.max_y)*.5;
    const auto Result=domain::IssueTerrainOrder(State,Prototype,OrderedSelection(*this),8000,Y,0,
        bFord ? domain::CrossingRoute::Ford : domain::CrossingRoute::Bridge);
    Report(Result,bFord ? TEXT("Selected troops take the distant ford. After crossing, right-drag toward the enemy flank.")
        : TEXT("Selected troops queue for the bridge, then spread into reserved positions. O uses the distant ford."));
}
void UShoenSimulationSubsystem::DeployTerrainLine()
{
    if (!Prototype.terrain_enabled || Prototype.phase!=domain::BattlePhase::Fighting) return;
    const auto Result=domain::IssueTerrainOrder(State,Prototype,OrderedSelection(*this),-8000,0,0);
    Report(Result,TEXT("Deploying selected formations west of the bridge. Right-drag places a line with chosen facing."));
}
void UShoenSimulationSubsystem::RotateTerrainLine(double Radians)
{
    if (!Prototype.terrain_enabled || Prototype.phase!=domain::BattlePhase::Fighting) return;
    const auto Ids=OrderedSelection(*this);
    if (Ids.empty()) return;
    double X=0,Y=0,Sin=0,Cos=0;
    for (const auto Id : Ids)
    {
        const auto& F=State.formations.at(Id);
        X+=F.target_x; Y+=F.target_y; Sin+=std::sin(F.target_facing); Cos+=std::cos(F.target_facing);
    }
    auto Route=domain::CrossingRoute::Automatic;
    bool First=true;
    for (const auto Id : Ids)
    {
        const auto Path=Prototype.navigation.player_paths.find(Id);
        const auto Current=Path==Prototype.navigation.player_paths.end() ? domain::CrossingRoute::Automatic : Path->second.route;
        if (First) { Route=Current; First=false; }
        else if (Route!=Current) { Route=domain::CrossingRoute::Automatic; break; }
    }
    const auto Result=domain::IssueTerrainOrder(State,Prototype,Ids,X/Ids.size(),Y/Ids.size(),std::atan2(Sin,Cos)+Radians,Route);
    Report(Result,TEXT("Selected line facing rotated 15 degrees. Destinations reserve space for each formation."));
}
bool UShoenSimulationSubsystem::ResetTerrainCombatFixture(int32 PerSide)
{
    if (IsProfilingFixture()) return false;
    const auto Result=domain::MakeTerrainCombatFixture(State,Prototype,PerSide);
    if (!Report(Result,FString::Printf(TEXT("Constrained combat fixture: %d vs %d, actual finite populations."),PerSide,PerSide))) return false;
    BuildingCatalog=Prototype.catalog;
    ++ViewGeneration; ++WorldGeneration;
    return true;
}
