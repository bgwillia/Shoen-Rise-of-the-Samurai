#include "domain/ProfilingFixture.h"
#include "domain/Buildings.h"
#include "domain/Inspection.h"
#include "domain/SaveCodec.h"
#include <functional>
#include <iostream>
#include <stdexcept>
using namespace domain;
#define CHECK(...) do {if(!(__VA_ARGS__)) throw std::runtime_error(std::string("line ")+std::to_string(__LINE__)+": "+#__VA_ARGS__);} while(false)
BuildingCatalog Catalog() {return {{"small_storehouse",{"small_storehouse","Small Storehouse",1,800,600,450,15,20,100,20,5}}};}
void CountsIdentityAndCommonTerrain() {
    auto cat=Catalog(); BuildArea common; Building anchor;
    for(std::size_t count:{1,10,100}) {
        World w; CHECK(MakeProfilingFixture(cat,count,w).ok && ValidateWorld(w).ok);
        CHECK(w.buildings.size()==count && w.services.empty() && w.formations.empty() && Summarize(w).available==200);
        CHECK(w.speed==0 && w.campaign_day==0 && w.subday_microseconds==0);
        CHECK(w.settlements.at(1).resources.timber==640 && w.settlements.at(1).resources.treasury==160);
        const auto& area=w.build_areas.at(1); CHECK(area.origin_x_cm==-6000 && area.origin_y_cm==-4000 && area.cell_size_cm==1000 && area.columns==13 && area.rows==9);
        for(auto height:area.heights_cm) CHECK(height==0);
        const auto& first=w.buildings.begin()->second; CHECK(first.x_cm==2250 && first.y_cm==2300 && first.yaw_degrees==0);
        if(count==1) {common=area;anchor=first;} else CHECK(area==common && first==anchor);
        std::size_t index=0;
        for(const auto& [id,b]:w.buildings) {
            CHECK(b.x_cm==-5400+850*(9-static_cast<int>(index%10)) && b.y_cm==-3550+650*(9-static_cast<int>(index/10)));
            CHECK(b.placement_transaction_id==index+1 && w.applied_transaction_ids.contains(b.placement_transaction_id));
            CHECK(b.definition_id=="small_storehouse" && b.width_cm==800 && b.depth_cm==600);
            CHECK(ResolveBuilding(w,{EntityKind::Building,id})==&b); ++index;
        }
        CHECK(w.revision==count && w.next_transaction_id==count+1 && w.next_id==5+count);
        if(count>1) {auto b=std::next(w.buildings.begin())->second;CHECK(b.x_cm==1400 && b.y_cm==2300);}
    }
}
void DeterministicRealPlacementAccounting() {
    auto cat=Catalog(); World a=MakeScaleWorld(1000),b;
    CHECK(MakeProfilingFixture(cat,10,a).ok && MakeProfilingFixture(cat,10,b).ok && a==b && EncodeSnapshot(a)==EncodeSnapshot(b));
    auto expected=MakeFoundationWorld(); expected.speed=0; expected.build_areas=a.build_areas;
    expected.settlements.at(1).resources.timber=840; expected.settlements.at(1).resources.treasury=210;
    for(int i=0;i<10;++i) CHECK(PlaceBuilding(expected,cat,{expected.next_transaction_id,"small_storehouse",1,2,2250-850*i,2300,0}).ok);
    CHECK(expected==a);
    cat.at("small_storehouse").timber_cost=37; cat.at("small_storehouse").treasury_cost=11;
    CHECK(MakeProfilingFixture(cat,10,a).ok && a.settlements.at(1).resources.timber==640 && a.settlements.at(1).resources.treasury==160);
}
void FailureNeverReplacesOutput() {
    auto cat=Catalog(); auto output=MakeScaleWorld(1000); auto before=output;
    for(std::size_t count:{0,2,99,101}) CHECK(!MakeProfilingFixture(cat,count,output).ok && output==before);
    CHECK(!MakeProfilingFixture({},10,output).ok && output==before);
    auto bad=cat; bad.at("small_storehouse").width_cm=0; CHECK(!MakeProfilingFixture(bad,10,output).ok && output==before);
    bad=cat; bad.at("small_storehouse").timber_cost=1'000'000'000; CHECK(!MakeProfilingFixture(bad,100,output).ok && output==before);
    bad=cat; bad.at("small_storehouse").width_cm=2000; CHECK(!MakeProfilingFixture(bad,10,output).ok && output==before);
    auto other=cat.at("small_storehouse"); other.id="other_type"; bad={{other.id,other}}; CHECK(!MakeProfilingFixture(bad,10,output).ok && output==before);
}
void ReservedSpaceAndRepresentativeRejections() {
    auto cat=Catalog();
    for(std::size_t count:{1,10,100}) {
        World w; CHECK(MakeProfilingFixture(cat,count,w).ok); const auto baseline=w;
        auto command=PlacementCommand{w.next_transaction_id,"small_storehouse",1,2,0,3350,0};
        for(int yaw=0;yaw<360;yaw+=15) {command.yaw_degrees=yaw; CHECK(EvaluatePlacement(w,cat,command).ok && w==baseline);}
        command.yaw_degrees=15; CHECK(PlaceBuilding(w,cat,command).ok && w.buildings.size()==count+1);
        CHECK(w.settlements.at(1).resources.timber==620 && w.settlements.at(1).resources.treasury==155);
        w=baseline; command={w.next_transaction_id,"small_storehouse",1,2,2250,2300,0};
        auto rejected=PlaceBuilding(w,cat,command); CHECK(!rejected.ok && rejected.code==PlacementCode::OverlapsBuilding && w==baseline);
        command.x_cm=0; command.y_cm=3950; rejected=PlaceBuilding(w,cat,command); CHECK(!rejected.ok && rejected.code==PlacementCode::OutsideBuildArea && w==baseline);
    }
}
int main() {
    std::vector<std::pair<const char*,std::function<void()>>> tests={
        {"same terrain funds anchor and exact1/10/100 counts",CountsIdentityAndCommonTerrain},
        {"deterministic fixture matches genuine placement accounting",DeterministicRealPlacementAccounting},
        {"fixture failures preserve complete output world",FailureNeverReplacesOutput},
        {"reserved rotation success and rejection space at every count",ReservedSpaceAndRepresentativeRejections}};
    int failed=0; for(auto& [name,test]:tests) {try{test();std::cout<<"PASS "<<name<<'\n';}catch(const std::exception& e){++failed;std::cerr<<"FAIL "<<name<<": "<<e.what()<<'\n';}}
    std::cout<<tests.size()-failed<<" passed, "<<failed<<" failed\n";return failed?1:0;
}
