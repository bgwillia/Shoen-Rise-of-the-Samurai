#pragma once
#include "domain/World.h"
namespace domain {
struct PrototypeState;
enum class CrossingRoute : std::uint8_t { Automatic, Bridge, Ford };
struct TerrainRect {
 double min_x=0,min_y=0,max_x=0,max_y=0;
 bool operator==(const TerrainRect&) const = default;
};
struct TerrainGeometry {
 TerrainRect bounds{-25600,-25600,25600,25600};
 TerrainRect river{-1000,-25600,1000,25600};
 TerrainRect bridge{-2400,-900,2400,900};
 TerrainRect ford{-2400,7200,2400,12000};
 TerrainRect forest{-11200,-11200,-3200,-3200};
 TerrainRect hill{3200,-4800,11200,4800};
 double hill_height_cm=550, grid_cm=1600, formation_radius_cm=720;
 bool operator==(const TerrainGeometry&) const = default;
};
struct TerrainPath {
 Point2 destination, cell, transit;
 bool in_transit=false;
 std::vector<Point2> waypoints;
 std::size_t next_waypoint=0;
 CrossingRoute route=CrossingRoute::Automatic;
 double blocked_seconds=0;
 bool crossed=false, had_crossing=false;
 bool operator==(const TerrainPath&) const = default;
};
struct TerrainNavigation {
 std::map<EntityId,TerrainPath> player_paths,enemy_paths;
 std::uint64_t path_requests=0, path_failures=0, waiting_formations=0, stuck_formations=0;
 std::uint64_t crossing_completions=0, bridge_completions=0, ford_completions=0;
 std::uint64_t friendly_overlap_pairs=0, peak_friendly_overlap_pairs=0, flank_attack_ticks=0, hill_attack_ticks=0;
 bool operator==(const TerrainNavigation&) const = default;
};
using TerrainTimingHook=void(*)(double milliseconds);
DOMAINCORE_API void SetTerrainTimingHook(TerrainTimingHook);
DOMAINCORE_API const TerrainGeometry& PrototypeTerrain();
DOMAINCORE_API bool TerrainWalkable(double x,double y,double radius_cm=720);
DOMAINCORE_API double TerrainHeight(double x,double y);
DOMAINCORE_API double TerrainMovementFactor(double x,double y);
DOMAINCORE_API Result MakeTerrainPrototype(World&,PrototypeState&);
DOMAINCORE_API Result MusterTerrainArmy(World&,PrototypeState&); // Available people and gear only; never replenishes society.
DOMAINCORE_API Result MakeTerrainCombatFixture(World&,PrototypeState&,Quantity soldiers_per_side);
DOMAINCORE_API Result IssueTerrainOrder(World&,PrototypeState&,const std::vector<EntityId>&,double x,double y,double facing,CrossingRoute route=CrossingRoute::Automatic);
// Shared core integration hooks, not separate simulation clocks.
DOMAINCORE_API void PrepareTerrainBattle(World&,PrototypeState&);
DOMAINCORE_API void StepTerrainMovement(World&,PrototypeState&,double seconds);
}
