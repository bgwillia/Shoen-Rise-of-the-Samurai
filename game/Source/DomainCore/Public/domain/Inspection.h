#pragma once
#include "domain/World.h"
namespace domain {
enum class EntityKind : std::uint8_t { None, Building };
struct EntitySelection {
    EntityKind kind = EntityKind::None;
    EntityId id = 0;
    bool operator==(const EntitySelection&) const = default;
};
// Borrowed read-only records. Reacquire after any world/catalog mutation or replacement;
// store EntitySelection rather than retaining these pointers in presentation state.
DOMAINCORE_API const Building* ResolveBuilding(const World&, EntitySelection);
// Resolve only the exact type ID. The current definition must be at least the placed
// version; newer tuning remains distinct from the instance's frozen placement data.
DOMAINCORE_API const BuildingDefinition* ResolveBuildingDefinition(const BuildingCatalog&, const Building&);
}
