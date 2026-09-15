#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "ShoenSimulationSubsystem.h"
#include "FormationView.h"
#include "Tests/AutomationCommon.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenPrototypeLoop, "Shoen.Prototype.IntegratedLoop",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenPrototypeLoop::RunTest(const FString&)
{
    auto* Sim=NewObject<UShoenSimulationSubsystem>(NewObject<UGameInstance>());
    if (!TestTrue(TEXT("load real prototype content"),Sim->ResetPrototype())) return false;
    TestEqual(TEXT("640 real people"),domain::Summarize(Sim->State).total,int64(640));
    const auto Baseline=domain::ForecastPrototype(Sim->State,Sim->Prototype);
    TestTrue(TEXT("mobilize farmers"),Sim->RecruitPrototypeTroops(domain::Occupation::Agriculture,domain::TroopRole::Polearm,100));
    TestTrue(TEXT("equip archers"),Sim->RecruitPrototypeTroops(domain::Occupation::Agriculture,domain::TroopRole::Bow,50));
    TestTrue(TEXT("equip smaller samurai formation"),Sim->RecruitPrototypeTroops(domain::Occupation::RetainerService,domain::TroopRole::SamuraiFoot,20));
    TestTrue(TEXT("civilian agriculture really declines"),domain::ForecastPrototype(Sim->State,Sim->Prototype).food_produced<Baseline.food_produced);
    const auto CampaignDay=Sim->State.campaign_day;
    TestTrue(TEXT("start actual combat"),Sim->StartPrototypeBattle());
    TestFalse(TEXT("battle is not the settlement input mode"),Sim->IsSettlement());
    Sim->SetGameSpeed(0); Sim->Advance(5);
    TestEqual(TEXT("battle pause binding"),Sim->Prototype.battle_steps,uint64(0));
    Sim->SetGameSpeed(1); Sim->OrderPrototypeAttack(); Sim->Advance(50);
    TestEqual(TEXT("campaign frozen during combat"),Sim->State.campaign_day,CampaignDay);
    TestTrue(TEXT("melee happened"),Sim->Prototype.battle.contact_events>0);
    TestTrue(TEXT("ranged happened"),Sim->Prototype.battle.ranged_attacks>0);
    TestTrue(TEXT("real player casualties"),Sim->Prototype.battle.player_dead+Sim->Prototype.battle.player_wounded>0);
    FTestWorldWrapper Fixture;
    if (!TestTrue(TEXT("presentation world"),Fixture.CreateTestWorld(EWorldType::Game))) return false;
    auto* View=Fixture.GetTestWorld()->SpawnActor<AFormationView>();
    const auto& Unit=Sim->Prototype.player_units.begin()->second;
    const auto& Formation=Sim->State.formations.at(Unit.formation_id);
    View->Rebuild(Sim->State,Formation);
    View->UpdateCombat(Sim->State,Formation,Unit,true);
    TestEqual(TEXT("standing instances match authoritative combat survivors"),View->InstanceCount(),int32(Unit.alive));
    Fixture.DestroyTestWorld(false);
    TestTrue(TEXT("return army"),Sim->ReturnPrototypeArmy());
    const auto After=domain::Summarize(Sim->State);
    TestEqual(TEXT("all people conserved"),After.total,int64(640));
    TestEqual(TEXT("dead persisted"),After.dead,Sim->Prototype.last_outcome.player_dead);
    TestEqual(TEXT("wounded unavailable"),After.recovering,Sim->Prototype.last_outcome.player_wounded);
    TestFalse(TEXT("cannot return twice"),Sim->ReturnPrototypeArmy());
    TestTrue(TEXT("fast-forward consequence and recovery"),Sim->FastForwardPrototype(7));
    TestTrue(TEXT("production permanently below prewar potential"),domain::ForecastPrototype(Sim->State,Sim->Prototype).food_produced<Baseline.food_produced);
    TestTrue(TEXT("population/origin/resource invariants after loop"),domain::ValidateWorld(Sim->State).ok);
    return true;
}
#endif
