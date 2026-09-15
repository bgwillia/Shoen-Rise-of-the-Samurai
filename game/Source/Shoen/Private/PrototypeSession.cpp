#include "ShoenSimulationSubsystem.h"
#include "FoundationGameMode.h"
#include "FoundationPlayerController.h"
#include "Dom/JsonObject.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "domain/Battle.h"
#include "domain/Terrain.h"
#include <cmath>
#include <limits>
#include <type_traits>

namespace
{
bool LoadPrototypeRules(domain::PrototypeConfig& Config, FString& Error)
{
    FString Text;
    TSharedPtr<FJsonObject> Json;
    if (!FFileHelper::LoadFileToString(Text, *(FPaths::ProjectContentDir()/TEXT("Domain/Data/prototype.json")))
        || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Json) || !Json.IsValid())
    { Error=TEXT("Could not read prototype.json rules."); return false; }
    auto Integer = [&](const TCHAR* Key, auto& Value)
    {
        double Number=0;
        if (!Json->TryGetNumberField(Key,Number) || !FMath::IsFinite(Number) || Number<1 || Number>100000 || std::floor(Number)!=Number)
        { Error=FString::Printf(TEXT("Invalid prototype rule: %s"),Key); return false; }
        Value=static_cast<std::decay_t<decltype(Value)>>(Number); return true;
    };
#define RULE(Name) if (!Integer(TEXT(#Name),Config.Name)) return false
    RULE(food_per_farmer); RULE(food_per_person);
    RULE(labor_per_timber); RULE(labor_per_iron); RULE(labor_per_fuel);
    RULE(smiths_per_equipment); RULE(timber_per_equipment); RULE(iron_per_equipment); RULE(fuel_per_equipment);
    RULE(elite_iron_cost); RULE(elite_timber_cost); RULE(elite_fuel_cost);
    RULE(recovery_days); RULE(elite_production_period_days);
    RULE(base_food_capacity); RULE(granary_food_capacity);
#undef RULE
    const TArray<TSharedPtr<FJsonValue>>* Troops=nullptr;
    if (!Json->TryGetArrayField(TEXT("troops"),Troops) || Troops->Num()!=5)
    { Error=TEXT("prototype.json needs five troop-role tuning records."); return false; }
    for (int32 Index=0; Index<5; ++Index)
    {
        const auto Object=(*Troops)[Index]->AsObject();
        if (!Object.IsValid()) { Error=TEXT("Invalid troop tuning record."); return false; }
        auto Number = [&](const TCHAR* Key,double& Value)
        {
            double Parsed=0;
            if (!Object->TryGetNumberField(Key,Parsed) || !FMath::IsFinite(Parsed) || Parsed<=0 || Parsed>100000)
            { Error=FString::Printf(TEXT("Invalid troop rule: %s"),Key); return false; }
            Value=Parsed; return true;
        };
        auto& T=Config.troops[Index];
        if (!Number(TEXT("attack_per_soldier"),T.attack_per_soldier) || !Number(TEXT("damage_received"),T.damage_received)
            || !Number(TEXT("movement_cm_per_second"),T.movement_cm_per_second) || !Number(TEXT("range_cm"),T.range_cm)
            || !Number(TEXT("starting_morale"),T.starting_morale)) return false;
    }
    return true;
}
void FramePrototypeScene(UShoenSimulationSubsystem& Sim)
{
    if (auto* World=Sim.GetWorld())
        if (auto* Mode=Cast<AFoundationGameMode>(World->GetAuthGameMode())) Mode->FrameCurrentScenario();
}
}

