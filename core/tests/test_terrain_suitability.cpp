#include "domain/Buildings.h"
#include "domain/SaveCodec.h"
#include "domain/TerrainSuitability.h"
#include <functional>
#include <iostream>
#include <stdexcept>

using namespace domain;
#define CHECK(...) do { if(!(__VA_ARGS__)) throw std::runtime_error(std::string("line ")+std::to_string(__LINE__)+": "+#__VA_ARGS__); } while(false)

// Represents the engine-owned surface while exercising real domain transactions.
struct TestSurface final : BuildingTerrain {
    PlacementCode code=PlacementCode::Valid;
    PlacementResult Evaluate(const PlacementCommand& command,const BuildingDefinition& definition) const override {
        if(command.definition_id!=definition.id || definition.width_cm!=800 || definition.depth_cm!=600)
            return {false,PlacementCode::InvalidCommand,0,0};
        return {code==PlacementCode::Valid,code,0,375};
    }
};
BuildingCatalog Catalog() {return {{"storehouse",{"storehouse","Storehouse",1,800,600,450,15,20,50,20,5}}};}
PlacementCommand Command(EntityId transaction=1,int x=0) {return {transaction,"storehouse",1,2,x,0,15};}
World Fixture(const std::shared_ptr<TestSurface>& surface) {
    auto w=MakeFoundationWorld();
    w.settlements.at(1).resources.timber=200; w.settlements.at(1).resources.treasury=100;
    BuildArea area; area.settlement_id=1; area.origin_x_cm=-5000; area.origin_y_cm=-5000;
    area.cell_size_cm=10000; area.columns=2; area.rows=2; area.heights_cm={0,0,0,0}; area.live_terrain=surface;
    w.build_areas.emplace(1,std::move(area)); return w;
}
void RejectedLiveTerrainPreservesWorld() {
    auto surface=std::make_shared<TestSurface>(); auto w=Fixture(surface); const auto before=w;
    for(auto code:{PlacementCode::TerrainTooSteep,PlacementCode::TerrainTooUneven,PlacementCode::InWater,PlacementCode::OutsideBuildArea}) {
        surface->code=code;
        auto preview=EvaluatePlacement(w,Catalog(),Command());
        CHECK(!preview.ok && preview.code==code && preview.ground_z_cm==375 && w==before);
        auto result=PlaceBuilding(w,Catalog(),Command());
        CHECK(!result.ok && result.code==code && w==before);
    }
}
void LivePlacementStoresHeightAndReplaysOnce() {
    auto surface=std::make_shared<TestSurface>(); auto w=Fixture(surface);
    auto placed=PlaceBuilding(w,Catalog(),Command());
    CHECK(placed.ok && placed.ground_z_cm==375 && w.buildings.at(placed.building_id).z_cm==375);
    CHECK(w.settlements.at(1).resources.timber==180 && w.settlements.at(1).resources.treasury==95);
    CHECK(ValidateWorld(w).ok);
    const auto committed=w;
    // A repeat transaction retains the original result even if the external surface changes.
    surface->code=PlacementCode::InWater;
    auto repeated=PlaceBuilding(w,Catalog(),Command());
    CHECK(repeated.ok && repeated.code==PlacementCode::AlreadyApplied && repeated.building_id==placed.building_id && repeated.ground_z_cm==375);
    CHECK(w==committed);
}
void LiveSurfaceRetainsOverlapAndBoundaryChecks() {
    auto surface=std::make_shared<TestSurface>(); auto w=Fixture(surface);
    CHECK(PlaceBuilding(w,Catalog(),Command()).ok); const auto before=w;
    auto overlap=PlaceBuilding(w,Catalog(),Command(2));
    CHECK(!overlap.ok && overlap.code==PlacementCode::OverlapsBuilding && w==before);
    auto outside=PlaceBuilding(w,Catalog(),Command(2,4999));
    CHECK(!outside.ok && outside.code==PlacementCode::OutsideBuildArea && w==before);
}
void LiveSurfaceCannotBeSilentlySavedAsSyntheticTerrain() {
    auto surface=std::make_shared<TestSurface>(); auto w=Fixture(surface);
    CHECK(ValidateWorld(w).ok);
    CHECK(EncodeSnapshot(w).empty());
}
void RepresentativeSuitabilityRules() {
    using namespace domain::suitability;
    const Rules rules;
    CHECK(suitability::Building(2,30,Water::Dry,true,rules)==BuildingResult::Valid);
    CHECK(suitability::Building(14,30,Water::Dry,true,rules)==BuildingResult::TooSteep);
    CHECK(suitability::Building(2,80,Water::Dry,true,rules)==BuildingResult::TooUneven);
    CHECK(Rice(2,true,Water::WetFlat,true,rules)==Quality::Ideal);
    CHECK(DryFarm(6,Water::Dry,true,rules)==Quality::Usable);
    CHECK(Traverse(40,Water::Dry,true,rules.infantry,rules).speed>0);
    CHECK(Traverse(40,Water::Dry,true,rules.cavalry,rules).speed==0);
    CHECK(Traverse(0,Water::MainRiver,true,rules.infantry,rules).speed==0);
    CHECK(suitability::Building(0,0,Water::Tributary,true,rules)==BuildingResult::InWater);
}
int main() {
    const std::pair<const char*,std::function<void()>> tests[]={
        {"live terrain rejection preserves resources and world",RejectedLiveTerrainPreservesWorld},
        {"live height and idempotent placement",LivePlacementStoresHeightAndReplaysOnce},
        {"live terrain retains overlap and boundary validation",LiveSurfaceRetainsOverlapAndBoundaryChecks},
        {"session terrain cannot silently lose its source on save",LiveSurfaceCannotBeSilentlySavedAsSyntheticTerrain},
        {"representative terrain suitability classifications",RepresentativeSuitabilityRules}};
    int failed=0;
    for(const auto& [name,test]:tests) {try {test(); std::cout<<"PASS "<<name<<'\n';} catch(const std::exception& e) {++failed; std::cerr<<"FAIL "<<name<<": "<<e.what()<<'\n';}}
    return failed?1:0;
}
