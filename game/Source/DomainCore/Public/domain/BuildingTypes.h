#pragma once
#include <array>
#include <cstdint>
#include <map>
#include <string>
#include <vector>
namespace domain {
constexpr std::size_t MaxBuildings = 10'000;
constexpr std::size_t MaxBuildAreas = 64;
constexpr std::size_t MaxTerrainVertices = 65'536;
constexpr double PlacementToleranceCm = 1e-6; // Edge contact within this tolerance is allowed.
struct Point2 { double x = 0, y = 0; bool operator==(const Point2&) const = default; };
struct Point3 { double x = 0, y = 0, z = 0; bool operator==(const Point3&) const = default; };
struct BuildingDefinition {
    std::string id, display_name; std::uint32_t version = 1;
    std::int32_t width_cm = 0, depth_cm = 0, height_cm = 0, rotation_step_degrees = 15;
    std::int32_t max_height_variation_cm = 0, max_slope_permille = 0;
    std::int64_t timber_cost = 0, treasury_cost = 0;
    bool operator==(const BuildingDefinition&) const = default;
};
using BuildingCatalog = std::map<std::string, BuildingDefinition>;
struct BuildArea {
    std::uint64_t settlement_id = 0;
    std::int32_t origin_x_cm = 0, origin_y_cm = 0, cell_size_cm = 0;
    std::uint32_t columns = 0, rows = 0; // Vertex counts; row-major heights, y first.
    std::vector<std::int32_t> heights_cm;
    bool operator==(const BuildArea&) const = default;
};
enum class ConstructionState : std::uint8_t { Completed };
struct Building {
    std::uint64_t id = 0, settlement_id = 0, district_id = 0, placement_transaction_id = 0;
    std::string definition_id; std::uint32_t definition_version = 0;
    std::int32_t x_cm = 0, y_cm = 0, z_cm = 0, yaw_degrees = 0;
    std::int32_t width_cm = 0, depth_cm = 0, height_cm = 0;
    ConstructionState state = ConstructionState::Completed;
    std::int32_t max_height_variation_cm = 0, max_slope_permille = 0;
    bool operator==(const Building&) const = default;
};
struct PlacementCommand {
    std::uint64_t transaction_id = 0; std::string definition_id;
    std::uint64_t settlement_id = 0, district_id = 0;
    std::int32_t x_cm = 0, y_cm = 0, yaw_degrees = 0;
};
enum class PlacementCode : std::uint8_t {
    Valid, AlreadyApplied, UnknownDefinition, InvalidCommand, InvalidWorld, NoBuildArea,
    OverlapsBuilding, OutsideBuildArea, TerrainTooSteep, InsufficientResources,
    TransactionConflict, CapacityExceeded
};
struct PlacementResult {
    bool ok = false; PlacementCode code = PlacementCode::InvalidCommand;
    std::uint64_t building_id = 0; std::int32_t ground_z_cm = 0;
};
}
