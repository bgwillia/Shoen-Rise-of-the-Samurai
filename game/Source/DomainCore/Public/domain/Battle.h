#pragma once
#include "domain/World.h"
namespace domain {
struct Slot { double x = 0, y = 0; };
DOMAINCORE_API std::vector<Slot> FormationSlots(const World&, EntityId formation_id);
DOMAINCORE_API Result IssueMove(World&, const std::vector<EntityId>& formation_ids, double x, double y, double facing);
DOMAINCORE_API Result AssignGroup(World&, const std::vector<EntityId>& formation_ids, std::uint8_t group);
DOMAINCORE_API Result StepFormations(World&, std::int64_t real_microseconds);
}
