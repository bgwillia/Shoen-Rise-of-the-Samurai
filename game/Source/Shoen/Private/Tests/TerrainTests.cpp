#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "ShoenSimulationSubsystem.h"
#include "FormationView.h"
#include "Tests/AutomationCommon.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "domain/Terrain.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenTerrainLoop,"Shoen.Prototype.TerrainIntegration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenTerrainLoop::RunTest(const FString&)
{
    auto* Sim=NewObject<UShoenSimulationSubsystem>(NewObject<UGameInstance>());
    if (!TestTrue(TEXT("create B society"),Sim->ResetTerrainPrototype())) return false;
    const auto Population=domain::Summarize(Sim->State).total;
    const auto Before=domain::ForecastPrototype(Sim->State,Sim->Prototype);
    if (!TestTrue(TEXT("real muster through runtime control"),Sim->MusterTerrainArmy())) return false;
    TestTrue(TEXT("representative army"),domain::Summarize(Sim->State).away>=1500);
    TestTrue(TEXT("muster removes food workers"),domain::ForecastPrototype(Sim->State,Sim->Prototype).food_produced<Before.food_produced);
    if (!TestTrue(TEXT("deploy terrain battle"),Sim->StartPrototypeBattle())) return false;
    TestTrue(TEXT("terrain mode reaches battle"),Sim->Prototype.terrain_enabled && Sim->IsPrototypeBattle());
    Sim->SetGameSpeed(0); Sim->Advance(1);
    TestEqual(TEXT("pause also pauses navigation"),Sim->Prototype.battle_steps,uint64(0));
    Sim->OrderTerrainCrossing(false);
    TestTrue(TEXT("bridge control reaches navigation"),Sim->Prototype.navigation.path_requests>0);
    Sim->SetGameSpeed(1); Sim->Advance(1);
    Sim->OrderTerrainCrossing(true);
    bool Ford=false;
    for (const auto& [Id,Path] : Sim->Prototype.navigation.player_paths) Ford|=Path.route==domain::CrossingRoute::Ford;
    TestTrue(TEXT("alternate route control"),Ford);
    Sim->RotateTerrainLine(0.2);
    for (const auto& [Id,Path] : Sim->Prototype.navigation.player_paths)
        TestTrue(TEXT("facing adjustment preserves the chosen ford"),Path.route==domain::CrossingRoute::Ford);
    FTestWorldWrapper Fixture;
    if (!TestTrue(TEXT("presentation world"),Fixture.CreateTestWorld(EWorldType::Game))) return false;
    auto* View=Fixture.GetTestWorld()->SpawnActor<AFormationView>(); View->bTerrain=true;
    const auto& Unit=Sim->Prototype.player_units.begin()->second;
    auto Formation=Sim->State.formations.at(Unit.formation_id);
    Formation.x=7200; Formation.y=0;
    View->Rebuild(Sim->State,Formation); View->UpdateCombat(Sim->State,Formation,Unit,true);
    TestEqual(TEXT("soldier rendering follows shared hill height"),View->GetActorLocation().Z,domain::TerrainHeight(Formation.x,Formation.y));
    TestEqual(TEXT("render count follows ledger combat state"),View->InstanceCount(),int32(Unit.alive));
    Fixture.DestroyTestWorld(false);
    TestTrue(TEXT("retreat through existing return transaction"),Sim->ReturnPrototypeArmy());
    TestEqual(TEXT("conserved population after B navigation"),domain::Summarize(Sim->State).total,Population);
    TestTrue(TEXT("world invariants"),domain::ValidateWorld(Sim->State).ok);
    TestTrue(TEXT("A remains independently available"),Sim->ResetPrototype());
    TestFalse(TEXT("A has no terrain navigation"),Sim->Prototype.terrain_enabled);
    return true;
}
#endif
