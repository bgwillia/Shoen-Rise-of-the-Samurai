#include "ShoenSimulationSubsystem.h"
#include "Dom/JsonObject.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Serialization/JsonSerializer.h"

// Opt-in F7 observation only: never advances time, creates troops or edits a save slot.
bool UShoenSimulationSubsystem::WriteTerrainSnapshot()
{
    if (!Prototype.terrain_enabled) return false;
    auto Json=MakeShared<FJsonObject>();
    Json->SetStringField(TEXT("scenario"),TEXT("prototype_b_terrain"));
    Json->SetStringField(TEXT("phase"),UTF8_TO_TCHAR(domain::BattlePhaseName(Prototype.phase)));
    Json->SetNumberField(TEXT("campaign_day"),double(State.campaign_day));
    Json->SetNumberField(TEXT("battle_seconds"),Prototype.battle.seconds);
    Json->SetNumberField(TEXT("world_revision"),double(State.revision));
    const auto Population=domain::Summarize(State);
    Json->SetNumberField(TEXT("population_total"),double(Population.total));
    Json->SetNumberField(TEXT("available"),double(Population.available));
    Json->SetNumberField(TEXT("away"),double(Population.away));
    Json->SetNumberField(TEXT("recovering"),double(Population.recovering));
    Json->SetNumberField(TEXT("dead"),double(Population.dead));
    Json->SetNumberField(TEXT("elite_equipment"),double(Prototype.elite_equipment));
    const auto Forecast=domain::ForecastPrototype(State,Prototype);
    Json->SetNumberField(TEXT("food_produced_per_day"),double(Forecast.food_produced));
    Json->SetNumberField(TEXT("food_consumed_per_day"),double(Forecast.food_consumed));
    Json->SetNumberField(TEXT("basic_equipment_per_day"),double(Forecast.basic_equipment_produced));
    if (!State.settlements.empty())
    {
        const auto& R=State.settlements.begin()->second.resources;
        Json->SetNumberField(TEXT("food_stock"),double(R.food));
        Json->SetNumberField(TEXT("basic_equipment_stock"),double(R.equipment));
    }
    TArray<TSharedPtr<FJsonValue>> Cohorts;
    for (const auto& [Id,C] : State.cohorts)
    {
        auto J=MakeShared<FJsonObject>(); J->SetNumberField(TEXT("id"),double(Id));
        J->SetStringField(TEXT("occupation"),UTF8_TO_TCHAR(domain::OccupationName(C.occupation)));
        J->SetNumberField(TEXT("available"),double(C.available)); J->SetNumberField(TEXT("recovering"),double(C.recovering_home));
        Cohorts.Add(MakeShared<FJsonValueObject>(J));
    }
    Json->SetArrayField(TEXT("cohorts"),Cohorts);
    const auto& N=Prototype.navigation;
#define NAV(Field) Json->SetNumberField(TEXT(#Field),double(N.Field))
    NAV(path_requests); NAV(path_failures); NAV(waiting_formations); NAV(stuck_formations);
    NAV(crossing_completions); NAV(bridge_completions); NAV(ford_completions);
    NAV(friendly_overlap_pairs); NAV(peak_friendly_overlap_pairs); NAV(flank_attack_ticks); NAV(hill_attack_ticks);
#undef NAV
    const auto& R=IsPrototypeBattle() ? Prototype.battle : Prototype.last_outcome;
#define REPORT(Field) Json->SetNumberField(TEXT(#Field),double(R.Field))
    REPORT(player_started); REPORT(player_alive); REPORT(player_dead); REPORT(player_wounded);
    REPORT(player_elite_started); REPORT(player_elite_dead); REPORT(player_elite_wounded);
    REPORT(enemy_started); REPORT(enemy_alive); REPORT(enemy_dead); REPORT(enemy_wounded);
    REPORT(contact_events); REPORT(ranged_attacks);
#undef REPORT
    TArray<TSharedPtr<FJsonValue>> Formations;
    for (const auto& [Id,F] : State.formations)
    {
        if (F.demobilized || F.service_ids.empty()) continue;
        auto J=MakeShared<FJsonObject>(); J->SetNumberField(TEXT("id"),double(Id));
        J->SetNumberField(TEXT("role"),int32(F.role)); J->SetNumberField(TEXT("x"),F.x); J->SetNumberField(TEXT("y"),F.y);
        J->SetNumberField(TEXT("facing"),F.facing); J->SetNumberField(TEXT("group"),F.control_group);
        J->SetNumberField(TEXT("strength"),double(domain::ActiveFormationCount(State,Id)));
        if (IsPrototypeBattle())
            if (const auto* U=domain::LookupCombatUnit(Prototype,domain::CombatSide::Player,Id))
            { J->SetNumberField(TEXT("alive"),double(U->alive)); J->SetNumberField(TEXT("morale"),U->morale); J->SetNumberField(TEXT("fatigue"),U->fatigue); J->SetBoolField(TEXT("routed"),U->routed); }
        Formations.Add(MakeShared<FJsonValueObject>(J));
    }
    Json->SetArrayField(TEXT("formations"),Formations);
    const FString Path=FPaths::ProjectSavedDir()/TEXT("Profiling")/FString::Printf(TEXT("terrain-%s-%llu.json"),*FDateTime::UtcNow().ToString(TEXT("%Y%m%d-%H%M%S")),uint64(GFrameCounter));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path),true);
    FString Text; FJsonSerializer::Serialize(Json,TJsonWriterFactory<>::Create(&Text));
    const bool Saved=FFileHelper::SaveStringToFile(Text,*Path);
    Message=Saved ? TEXT("F7 terrain state snapshot saved under Saved/Profiling.") : TEXT("Terrain snapshot write failed.");
    return Saved;
}
