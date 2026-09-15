#include "domain/Inspection.h"
#include "domain/Buildings.h"
#include "domain/SaveCodec.h"
#include <algorithm>
#include <functional>
#include <iostream>
#include <stdexcept>
#include <type_traits>
using namespace domain;
#define CHECK(...) do {if(!(__VA_ARGS__)) throw std::runtime_error(std::string("line ")+std::to_string(__LINE__)+": "+#__VA_ARGS__);} while(false)
static_assert(std::is_same_v<decltype(ResolveBuilding(std::declval<const World&>(),EntitySelection{})),const Building*>);
static_assert(std::is_same_v<decltype(ResolveBuildingDefinition(std::declval<const BuildingCatalog&>(),std::declval<const Building&>())),const BuildingDefinition*>);
struct Scene {World world; BuildingCatalog catalog; std::array<EntityId,3> ids{};};
Scene ThreeBuildings() {
    Scene s; s.world=MakeFoundationWorld();
    s.world.build_areas.emplace(1,BuildArea{1,-5000,-5000,500,21,21,std::vector<std::int32_t>(441,0)});
    s.catalog.emplace("small_storehouse",BuildingDefinition{"small_storehouse","Small Storehouse",1,800,600,450,15,20,50,20,5});
    const std::array<PlacementCommand,3> commands={PlacementCommand{1,"small_storehouse",1,2,-2000,-1000,0},PlacementCommand{2,"small_storehouse",1,2,0,0,45},PlacementCommand{3,"small_storehouse",1,2,2000,1500,90}};
    for(std::size_t i=0;i<commands.size();++i) {auto result=PlaceBuilding(s.world,s.catalog,commands[i]); CHECK(result.ok); s.ids[i]=result.building_id;}
    CHECK(s.ids[0]!=s.ids[1] && s.ids[0]!=s.ids[2] && s.ids[1]!=s.ids[2]);
    return s;
}
void ExactIdentityAndThreeTransforms() {
    auto s=ThreeBuildings();
    for(std::size_t i=0;i<s.ids.size();++i) {
        EntitySelection selection{EntityKind::Building,s.ids[i]};
        const auto* b=ResolveBuilding(s.world,selection); CHECK(b && b==&s.world.buildings.at(s.ids[i]) && b->id==s.ids[i]);
        CHECK(b->yaw_degrees==static_cast<int>(i)*45);
        for(std::size_t j=0;j<s.ids.size();++j) if(i!=j) CHECK(b!=&s.world.buildings.at(s.ids[j]) && b->x_cm!=s.world.buildings.at(s.ids[j]).x_cm);
        const auto* definition=ResolveBuildingDefinition(s.catalog,*b); CHECK(definition==&s.catalog.at("small_storehouse"));
    }
    CHECK((EntitySelection{EntityKind::Building,s.ids[0]})==(EntitySelection{EntityKind::Building,s.ids[0]}));
    CHECK((EntitySelection{EntityKind::Building,s.ids[0]})!=(EntitySelection{EntityKind::Building,s.ids[1]}));
}
void InvalidMissingAndRemovedIdentity() {
    auto s=ThreeBuildings(); CHECK(ResolveBuilding(s.world,{EntityKind::Building,s.ids[1]}));
    auto before=s.world;
    CHECK(!ResolveBuilding(s.world,{})); CHECK(!ResolveBuilding(s.world,{EntityKind::None,s.ids[0]}));
    CHECK(!ResolveBuilding(s.world,{static_cast<EntityKind>(255),s.ids[0]}));
    CHECK(!ResolveBuilding(s.world,{EntityKind::Building,0})); CHECK(!ResolveBuilding(s.world,{EntityKind::Building,s.world.next_id}));
    CHECK(!ResolveBuilding(s.world,{EntityKind::Building,3})); // Existing cohort ID is not a building.
    CHECK(s.world==before);
    s.world.buildings.erase(s.ids[0]); before=s.world;
    CHECK(!ResolveBuilding(s.world,{EntityKind::Building,s.ids[0]}));
    CHECK(ResolveBuilding(s.world,{EntityKind::Building,s.ids[1]})->id==s.ids[1]); CHECK(s.world==before);
}
void RegistryMismatchDoesNotSelectAnother() {
    auto s=ThreeBuildings(); CHECK(ResolveBuilding(s.world,{EntityKind::Building,s.ids[0]}));
    s.world.buildings.at(s.ids[0]).id=s.ids[1]; auto before=s.world;
    CHECK(!ResolveBuilding(s.world,{EntityKind::Building,s.ids[0]}));
    const auto* b=ResolveBuilding(s.world,{EntityKind::Building,s.ids[1]}); CHECK(b && b==&s.world.buildings.at(s.ids[1]));
    s.world.buildings.emplace(0,Building{}); CHECK(!ResolveBuilding(s.world,{EntityKind::Building,0}));
    s.world.buildings.erase(0); CHECK(s.world==before);
}
void SnapshotRestoresExactSelectedRecords() {
    auto s=ThreeBuildings(); const auto expected=s.world; const auto original_records=s.world.buildings;
    const auto bytes=EncodeSnapshot(s.world); CHECK(!bytes.empty() && bytes[8]==2);
    CHECK(PlaceBuilding(s.world,s.catalog,{4,"small_storehouse",1,2,-2500,2500,135}).ok);
    CHECK(LoadSnapshot(s.world,bytes).ok && s.world==expected);
    for(auto id:s.ids) {
        const auto* restored=ResolveBuilding(s.world,{EntityKind::Building,id}); CHECK(restored && *restored==original_records.at(id));
        CHECK(restored->definition_id=="small_storehouse" && restored->definition_version==1);
    }
}
void RepeatedInspectionAndViewOrderingAreReadOnly() {
    auto s=ThreeBuildings(); auto before=s.world; auto definitions_before=s.catalog; auto saved=EncodeSnapshot(s.world);
    std::vector<EntityId> visual_order(s.ids.begin(),s.ids.end()); std::reverse(visual_order.begin(),visual_order.end());
    for(int repeat=0;repeat<1000;++repeat) for(auto id:visual_order) {
        const auto* b=ResolveBuilding(s.world,{EntityKind::Building,id}); CHECK(b && b->id==id);
        const auto* d=ResolveBuildingDefinition(s.catalog,*b); CHECK(d && d->id==b->definition_id);
    }
    visual_order.clear(); visual_order.assign(s.ids.begin(),s.ids.end());
    CHECK(ResolveBuilding(s.world,{EntityKind::Building,s.ids[0]})->id==s.ids[0]);
    CHECK(s.world==before && s.catalog==definitions_before && EncodeSnapshot(s.world)==saved);
}
void CurrentTuningAndFrozenInstanceAreSeparate() {
    auto s=ThreeBuildings(); const auto instance=s.world.buildings.at(s.ids[0]); auto world_before=s.world;
    auto& configured=s.catalog.at("small_storehouse"); configured.version=2; configured.width_cm=1600; configured.depth_cm=900; configured.timber_cost=35; configured.treasury_cost=9;
    const auto* b=ResolveBuilding(s.world,{EntityKind::Building,s.ids[0]}); CHECK(b && *b==instance);
    const auto* d=ResolveBuildingDefinition(s.catalog,*b); CHECK(d==&configured && d->version==2 && d->width_cm==1600 && d->timber_cost==35);
    CHECK(b->definition_version==1 && b->width_cm==800 && b->depth_cm==600 && s.world==world_before);
}
void MissingOlderAndMismatchedDefinitionsFailSafely() {
    auto s=ThreeBuildings(); Building b=s.world.buildings.at(s.ids[0]); CHECK(ResolveBuildingDefinition(s.catalog,b));
    auto before=s.world; s.catalog.emplace("different_type",BuildingDefinition{"different_type","Small Storehouse",9,300,300,100,15,0,0,1,1});
    s.catalog.erase("small_storehouse"); CHECK(!ResolveBuildingDefinition(s.catalog,b)); CHECK(s.world==before);
    auto wrong=s.catalog.at("different_type"); s.catalog.emplace("small_storehouse",wrong); CHECK(!ResolveBuildingDefinition(s.catalog,b));
    s.catalog.at("small_storehouse").id="small_storehouse"; s.catalog.at("small_storehouse").version=1;
    b.definition_version=2; CHECK(!ResolveBuildingDefinition(s.catalog,b));
    b.definition_version=0; CHECK(!ResolveBuildingDefinition(s.catalog,b));
    b.definition_version=1; s.catalog.at("small_storehouse").version=0; CHECK(!ResolveBuildingDefinition(s.catalog,b));
    b.definition_id.clear(); s.catalog.emplace("",BuildingDefinition{}); CHECK(!ResolveBuildingDefinition(s.catalog,b));
    CHECK(s.world==before);
}
int main() {
    std::vector<std::pair<const char*,std::function<void()>>> tests={
        {"three real placements resolve exact IDs and transforms",ExactIdentityAndThreeTransforms},
        {"none wrong kind zero missing and removed selections are safe",InvalidMissingAndRemovedIdentity},
        {"registry mismatch cannot select another building",RegistryMismatchDoesNotSelectAnother},
        {"snapshot v2 restores exact inspected records",SnapshotRestoresExactSelectedRecords},
        {"repeated inspection and reordered views leave all state unchanged",RepeatedInspectionAndViewOrderingAreReadOnly},
        {"current definition tuning differs from frozen placed dimensions",CurrentTuningAndFrozenInstanceAreSeparate},
        {"missing older and mismatched definitions have no fallback",MissingOlderAndMismatchedDefinitionsFailSafely}};
    int failed=0; for(auto& [name,test]:tests) {try{test(); std::cout<<"PASS "<<name<<'\n';}catch(const std::exception& e){++failed;std::cerr<<"FAIL "<<name<<": "<<e.what()<<'\n';}}
    std::cout<<tests.size()-failed<<" passed, "<<failed<<" failed\n"; return failed?1:0;
}
