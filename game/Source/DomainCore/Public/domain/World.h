#pragma once
#include <array>
#include <cstdint>
#include <map>
#include <set>
#include <string>
#include <vector>

#ifndef DOMAINCORE_API
#define DOMAINCORE_API
#endif

namespace domain {
using EntityId = std::uint64_t;
using Quantity = std::int64_t;
using Day = std::int64_t;
constexpr std::int64_t MicrosecondsPerDay = 3'000'000;
constexpr int StartYear = 1180;
constexpr int DaysPerYear = 360;
constexpr std::size_t MaxServiceRecords = 100'000;

enum class Occupation : std::uint8_t { Agriculture, GeneralLabor, Smithing, Commerce, MaritimeWork, RetainerService };
enum class Skill : std::uint8_t { Novice, Trained, Expert, Apprentice = Novice, Master = Expert };
enum class Estate : std::uint8_t { Ordinary, Merchant, Warrior, Religious };
enum class ServiceStatus : std::uint8_t { Active, WoundedAway, Captive, Missing, DesertedAway, Dead, ReturnedHealthy, ReturnedWounded };
enum class TroopRole : std::uint8_t { Polearm, Bow, RetainerInfantry, SamuraiFoot, MountedSamurai };
enum class RngStream : std::uint8_t { Weather, Migration, Placement, Recruitment, Encounters, Combat, Diplomacy };
struct ResourceStocks {
    Quantity food = 0, timber = 0, iron = 0, treasury = 0, seed_grain = 0, fuel = 0, equipment = 0;
    bool operator==(const ResourceStocks&) const = default;
};
struct Settlement {
    EntityId id = 0; std::string name; ResourceStocks resources;
    bool operator==(const Settlement&) const = default;
};
struct District {
    EntityId id = 0, settlement_id = 0; std::string name;
    bool operator==(const District&) const = default;
};
struct Cohort {
    EntityId id = 0, settlement_id = 0, district_id = 0;
    Occupation occupation = Occupation::Agriculture;
    Skill skill = Skill::Trained; Estate estate = Estate::Ordinary;
    Quantity available = 0, dependent_or_ineligible = 0, recovering_home = 0;
    bool operator==(const Cohort&) const = default;
};
struct Origin {
    EntityId settlement_id = 0, district_id = 0, cohort_id = 0;
    Occupation occupation = Occupation::Agriculture;
    Skill skill = Skill::Trained; Estate estate = Estate::Ordinary;
    bool operator==(const Origin&) const = default;
};
struct ServiceRecord {
    EntityId id = 0; Origin origin; ServiceStatus status = ServiceStatus::Active;
    EntityId formation_id = 0;
    bool operator==(const ServiceRecord&) const = default;
};
struct Formation {
    EntityId id = 0; std::string name; std::vector<EntityId> service_ids;
    double x = 0, y = 0, facing = 0, target_x = 0, target_y = 0, target_facing = 0;
    bool moving = false; std::uint8_t control_group = 0; bool demobilized = false;
    TroopRole role = TroopRole::Polearm;
    bool operator==(const Formation&) const = default;
};
struct General {
    EntityId id = 0; std::string name;
    int command = 50, coordination = 50, scouting = 50, secrecy = 50, terrain_knowledge = 50, logistics = 50;
    bool operator==(const General&) const = default;
};
struct RandomState {
    std::uint64_t state = 1, counter = 0;
    bool operator==(const RandomState&) const = default;
};
struct World {
    std::map<EntityId, Settlement> settlements;
    std::map<EntityId, District> districts;
    std::map<EntityId, Cohort> cohorts;
    std::map<EntityId, ServiceRecord> services;
    std::map<EntityId, Formation> formations;
    std::map<EntityId, General> generals;
    Day campaign_day = 0; int speed = 1; std::int64_t subday_microseconds = 0;
    std::int64_t formation_substep_microseconds = 0;
    std::uint64_t revision = 0; EntityId next_id = 1, next_transaction_id = 1;
    std::array<RandomState, 7> rng{};
    std::set<EntityId> applied_transaction_ids;
    Quantity initial_population = 0, births = 0, admitted_immigrants = 0, recorded_emigrants = 0;
    bool operator==(const World&) const = default;
};
struct Result {
    bool ok = false; std::string error; EntityId id = 0;
    explicit operator bool() const { return ok; }
};
struct Disposition { EntityId service_id = 0; ServiceStatus status = ServiceStatus::Active; };
struct Outcome {
    EntityId transaction_id = 0, formation_id = 0; std::uint64_t expected_revision = 0;
    std::vector<Disposition> dispositions;
};
struct PopulationSummary {
    Quantity available = 0, dependent = 0, recovering = 0, away = 0, dead = 0, living = 0, total = 0;
    bool operator==(const PopulationSummary&) const = default;
};
DOMAINCORE_API World MakeFoundationWorld(); // Settlement 1, district 2, agricultural cohort 3 (200 people).
DOMAINCORE_API World MakeScaleWorld(Quantity soldiers); // Finite civilian source; 100 people per formation.
DOMAINCORE_API Result ValidateWorld(const World&);
DOMAINCORE_API Result Mobilize(World&, EntityId cohort_id, Quantity count);
DOMAINCORE_API Result ApplyOutcome(World&, const Outcome&);
DOMAINCORE_API Result Demobilize(World&, EntityId formation_id);
DOMAINCORE_API PopulationSummary Summarize(const World&, EntityId district_id = 0);
DOMAINCORE_API Quantity ActiveFormationCount(const World&, EntityId formation_id); // Healthy and wounded still attached.
DOMAINCORE_API Result SetSpeed(World&, int speed);
DOMAINCORE_API Result AdvanceRealTime(World&, std::int64_t real_microseconds);
DOMAINCORE_API void AdvanceOneDay(World&);
DOMAINCORE_API std::uint64_t NextRandom(World&, RngStream);
DOMAINCORE_API const char* OccupationName(Occupation);
DOMAINCORE_API const char* StatusName(ServiceStatus);
}
