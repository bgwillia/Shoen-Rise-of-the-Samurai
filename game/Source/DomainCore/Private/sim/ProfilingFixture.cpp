#include "domain/ProfilingFixture.h"
#include "domain/Buildings.h"
namespace domain {
Result MakeProfilingFixture(const BuildingCatalog& catalog,std::size_t count,World& out) {
    if(count!=1 && count!=10 && count!=100) return {false,"Profiling fixture count must be 1, 10 or 100.",0};
    const auto valid_catalog=ValidateBuildingCatalog(catalog);
    if(!valid_catalog.ok) return valid_catalog;
    const auto found=catalog.find("small_storehouse");
    if(found==catalog.end()) return {false,"Profiling fixture requires small_storehouse content.",0};
    const auto& definition=found->second;
    constexpr Quantity ReserveTimber=640,ReserveTreasury=160,QuantityLimit=1'000'000'000;
    const auto quantity=static_cast<Quantity>(count);
    if(definition.timber_cost>(QuantityLimit-ReserveTimber)/quantity || definition.treasury_cost>(QuantityLimit-ReserveTreasury)/quantity)
        return {false,"Profiling fixture funding exceeds resource bounds.",0};

    auto candidate=MakeFoundationWorld(); candidate.speed=0;
    candidate.build_areas.emplace(1,BuildArea{1,-6000,-4000,1000,13,9,std::vector<std::int32_t>(117,0)});
    auto& resources=candidate.settlements.at(1).resources;
    resources.timber=ReserveTimber+quantity*definition.timber_cost;
    resources.treasury=ReserveTreasury+quantity*definition.treasury_cost;
    for(std::size_t index=0;index<count;++index) {
        const auto row=9-static_cast<std::int32_t>(index/10),column=9-static_cast<std::int32_t>(index%10);
        const PlacementCommand command{candidate.next_transaction_id,"small_storehouse",1,2,-5400+850*column,-3550+650*row,0};
        const auto placed=PlaceBuilding(candidate,catalog,command);
        if(!placed.ok) return {false,std::string("Profiling fixture placement failed: ")+PlacementReason(placed.code),0};
    }
    const auto valid_world=ValidateWorld(candidate);
    if(!valid_world.ok) return valid_world;
    out=std::move(candidate);
    return {true,{},0};
}
}