bool UShoenSimulationSubsystem::ResetPrototype()
{
    if (IsProfilingFixture()) return false;
    domain::World Candidate;
    domain::PrototypeState Runtime;
    const auto Result=domain::MakePrototype(Candidate,Runtime);
    if (!Result.ok) return Report(Result,TEXT(""));
    FString Error;
    if (!LoadPrototypeRules(Runtime.config,Error)) { Message=Error; return false; }
    State=std::move(Candidate); Prototype=std::move(Runtime);
    BuildingCatalog=Prototype.catalog;
    Prototype.last_day=domain::ForecastPrototype(State,Prototype);
    ++ViewGeneration; ++WorldGeneration;
    Message=TEXT("640 people. Watch daily production; recruit with M / L / J / K / T, then F to fight.");
    return true;
}
bool UShoenSimulationSubsystem::RecruitPrototypeTroops(domain::Occupation Occupation,domain::TroopRole Role,int32 Count)
{
    if (!Prototype.enabled) return false;
    domain::EntityId Cohort=0;
    for (const auto& [Id,C] : State.cohorts)
        if (C.occupation==Occupation) { Cohort=Id; break; }
    const auto Result=domain::RecruitPrototype(State,Prototype,Cohort,Count,Role);
    if (!Report(Result,FString::Printf(TEXT("%d %s workers mobilized. Their civilian output is now lower."),Count,UTF8_TO_TCHAR(domain::OccupationName(Occupation))))) return false;
    ++ViewGeneration;
    return true;
}
bool UShoenSimulationSubsystem::StartPrototypeBattle()
{
    const auto Result=domain::BeginPrototypeBattle(State,Prototype);
    if (!Report(Result,TEXT("Battle deployed; campaign frozen. Select troops and right-click/drag orders, or G to advance."))) return false;
    ++ViewGeneration; ++WorldGeneration;
    FramePrototypeScene(*this);
    return true;
}
bool UShoenSimulationSubsystem::ReturnPrototypeArmy()
{
    const auto Result=domain::ReturnFromPrototypeBattle(State,Prototype,Prototype.phase==domain::BattlePhase::Fighting);
    if (!Result.ok) return Report(Result,TEXT(""));
    const auto& R=Prototype.last_outcome;
    Message=FString::Printf(TEXT("Home: %lld dead, %lld wounded, %lld healthy returned. P: advance 7 days to see recovery and production."),R.player_dead,R.player_wounded,R.player_alive);
    ++ViewGeneration; ++WorldGeneration;
    FramePrototypeScene(*this);
    return true;
}
void UShoenSimulationSubsystem::OrderPrototypeAttack()
{
    if (!IsPrototypeBattle() || Prototype.phase!=domain::BattlePhase::Fighting) return;
    const auto* PC=GetWorld() ? Cast<AFoundationPlayerController>(GetWorld()->GetFirstPlayerController()) : nullptr;
    int32 Issued=0;
    for (const auto& [Id,U] : Prototype.player_units)
    {
        if (U.routed || U.alive==0 || (PC && PC->Selected.Num()>0 && !PC->Selected.Contains(Id))) continue;
        const auto& F=State.formations.at(Id);
        const domain::Formation* Target=nullptr;
        double Best=std::numeric_limits<double>::max();
        for (const auto& [EnemyId,Enemy] : Prototype.enemy_units)
        {
            if (Enemy.alive==0 || Enemy.routed) continue;
            const auto& E=Prototype.enemy.formations.at(EnemyId);
            const double Distance=std::hypot(E.x-F.x,E.y-F.y);
            if (Distance<Best) { Best=Distance; Target=&E; }
        }
        if (!Target) continue;
        const double Facing=std::atan2(Target->y-F.y,Target->x-F.x);
        double Standoff=F.role==domain::TroopRole::Bow ? Prototype.config.troops[1].range_cm*.8 : 0;
        // A ranged stand-off point may fall in the river. Advance to the next
        // traversable point along that approach instead of silently rejecting it.
        while (Prototype.terrain_enabled && Standoff>0 && !domain::TerrainWalkable(Target->x-std::cos(Facing)*Standoff,Target->y-std::sin(Facing)*Standoff))
            Standoff=FMath::Max(0.,Standoff-domain::PrototypeTerrain().grid_cm);
        const auto Result=domain::IssuePrototypeOrder(State,Prototype,{Id},Target->x-std::cos(Facing)*Standoff,Target->y-std::sin(Facing)*Standoff,Facing);
        if (Result.ok) ++Issued;
    }
    Message=FString::Printf(TEXT("Advance orders sent to %d formations. Right-drag sets a chosen position and facing."),Issued);
}
bool UShoenSimulationSubsystem::FastForwardPrototype(int32 Days)
{
    if (!Prototype.enabled || IsPrototypeBattle() || Days<1 || Days>30)
    { Message=TEXT("Return to the settlement before advancing campaign days."); return false; }
    const int OldSpeed=State.speed;
    State.speed=1;
    const auto Result=domain::AdvancePrototype(State,Prototype,domain::MicrosecondsPerDay*Days);
    State.speed=OldSpeed;
    return Report(Result,FString::Printf(TEXT("Advanced %d days. Compare available workers, food balance, equipment and recovering people."),Days));
}
bool UShoenSimulationSubsystem::ResetCombatFixture(int32 PerSide)
{
    if (IsProfilingFixture()) return false;
    const auto Result=domain::MakeCombatFixture(State,Prototype,PerSide);
    if (!Report(Result,FString::Printf(TEXT("Combat scale fixture: %d vs %d. Independent finite test populations."),PerSide,PerSide))) return false;
    BuildingCatalog=Prototype.catalog;
    ++ViewGeneration; ++WorldGeneration;
    return true;
}
