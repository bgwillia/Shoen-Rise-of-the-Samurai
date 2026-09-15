#include "domain/Buildings.h"
#include "domain/SaveCodec.h"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <functional>
#include <iostream>
#include <iterator>
#include <limits>
#include <stdexcept>
using namespace domain;
#define CHECK(...) do { if(!(__VA_ARGS__)) throw std::runtime_error(std::string("line ")+std::to_string(__LINE__)+": "+#__VA_ARGS__); } while(false)
BuildingCatalog Catalog() {return {{"small_storehouse",{"small_storehouse","Small Storehouse",1,800,600,450,15,20,50,20,5}}};}
World Fixture() {
    auto w=MakeFoundationWorld(); w.settlements.at(1).resources.timber=200; w.settlements.at(1).resources.treasury=100;
    w.build_areas.emplace(1,BuildArea{1,-5000,-5000,500,21,21,std::vector<std::int32_t>(441,0)}); return w;
}
PlacementCommand Command(EntityId tx=1,int x=0,int y=0,int yaw=0) {return {tx,"small_storehouse",1,2,x,y,yaw};}
void Reject(World& w,const BuildingCatalog& cat,PlacementCommand command,PlacementCode code) {
    auto before=w; auto result=PlaceBuilding(w,cat,command); CHECK(!result.ok && result.code==code); CHECK(w==before);
}
void SuccessAndPreview() {
    auto w=Fixture(); auto cat=Catalog(); auto before=w; auto cmd=Command(0,123,-456,15);
    auto p=EvaluatePlacement(w,cat,cmd); CHECK(p.ok && p.code==PlacementCode::Valid && p.ground_z_cm==0); CHECK(w==before);
    cmd.transaction_id=1; auto r=PlaceBuilding(w,cat,cmd); CHECK(r.ok && r.code==PlacementCode::Valid && r.building_id==before.next_id);
    CHECK(w.buildings.size()==1); const auto& b=w.buildings.at(r.building_id);
    CHECK(b.id==r.building_id && b.definition_id==cmd.definition_id && b.definition_version==1 && b.settlement_id==1 && b.district_id==2);
    CHECK(b.x_cm==123 && b.y_cm==-456 && b.z_cm==0 && b.yaw_degrees==15 && b.width_cm==800 && b.depth_cm==600 && b.height_cm==450);
    CHECK(b.state==ConstructionState::Completed && b.placement_transaction_id==1);
    CHECK(b.max_height_variation_cm==20 && b.max_slope_permille==50);
    CHECK(w.settlements.at(1).resources.timber==180 && w.settlements.at(1).resources.treasury==95);
    CHECK(w.next_id==before.next_id+1 && w.next_transaction_id==2 && w.revision==before.revision+1 && w.applied_transaction_ids.contains(1));
    CHECK(Summarize(w)==Summarize(before) && w.cohorts==before.cohorts && w.services==before.services && w.rng==before.rng);
    CHECK(ValidateWorld(w).ok && ValidateBuildingState(w).ok);
}
void ResourceAtomicity() {
    auto cat=Catalog();
    for(bool timber:{true,false}) {auto w=Fixture(); auto& r=w.settlements.at(1).resources; if(timber) r.timber=19; else r.treasury=4; Reject(w,cat,Command(),PlacementCode::InsufficientResources);}
    auto w=Fixture(); w.settlements.at(1).resources.timber=20; w.settlements.at(1).resources.treasury=5;
    CHECK(PlaceBuilding(w,cat,Command()).ok); CHECK(w.settlements.at(1).resources.timber==0 && w.settlements.at(1).resources.treasury==0);
    auto geometry=ValidatePlacementGeometry(w,cat.begin()->second,Command(2,2000)); CHECK(geometry.ok);
    Reject(w,cat,Command(2,2000),PlacementCode::InsufficientResources);
}
void RotatedOverlapAndEdges() {
    auto cat=Catalog(); auto w=Fixture(); CHECK(PlaceBuilding(w,cat,Command()).ok);
    Reject(w,cat,Command(2,0,0,45),PlacementCode::OverlapsBuilding);
    Reject(w,cat,Command(2,0,699,90),PlacementCode::OverlapsBuilding);
    CHECK(PlaceBuilding(w,cat,Command(2,0,700,90)).ok); // Exact edge touching.
    CHECK(PlaceBuilding(w,cat,Command(3,800,0,0)).ok);
    auto corners=FootprintCorners(0,0,800,600,90); CHECK(std::abs(corners[0].x-300)<1e-6 && std::abs(corners[0].y+400)<1e-6);
    auto other=Fixture(); CHECK(PlaceBuilding(other,cat,Command(1,0,0,45)).ok);
    Reject(other,cat,Command(2,300,0,135),PlacementCode::OverlapsBuilding);
    CHECK(PlaceBuilding(other,cat,Command(2,900,900,45)).ok);
}
void BoundaryAndGeometry() {
    auto w=Fixture(); auto cat=Catalog(); Reject(w,cat,Command(1,4510,0,45),PlacementCode::OutsideBuildArea);
    CHECK(PlaceBuilding(w,cat,Command(1,4500,0,45)).ok);
    w=Fixture(); CHECK(PlaceBuilding(w,cat,Command(1,4600,0,0)).ok);
    Reject(w,cat,Command(2,-4601,0,0),PlacementCode::OutsideBuildArea);
    w=Fixture(); w.build_areas.clear(); Reject(w,cat,Command(2),PlacementCode::NoBuildArea);
}
void InteriorTerrainAndSlope() {
    auto cat=Catalog(); auto w=Fixture(); auto& a=w.build_areas.at(1); a.cell_size_cm=100; a.columns=101; a.rows=101; a.heights_cm.assign(10201,0); a.heights_cm[51*101+51]=60;
    CHECK(TerrainHeightAt(a,0,0)==0);
    for(auto corner:FootprintCorners(0,0,800,600,0)) CHECK(TerrainHeightAt(a,corner.x,corner.y)==0);
    auto heightCat=cat; heightCat.begin()->second.max_slope_permille=1000;
    Reject(w,heightCat,Command(),PlacementCode::TerrainTooSteep); // Interior peak, all four corners flat.
    auto slopeCat=cat; slopeCat.begin()->second.max_height_variation_cm=1000;
    Reject(w,slopeCat,Command(),PlacementCode::TerrainTooSteep);
    w=Fixture(); for(std::uint32_t y=0;y<21;++y) for(std::uint32_t x=0;x<21;++x) w.build_areas.at(1).heights_cm[y*21+x]=static_cast<int>(x)*5;
    auto result=PlaceBuilding(w,cat,Command()); CHECK(result.ok && result.ground_z_cm==50 && w.buildings.at(result.building_id).z_cm==50);
}
void TriangulatedTerrainAndRaycast() {
    BuildArea a{1,0,0,100,2,2,{0,0,0,100}};
    CHECK(std::abs(TerrainHeightAt(a,75,25)-25)<1e-8); CHECK(std::abs(TerrainHeightAt(a,25,75)-25)<1e-8);
    CHECK(TerrainHeightAt(a,50,50)==50 && TerrainHeightAt(a,100,100)==100); CHECK(std::isnan(TerrainHeightAt(a,-0.1,50)));
    Point3 hit{9,8,7}; CHECK(RaycastBuildArea(a,{75,25,1000},{0,0,-2},hit)); CHECK(std::abs(hit.x-75)<1e-8 && std::abs(hit.y-25)<1e-8 && std::abs(hit.z-25)<1e-8);
    CHECK(RaycastBuildArea(a,{-50,25,100},{1,0,-1},hit)); CHECK(std::abs(hit.x-25)<1e-8 && std::abs(hit.z-25)<1e-8);
    auto previous=hit; CHECK(!RaycastBuildArea(a,{75,25,1000},{0,0,1},hit) && hit==previous);
    CHECK(!RaycastBuildArea(a,{75,25,1000},{0,0,0},hit) && hit==previous);
    CHECK(!RaycastBuildArea(a,{std::numeric_limits<double>::quiet_NaN(),0,0},{0,0,-1},hit) && hit==previous);
    a.heights_cm.pop_back(); CHECK(std::isnan(TerrainHeightAt(a,0,0))); CHECK(!RaycastBuildArea(a,{0,0,100},{0,0,-1},hit) && hit==previous);
}
void InvalidPreviewKeepsTerrainElevation() {
    auto w=Fixture(); auto cat=Catalog();
    for(std::uint32_t y=0;y<21;++y) for(std::uint32_t x=0;x<21;++x) w.build_areas.at(1).heights_cm[y*21+x]=static_cast<int>(x)*40;
    auto preview=EvaluatePlacement(w,cat,Command(0)); CHECK(!preview.ok && preview.code==PlacementCode::TerrainTooSteep && preview.ground_z_cm==400);
    w.build_areas.at(1).heights_cm.assign(441,400); CHECK(PlaceBuilding(w,cat,Command()).ok);
    preview=EvaluatePlacement(w,cat,Command(0)); CHECK(!preview.ok && preview.code==PlacementCode::OverlapsBuilding && preview.ground_z_cm==400);
    preview=EvaluatePlacement(w,cat,Command(0,4800)); CHECK(!preview.ok && preview.code==PlacementCode::OutsideBuildArea && preview.ground_z_cm==400);
    w.settlements.at(1).resources.timber=0;
    preview=EvaluatePlacement(w,cat,Command(0,2000)); CHECK(!preview.ok && preview.code==PlacementCode::InsufficientResources && preview.ground_z_cm==400);
}
void DefinitionsAndBadCommands() {
    auto cat=Catalog(); CHECK(ValidateBuildingCatalog(cat).ok); CHECK(!ValidateBuildingCatalog({}).ok);
    auto bad=cat; bad.begin()->second.width_cm=0; CHECK(!ValidateBuildingCatalog(bad).ok);
    bad=cat; bad.begin()->second.timber_cost=-1; CHECK(!ValidateBuildingCatalog(bad).ok);
    bad=cat; bad.begin()->second.version=0; CHECK(!ValidateBuildingCatalog(bad).ok);
    bad=cat; bad.begin()->second.id="wrong"; CHECK(!ValidateBuildingCatalog(bad).ok);
    bad=cat; bad.begin()->second.rotation_step_degrees=0; CHECK(!ValidateBuildingCatalog(bad).ok);
    bad=cat; bad.begin()->second.max_slope_permille=-1; CHECK(!ValidateBuildingCatalog(bad).ok);
    auto w=Fixture(); auto before=w; CHECK(!PlaceBuilding(w,bad,Command()).ok && w==before);
    auto c=Command(); c.definition_id="missing"; Reject(w,cat,c,PlacementCode::UnknownDefinition);
    c=Command(); c.yaw_degrees=-1; Reject(w,cat,c,PlacementCode::InvalidCommand);
    c=Command(); c.yaw_degrees=360; Reject(w,cat,c,PlacementCode::InvalidCommand);
    c=Command(); c.x_cm=std::numeric_limits<std::int32_t>::max(); Reject(w,cat,c,PlacementCode::InvalidCommand);
    c=Command(); c.settlement_id=999; Reject(w,cat,c,PlacementCode::InvalidCommand);
    c=Command(); c.district_id=999; Reject(w,cat,c,PlacementCode::InvalidCommand);
    c=Command(0); Reject(w,cat,c,PlacementCode::InvalidCommand);
    w.districts.emplace(6,District{6,1,"Other district"}); w.next_id=7; c=Command(); c.district_id=0; CHECK(PlaceBuilding(w,cat,c).ok);
}
void DuplicateTransactions() {
    auto w=Fixture(); auto cat=Catalog(); auto cmd=Command(); auto placed=PlaceBuilding(w,cat,cmd); CHECK(placed.ok); auto before=w;
    auto same=PlaceBuilding(w,cat,cmd); CHECK(same.ok && same.code==PlacementCode::AlreadyApplied && same.building_id==placed.building_id && w==before);
    auto changed=cmd; changed.x_cm=1000; Reject(w,cat,changed,PlacementCode::TransactionConflict);
    changed=cmd; changed.definition_id="another"; Reject(w,cat,changed,PlacementCode::TransactionConflict);
    auto changedCatalog=cat; changedCatalog.begin()->second.width_cm=1000; changedCatalog.begin()->second.version=2;
    same=PlaceBuilding(w,changedCatalog,cmd); CHECK(same.ok && same.building_id==placed.building_id && w==before); // Replay original identity despite changed tuning.
    auto loaded=DecodeSnapshot(EncodeSnapshot(w)); CHECK(loaded.ok); before=loaded.world;
    same=PlaceBuilding(loaded.world,{},cmd); CHECK(same.ok && same.code==PlacementCode::AlreadyApplied && loaded.world==before);
    auto f=Mobilize(w,3,1); CHECK(f.ok); Outcome o{2,f.id,w.revision,{{w.formations.at(f.id).service_ids[0],ServiceStatus::Active}}}; CHECK(ApplyOutcome(w,o).ok);
    Reject(w,cat,Command(2,2000),PlacementCode::TransactionConflict);
}
void StableIdsAndDeterminism() {
    auto a=Fixture(),b=a; auto cat=Catalog();
    for(auto c:{Command(1,-2000,-2000,15),Command(2,0,0,30),Command(3,2000,2000,90)}) {CHECK(PlaceBuilding(a,cat,c).ok && PlaceBuilding(b,cat,c).ok); CHECK(a==b);}
    auto old=a.buildings; auto f=Mobilize(a,3,10); CHECK(f.ok); CHECK(!old.contains(f.id)); for(auto id:a.formations.at(f.id).service_ids) CHECK(!old.contains(id));
    auto before=a; auto viewCopy=a.buildings; viewCopy.clear(); CHECK(a==before);
    auto c=Command(4,3000,-3000,45); auto added=PlaceBuilding(a,cat,c); CHECK(added.ok && added.building_id>f.id);
}
void SnapshotV2AndFrozenDimensions() {
    CHECK(SnapshotVersion==2); auto w=Fixture(); auto cat=Catalog(); auto p=PlaceBuilding(w,cat,Command(7,123,-456,105)); CHECK(p.ok);
    auto expected=w; auto bytes=EncodeSnapshot(w); CHECK(!bytes.empty() && bytes[8]==2); CHECK(PlaceBuilding(w,cat,Command(8,3000,3000)).ok);
    CHECK(LoadSnapshot(w,bytes).ok && w==expected); CHECK(EncodeSnapshot(w)==bytes);
    cat.begin()->second.width_cm=1600; cat.begin()->second.version=2;
    CHECK(w.buildings.at(p.building_id).width_cm==800 && w.buildings.at(p.building_id).definition_version==1);
    CHECK(ValidateWorld(w).ok);
}
void AcceptedV1Migration() {
    std::ifstream in(std::string(FIXTURE_DIR)+"/milestone1-v1.shoen",std::ios::binary); CHECK(in.good());
    std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(in)),{}); CHECK(bytes.size()>28 && bytes[8]==1);
    auto d=DecodeSnapshot(bytes); CHECK(d.ok); auto expected=MakeFoundationWorld(); auto f=Mobilize(expected,3,100); CHECK(f.ok);
    Outcome o{1,f.id,expected.revision,{}}; std::size_t i=0; for(auto id:expected.formations.at(f.id).service_ids) {o.dispositions.push_back({id,i<20?ServiceStatus::Dead:i<35?ServiceStatus::WoundedAway:ServiceStatus::Active}); ++i;}
    CHECK(ApplyOutcome(expected,o).ok && Demobilize(expected,f.id).ok); SetSpeed(expected,5); AdvanceRealTime(expected,700001); NextRandom(expected,RngStream::Combat); expected.formation_substep_microseconds=12345;
    CHECK(d.world==expected && d.world.buildings.empty() && d.world.build_areas.empty());
    auto migrated=EncodeSnapshot(d.world); CHECK(migrated[8]==2); auto again=DecodeSnapshot(migrated); CHECK(again.ok && again.world==expected);
}
void SetU32(std::vector<std::uint8_t>&,std::size_t,std::uint32_t);
void RepairHeader(std::vector<std::uint8_t>&);
void SavedTerrainMustRemainPlaceable() {
    auto cat=Catalog(); cat.begin()->second.max_height_variation_cm=1000; cat.begin()->second.max_slope_permille=100;
    auto w=Fixture();
    for(std::uint32_t y=0;y<21;++y) for(std::uint32_t x=16;x<21;++x) w.build_areas.at(1).heights_cm[y*21+x]=static_cast<int>(x-16)*100;
    auto placed=PlaceBuilding(w,cat,Command()); CHECK(placed.ok);
    auto tampered=w; tampered.buildings.at(placed.building_id).x_cm=4000; tampered.buildings.at(placed.building_id).z_cm=200;
    CHECK(!ValidateBuildingState(tampered).ok && !ValidateWorld(tampered).ok && EncodeSnapshot(tampered).empty());
    auto malicious=EncodeSnapshot(w); CHECK(!malicious.empty());
    // Single record tail: seven I32 transform/dimension fields, state byte, two I32 terrain limits.
    SetU32(malicious,malicious.size()-37,4000); SetU32(malicious,malicious.size()-29,200); RepairHeader(malicious);
    const auto before=w; CHECK(!LoadSnapshot(w,malicious).ok && w==before);
    // The center and all four corners remain flat; the saved footprint contains an interior ridge.
    w=Fixture(); cat=Catalog(); cat.begin()->second.max_slope_permille=1000;
    auto& a=w.build_areas.at(1); a.cell_size_cm=100; a.columns=101; a.rows=101; a.heights_cm.assign(10201,0);
    placed=PlaceBuilding(w,cat,Command()); CHECK(placed.ok); auto& changedArea=w.build_areas.at(1); changedArea.heights_cm[51*101+51]=60;
    CHECK(TerrainHeightAt(changedArea,0,0)==0); for(auto p:FootprintCorners(0,0,800,600,0)) CHECK(TerrainHeightAt(changedArea,p.x,p.y)==0);
    CHECK(!ValidateBuildingState(w).ok && !ValidateWorld(w).ok && EncodeSnapshot(w).empty());
}
void FrozenTerrainToleranceSurvivesTuning() {
    auto w=Fixture(); auto cat=Catalog(); cat.begin()->second.max_height_variation_cm=100; cat.begin()->second.max_slope_permille=100;
    for(std::uint32_t y=0;y<21;++y) for(std::uint32_t x=0;x<21;++x) w.build_areas.at(1).heights_cm[y*21+x]=static_cast<int>(x)*40;
    auto placed=PlaceBuilding(w,cat,Command()); CHECK(placed.ok);
    CHECK(w.buildings.at(placed.building_id).max_height_variation_cm==100 && w.buildings.at(placed.building_id).max_slope_permille==100);
    auto bytes=EncodeSnapshot(w); CHECK(!bytes.empty()); cat.begin()->second.max_height_variation_cm=0; cat.begin()->second.max_slope_permille=0; cat.begin()->second.version=2;
    auto decoded=DecodeSnapshot(bytes); CHECK(decoded.ok && decoded.world==w && ValidateBuildingState(decoded.world).ok);
    auto repeat=PlaceBuilding(decoded.world,cat,Command()); CHECK(repeat.ok && repeat.code==PlacementCode::AlreadyApplied && decoded.world==w);
}
void MalformedBuildingState() {
    auto w=Fixture(); auto cat=Catalog(); auto p=PlaceBuilding(w,cat,Command()); CHECK(p.ok);
    auto invalid=[&](const std::function<void(World&)>& damage) {auto bad=w; damage(bad); CHECK(!ValidateWorld(bad).ok && !ValidateBuildingState(bad).ok && EncodeSnapshot(bad).empty());};
    invalid([](World& a){a.build_areas.at(1).heights_cm.pop_back();});
    invalid([](World& a){a.build_areas.at(1).columns=std::numeric_limits<std::uint32_t>::max();});
    invalid([](World& a){a.build_areas.at(1).cell_size_cm=0;});
    invalid([](World& a){a.build_areas.at(1).settlement_id=999;});
    invalid([](World& a){a.buildings.begin()->second.district_id=999;});
    invalid([](World& a){a.buildings.begin()->second.width_cm=-1;});
    invalid([](World& a){a.buildings.begin()->second.max_height_variation_cm=-1;});
    invalid([](World& a){a.buildings.begin()->second.max_slope_permille=1'000'001;});
    invalid([](World& a){a.buildings.begin()->second.state=static_cast<ConstructionState>(99);});
    invalid([](World& a){a.buildings.begin()->second.placement_transaction_id=99;});
    invalid([](World& a){a.buildings.begin()->second.id=3;});
    invalid([](World& a){a.buildings.begin()->second.x_cm=5000;});
    invalid([](World& a){a.buildings.begin()->second.z_cm=10;});
    invalid([](World& a){auto b=a.buildings.begin()->second; b.id=a.next_id++; b.placement_transaction_id=a.next_transaction_id++; a.applied_transaction_ids.insert(b.placement_transaction_id); a.buildings.emplace(b.id,b);});
}
void SetU32(std::vector<std::uint8_t>& bytes,std::size_t offset,std::uint32_t value) {for(int i=0;i<4;++i) bytes[offset+i]=static_cast<std::uint8_t>(value>>(i*8));}
void RepairHeader(std::vector<std::uint8_t>& bytes) {
    std::uint64_t size=bytes.size()-28,hash=14695981039346656037ULL;
    for(std::size_t i=28;i<bytes.size();++i) {hash^=bytes[i]; hash*=1099511628211ULL;}
    for(int i=0;i<8;++i) {bytes[12+i]=static_cast<std::uint8_t>(size>>(i*8)); bytes[20+i]=static_cast<std::uint8_t>(hash>>(i*8));}
}
void MalformedV2Payloads() {
    auto w=Fixture(); auto cat=Catalog(); CHECK(PlaceBuilding(w,cat,Command()).ok); auto bytes=EncodeSnapshot(w); CHECK(bytes[8]==2);
    auto prefix=w; prefix.buildings.clear(); prefix.build_areas.clear(); auto start=EncodeSnapshot(prefix).size()-8;
    auto buildingCount=start+4+32+w.build_areas.at(1).heights_cm.size()*4;
    auto buildingStart=buildingCount+4;
    auto reject=[&](std::vector<std::uint8_t> bad) {RepairHeader(bad); auto before=w; CHECK(!LoadSnapshot(w,bad).ok && w==before);};
    auto bad=bytes; SetU32(bad,start,MaxBuildAreas+1); reject(bad);
    bad=bytes; SetU32(bad,start+4+28,MaxTerrainVertices+1); reject(bad);
    bad=bytes; SetU32(bad,start+4+20,std::numeric_limits<std::uint32_t>::max()); reject(bad);
    bad=bytes; SetU32(bad,buildingCount,MaxBuildings+1); reject(bad);
    bad=bytes; bad[bad.size()-9]=99; reject(bad); // Construction enum before the two frozen terrain limits.
    bad=bytes; SetU32(bad,bad.size()-8,0xffffffff); reject(bad);
    bad=bytes; SetU32(bad,bad.size()-4,1'000'001); reject(bad);
    bad=bytes; bad[buildingStart]=3; reject(bad); // Collides with cohort ID and map/global registry.
    bad=bytes; SetU32(bad,buildingStart+32,257); reject(bad); // Oversized definition string.
    bad=bytes; bad.pop_back(); reject(bad);
    bad=bytes; bad.push_back(0); reject(bad);
    bad=bytes; SetU32(bad,8,1); reject(bad); // v2 appended fields cannot masquerade as v1.
    bad=bytes; SetU32(bad,8,3); reject(bad);
    bad=bytes; SetU32(bad,buildingCount,2); bad.insert(bad.end(),bytes.begin()+buildingStart,bytes.end()); reject(bad);
}
void LimitsAndCounters() {
    auto w=Fixture(); auto cat=Catalog(); w.next_id=std::numeric_limits<EntityId>::max()-1; Reject(w,cat,Command(),PlacementCode::CapacityExceeded);
    w=Fixture(); w.revision=std::numeric_limits<std::uint64_t>::max()-1; Reject(w,cat,Command(),PlacementCode::CapacityExceeded);
    w=Fixture(); Reject(w,cat,Command(std::numeric_limits<EntityId>::max()-1),PlacementCode::CapacityExceeded);
    for(EntityId i=1;i<=MaxServiceRecords;++i) w.applied_transaction_ids.insert(i); w.next_transaction_id=MaxServiceRecords+1;
    Reject(w,cat,Command(w.next_transaction_id),PlacementCode::CapacityExceeded);
    auto bad=Fixture(); bad.build_areas.at(1).heights_cm.assign(MaxTerrainVertices+1,0); CHECK(!ValidateBuildingState(bad).ok);
    bad=Fixture(); for(std::size_t i=0;i<=MaxBuildings;++i) bad.buildings.emplace(100+i,Building{});
    CHECK(!ValidateBuildingState(bad).ok); auto before=bad; CHECK(!PlaceBuilding(bad,cat,Command()).ok && bad==before);
    bad=Fixture(); for(std::size_t i=0;i<=MaxBuildAreas;++i) bad.build_areas.emplace(100+i,BuildArea{});
    CHECK(!ValidateBuildingState(bad).ok); before=bad; CHECK(!PlaceBuilding(bad,cat,Command()).ok && bad==before);
}
struct ObservedPlacement {
    const World* live=nullptr; World before; std::array<PlacementTraceStage,16> stages{};
    std::size_t count=0; bool unchanged_before_commit=true, committed_state_correct=false;
};
void RecordPlacementStage(PlacementTraceStage stage,void* context) {
    auto& observed=*static_cast<ObservedPlacement*>(context);
    if(observed.count<observed.stages.size()) observed.stages[observed.count]=stage;
    ++observed.count;
    if(stage==PlacementTraceStage::Committed) {
        observed.committed_state_correct=observed.live->buildings.size()==observed.before.buildings.size()+1
            && observed.live->settlements.at(1).resources.timber==observed.before.settlements.at(1).resources.timber-20
            && observed.live->settlements.at(1).resources.treasury==observed.before.settlements.at(1).resources.treasury-5
            && observed.live->next_id==observed.before.next_id+1
            && observed.live->applied_transaction_ids.contains(1);
    } else observed.unchanged_before_commit=observed.unchanged_before_commit && *observed.live==observed.before;
}
void PlacementObserverOrderAndCommitVisibility() {
    auto w=Fixture(); auto unobserved=w; auto cat=Catalog(); ObservedPlacement observed{&w,w};
    auto result=PlaceBuilding(w,cat,Command(),{RecordPlacementStage,&observed}); CHECK(result.ok);
    const std::array expected={PlacementTraceStage::InitialValidationBegin,PlacementTraceStage::InitialValidationEnd,
        PlacementTraceStage::PlacementValidationBegin,PlacementTraceStage::PlacementValidationEnd,
        PlacementTraceStage::CandidateCopyBegin,PlacementTraceStage::CandidateCopyEnd,
        PlacementTraceStage::CandidateValidationBegin,PlacementTraceStage::CandidateValidationEnd,PlacementTraceStage::Committed};
    CHECK(observed.count==expected.size());
    for(std::size_t i=0;i<expected.size();++i) CHECK(observed.stages[i]==expected[i]);
    CHECK(observed.unchanged_before_commit && observed.committed_state_correct);
    CHECK(PlaceBuilding(unobserved,cat,Command()).ok && unobserved==w);
    auto empty_observer=Fixture(); CHECK(PlaceBuilding(empty_observer,cat,Command(),{nullptr,&observed}).ok && empty_observer==w);
}
void PlacementObserverRejectAndRetryNeverCommit() {
    auto w=Fixture(); auto cat=Catalog(); CHECK(PlaceBuilding(w,cat,Command()).ok);
    auto verify=[&](PlacementCommand command,PlacementCode code,std::size_t expected_count) {
        ObservedPlacement observed{&w,w}; auto result=PlaceBuilding(w,cat,command,{RecordPlacementStage,&observed});
        CHECK(result.code==code && observed.count==expected_count && w==observed.before && observed.unchanged_before_commit);
        CHECK(observed.stages[0]==PlacementTraceStage::InitialValidationBegin && observed.stages[1]==PlacementTraceStage::InitialValidationEnd);
        for(std::size_t i=0;i<observed.count;++i) CHECK(observed.stages[i]!=PlacementTraceStage::Committed && observed.stages[i]!=PlacementTraceStage::CandidateCopyBegin);
        if(expected_count==4) CHECK(observed.stages[2]==PlacementTraceStage::PlacementValidationBegin && observed.stages[3]==PlacementTraceStage::PlacementValidationEnd);
    };
    verify(Command(),PlacementCode::AlreadyApplied,2);
    verify(Command(1,2000),PlacementCode::TransactionConflict,2);
    verify(Command(0),PlacementCode::InvalidCommand,2);
    verify(Command(2),PlacementCode::OverlapsBuilding,4);
    verify(Command(2,5000),PlacementCode::OutsideBuildArea,4);
    w.settlements.at(1).resources.timber=0; verify(Command(2,2000),PlacementCode::InsufficientResources,4);
    w.settlements.at(1).resources.timber=-1; verify(Command(2,2000),PlacementCode::InvalidWorld,2);
}
int main() {
    std::vector<std::pair<const char*,std::function<void()>>> tests={
        {"preview and atomic successful placement",SuccessAndPreview},{"each resource independently required and exact costs",ResourceAtomicity},
        {"rotated overlap and exact edge contact",RotatedOverlapAndEdges},{"rotated boundary and no build area",BoundaryAndGeometry},
        {"interior terrain peak and independent slope limit",InteriorTerrainAndSlope},{"shared triangulation height and nearest ray hit",TriangulatedTerrainAndRaycast},
        {"invalid preview retains authoritative ground elevation",InvalidPreviewKeepsTerrainElevation},{"invalid definitions coordinates and references",DefinitionsAndBadCommands},{"duplicate conflict replay and shared transaction namespace",DuplicateTransactions},
        {"stable global IDs view independence and determinism",StableIdsAndDeterminism},{"v2 restore all state and frozen definition dimensions",SnapshotV2AndFrozenDimensions},
        {"real accepted v1 fixture migration",AcceptedV1Migration},{"saved buildings retain terrain placement constraints",SavedTerrainMustRemainPlaceable},{"frozen terrain tolerances survive changed tuning",FrozenTerrainToleranceSurvivesTuning},{"malformed building area and registry validation",MalformedBuildingState},
        {"malformed v2 added records reject before replacement",MalformedV2Payloads},{"capacity and counter failures are immutable",LimitsAndCounters},{"optional observer stages match live atomic commit",PlacementObserverOrderAndCommitVisibility},{"observer rejection and retry never claim commit",PlacementObserverRejectAndRetryNeverCommit}};
    int failed=0; for(auto& [name,test]:tests) {try{test(); std::cout<<"PASS "<<name<<'\n';}catch(const std::exception& e){++failed;std::cerr<<"FAIL "<<name<<": "<<e.what()<<'\n';}}
    std::cout<<tests.size()-failed<<" passed, "<<failed<<" failed\n"; return failed?1:0;
}
