#pragma once
#include "domain/World.h"
namespace domain {
DOMAINCORE_API Result ValidateBuildingCatalog(const BuildingCatalog&);
DOMAINCORE_API Result ValidateBuildingState(const World&);
DOMAINCORE_API PlacementResult ValidatePlacementGeometry(const World&, const BuildingDefinition&, const PlacementCommand&);
// Preview is read-only and does not reserve a transaction or entity ID; transaction_id is ignored.
DOMAINCORE_API PlacementResult EvaluatePlacement(const World&, const BuildingCatalog&, const PlacementCommand&);
DOMAINCORE_API PlacementResult PlaceBuilding(World&, const BuildingCatalog&, const PlacementCommand&);
DOMAINCORE_API const char* PlacementReason(PlacementCode);
DOMAINCORE_API std::array<Point2,4> FootprintCorners(std::int32_t x_cm, std::int32_t y_cm, std::int32_t width_cm, std::int32_t depth_cm, std::int32_t yaw_degrees);
// Every cell uses triangles (00,10,11) and (00,11,01). Heights are linear per triangle.
DOMAINCORE_API double TerrainHeightAt(const BuildArea&, double x, double y);
// The nearest nonnegative ray hit is returned. Failure preserves hit unchanged.
DOMAINCORE_API bool RaycastBuildArea(const BuildArea&, Point3 origin, Point3 direction, Point3& hit);
}
