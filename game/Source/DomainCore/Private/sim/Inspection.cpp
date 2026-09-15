#include "domain/Inspection.h"
namespace domain {
const Building* ResolveBuilding(const World& world,EntitySelection selection) {
    if(selection.kind!=EntityKind::Building || selection.id==0) return nullptr;
    const auto found=world.buildings.find(selection.id);
    if(found==world.buildings.end() || found->second.id!=selection.id) return nullptr;
    return &found->second;
}
const BuildingDefinition* ResolveBuildingDefinition(const BuildingCatalog& catalog,const Building& building) {
    if(building.definition_id.empty() || building.definition_version==0) return nullptr;
    const auto found=catalog.find(building.definition_id);
    if(found==catalog.end() || found->second.id!=building.definition_id || found->second.version<building.definition_version) return nullptr;
    return &found->second;
}
}
