#include "domain/SaveCodec.h"
#include <fstream>
#include <iostream>
#include <iterator>
int main(int argc,char** argv) {
 if(argc!=2)return 2;
 std::ifstream f(argv[1],std::ios::binary); if(!f)return 2;
 std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(f)),{});
 domain::World w; auto result=domain::LoadSnapshot(w,bytes);
 if(!result.ok){std::cerr<<result.error<<'\n';return 1;}
 std::cout<<"Decoded with the same DomainCore snapshot reader as the game.\n";
 std::cout<<"Bytes "<<bytes.size()<<", buildings "<<w.buildings.size()<<", campaign_day "<<w.campaign_day<<", speed "<<w.speed<<'\n';
 for(const auto& [id,b]:w.buildings)std::cout<<"id="<<id<<" type="<<b.definition_id<<" definition_version="<<b.definition_version<<" settlement="<<b.settlement_id<<" district="<<b.district_id<<" position_cm="<<b.x_cm<<","<<b.y_cm<<","<<b.z_cm<<" yaw_deg="<<b.yaw_degrees<<" footprint_cm="<<b.width_cm<<","<<b.depth_cm<<" state="<<static_cast<int>(b.state)<<" transaction="<<b.placement_transaction_id<<'\n';
 for(const auto& [id,s]:w.settlements)std::cout<<"settlement="<<id<<" timber="<<s.resources.timber<<" treasury="<<s.resources.treasury<<'\n';
}
