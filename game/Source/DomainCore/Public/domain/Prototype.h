#pragma once
#include "domain/World.h"

namespace domain {
// Prototype-only runtime state. Not part of the versioned World save format.
enum class BattlePhase : std::uint8_t { Settlement, Fighting, Victory, Defeat };
enum class CombatSide : std::uint8_t { Player, Enemy };
struct CombatTuning {
    double attack_per_soldier = .028; // casualties/second before defense/fatigue
    double damage_received = 1.0, movement_cm_per_second = 600;
    double range_cm = 700, starting_morale = 100;
    bool operator==(const CombatTuning&) const = default;
};
struct PrototypeConfig {
    Quantity food_per_farmer = 3, food_per_person = 1;
    Quantity labor_per_timber = 8, labor_per_iron = 20, labor_per_fuel = 10;
    Quantity smiths_per_equipment = 5, timber_per_equipment = 1, iron_per_equipment = 1, fuel_per_equipment = 1;
    Quantity elite_iron_cost = 3, elite_timber_cost = 2, elite_fuel_cost = 2;
    Quantity ordinary_formation_size = 50, elite_formation_size = 20;
    Day recovery_days = 7, elite_production_period_days = 3;
    Quantity base_food_capacity = 1500, granary_food_capacity = 8000;
    std::array<CombatTuning,5> troops{{
        {.028,1.0,600,700,100}, {.024,1.10,580,5000,85},
        {.072,.55,640,700,120}, {.09,.45,660,700,130}, {.075,.65,1000,850,120}}};
    bool operator==(const PrototypeConfig&) const = default;
};
struct DailyEconomy {
    Quantity farmers=0, laborers=0, smiths=0, retainers=0;
    Quantity food_produced=0, food_consumed=0, timber_produced=0, iron_produced=0, fuel_produced=0;
    Quantity basic_equipment_produced=0, elite_equipment_produced=0;
    Quantity food_shortfall=0, housing_capacity=0, food_capacity=0;
    bool operator==(const DailyEconomy&) const = default;
};
struct RecoveryEntry {
    EntityId service_id=0, cohort_id=0; Day due_day=0;
    bool operator==(const RecoveryEntry&) const = default;
};
struct CombatUnit {
    EntityId formation_id=0; CombatSide side=CombatSide::Player;
    Quantity starting=0, alive=0, dead=0, wounded=0;
    double morale=100, fatigue=0, casualty_fraction=0;
    bool routed=false, engaged=false;
    EntityId target_formation_id=0; bool ranged_attacking=false;
    // Aligned with the source Formation::service_ids; no per-soldier AI.
    std::vector<ServiceStatus> service_states;
    bool operator==(const CombatUnit&) const = default;
};
struct BattleReport {
    Quantity player_started=0, player_alive=0, player_dead=0, player_wounded=0;
    Quantity enemy_started=0, enemy_alive=0, enemy_dead=0, enemy_wounded=0;
    std::uint64_t contact_events=0, ranged_attacks=0, melee_casualties=0, ranged_casualties=0;
    std::uint64_t peak_congestion_pairs=0, commands=0;
    double seconds=0; bool victory=false, retreated=false;
    bool operator==(const BattleReport&) const = default;
};
struct PrototypeState {
    bool enabled=false; BattlePhase phase=BattlePhase::Settlement;
    PrototypeConfig config;
    World enemy;
    BuildingCatalog catalog;
    Quantity elite_equipment=0;
    std::map<EntityId,CombatUnit> player_units, enemy_units;
    std::vector<RecoveryEntry> recovery;
    DailyEconomy last_day;
    BattleReport battle, last_outcome;
    std::int64_t battle_substep_microseconds=0;
    std::uint64_t battle_steps=0;
    bool operator==(const PrototypeState&) const = default;
};
DOMAINCORE_API Result MakePrototype(World&, PrototypeState&);
DOMAINCORE_API DailyEconomy ForecastPrototype(const World&, const PrototypeState&);
DOMAINCORE_API Result AdvancePrototype(World&, PrototypeState&, std::int64_t real_microseconds);
DOMAINCORE_API Result RecruitPrototype(World&, PrototypeState&, EntityId cohort_id, Quantity count, TroopRole);
DOMAINCORE_API Result BeginPrototypeBattle(World&, PrototypeState&, Quantity enemy_count=0);
DOMAINCORE_API Result ReturnFromPrototypeBattle(World&, PrototypeState&, bool retreat=false);
DOMAINCORE_API Result MakeCombatFixture(World&, PrototypeState&, Quantity soldiers_per_side);
DOMAINCORE_API const CombatUnit* LookupCombatUnit(const PrototypeState&, CombatSide, EntityId formation_id);
DOMAINCORE_API Result IssuePrototypeOrder(World&, PrototypeState&, const std::vector<EntityId>& formation_ids, double x, double y, double facing);
DOMAINCORE_API const char* BattlePhaseName(BattlePhase);
}
