#include "domain/Buildings.h"
#include <algorithm>
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <vector>
using namespace domain;
using Clock=std::chrono::steady_clock;
constexpr int Warmups=10, Samples=100;
BuildingCatalog Catalog() {return {{"small_storehouse",{"small_storehouse","Small Storehouse",1,800,600,450,15,20,100,20,5}}};}
World Baseline(int n,const BuildingCatalog& catalog) {
    auto w=MakeFoundationWorld(); w.speed=0;
    w.build_areas.emplace(1,BuildArea{1,-6000,-4000,1000,13,9,std::vector<std::int32_t>(117,0)});
    w.settlements.at(1).resources.timber=(n+32)*20; w.settlements.at(1).resources.treasury=(n+32)*5;
    for(int i=0;i<n;++i) {
        int row=9-i/10,column=9-i%10;
        auto r=PlaceBuilding(w,catalog,{w.next_transaction_id,"small_storehouse",1,2,-5400+850*column,-3550+650*row,0});
        if(!r.ok) throw std::runtime_error("fixture placement rejected at index "+std::to_string(i)+": "+PlacementReason(r.code));
    }
    if(!ValidateWorld(w).ok || w.buildings.size()!=static_cast<std::size_t>(n) || w.settlements.at(1).resources.timber!=640 || w.settlements.at(1).resources.treasury!=160) throw std::runtime_error("bad baseline");
    return w;
}
template<class Function> double Timed(Function function) {
    const auto begin=Clock::now(); function(); return std::chrono::duration<double,std::micro>(Clock::now()-begin).count();
}
void Summary(int n,const char* name,std::vector<double> values) {
    std::sort(values.begin(),values.end());
    double median=(values[values.size()/2-1]+values[values.size()/2])/2.0;
    std::cout<<n<<','<<name<<','<<values.size()<<','<<median<<','<<values.back()<<'\n';
}
int main() {
    static_assert(Clock::is_steady);
    std::ofstream raw("/tmp/shoen-placement-latency-raw.csv"); raw<<"buildings,stage,sample,microseconds\n"; raw<<std::fixed<<std::setprecision(3);
    std::cout<<"Clock=std::chrono::steady_clock; warmups="<<Warmups<<"; samples="<<Samples<<"; flat vertices=117; cells=96; generation/reset copies excluded\n";
    std::cout<<"buildings,stage,samples,median_us,max_us\n"<<std::fixed<<std::setprecision(3);
    const auto catalog=Catalog();
    for(int n:{1,10,100}) {
        const auto baseline=Baseline(n,catalog);
        const PlacementCommand success{baseline.next_transaction_id,"small_storehouse",1,2,0,3350,15};
        const PlacementCommand overlap{baseline.next_transaction_id,"small_storehouse",1,2,2250,2300,0};
        const char* stages[]={"ValidateWorld","EvaluatePlacement_valid","PlaceBuilding_valid","EvaluatePlacement_overlap","PlaceBuilding_overlap"};
        std::vector<double> durations[5];
        for(int sample=-Warmups;sample<Samples;++sample) {
            auto candidate=baseline; auto reject_candidate=baseline; // Setup intentionally outside the timed calls.
            double value[5];
            value[0]=Timed([&] {if(!ValidateWorld(baseline).ok) throw std::runtime_error("validation failed");});
            value[1]=Timed([&] {auto r=EvaluatePlacement(baseline,catalog,success); if(!r.ok) throw std::runtime_error("preview failed");});
            value[2]=Timed([&] {auto r=PlaceBuilding(candidate,catalog,success); if(!r.ok || r.code!=PlacementCode::Valid) throw std::runtime_error("placement failed");});
            value[3]=Timed([&] {auto r=EvaluatePlacement(baseline,catalog,overlap); if(r.ok || r.code!=PlacementCode::OverlapsBuilding) throw std::runtime_error("overlap preview failed");});
            value[4]=Timed([&] {auto r=PlaceBuilding(reject_candidate,catalog,overlap); if(r.ok || r.code!=PlacementCode::OverlapsBuilding) throw std::runtime_error("overlap placement failed");});
            if(reject_candidate!=baseline || candidate.buildings.size()!=baseline.buildings.size()+1 || candidate.settlements.at(1).resources.timber!=620 || candidate.settlements.at(1).resources.treasury!=155) throw std::runtime_error("postcondition failed");
            if(sample>=0) for(int stage=0;stage<5;++stage) {durations[stage].push_back(value[stage]); raw<<n<<','<<stages[stage]<<','<<sample<<','<<value[stage]<<'\n';}
        }
        for(int stage=0;stage<5;++stage) Summary(n,stages[stage],durations[stage]);
    }
    return raw?0:2;
}
