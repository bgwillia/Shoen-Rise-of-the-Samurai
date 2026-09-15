#include "domain/World.h"
#include "domain/SaveCodec.h"
#include "domain/Battle.h"
#include <cmath>
#include <functional>
#include <iostream>
#include <limits>
#include <stdexcept>
using namespace domain;
#define CHECK(...) do { if (!(__VA_ARGS__)) throw std::runtime_error(std::string("line ") + std::to_string(__LINE__) + ": " + #__VA_ARGS__); } while (false)

World Base() {
    World w;
    w.settlements.emplace(1, Settlement{1,"Test manor",{500,12,15,100,30,47,53}});
    w.districts.emplace(2, District{2,1,"Rice fields"});
    w.cohorts.emplace(3, Cohort{3,1,2,Occupation::Agriculture,Skill::Trained,Estate::Ordinary,200,0,0});
    w.generals.emplace(4,General{4,"Test commander",61,62,63,64,65,66});
    w.initial_population=200; w.next_id=5;
    for (std::size_t i=0;i<w.rng.size();++i) w.rng[i].state=100+i;
    return w;
}
EntityId Muster(World& w, EntityId cohort=3, Quantity count=100) {
    auto r=Mobilize(w,cohort,count); CHECK(r.ok); CHECK(r.id!=0); return r.id;
}
Outcome Losses(const World& w,EntityId formation, EntityId tx=1) {
    Outcome o{tx,formation,w.revision,{}};
    auto& ids=w.formations.at(formation).service_ids;
    for (std::size_t i=0;i<ids.size();++i) o.dispositions.push_back({ids[i],i<20?ServiceStatus::Dead:i<35?ServiceStatus::WoundedAway:ServiceStatus::Active});
    return o;
}
void Conservation() {
    auto w=MakeFoundationWorld(); CHECK(Summarize(w).available==200);
    auto f=Muster(w); auto s=Summarize(w); CHECK(s.available==100 && s.away==100 && s.total==200);
    CHECK(ApplyOutcome(w,Losses(w,f)).ok); CHECK(Demobilize(w,f).ok);
    s=Summarize(w); CHECK(s.available==165 && s.recovering==15 && s.dead==20 && s.living==180 && s.total==200); CHECK(ValidateWorld(w).ok);
}
void ExactlyOnce() {
    auto w=Base(); auto f=Muster(w); auto o=Losses(w,f); CHECK(ApplyOutcome(w,o).ok);
    auto before=w; CHECK(!ApplyOutcome(w,o).ok); CHECK(w==before);
    CHECK(Demobilize(w,f).ok); before=w; CHECK(!Demobilize(w,f).ok); CHECK(w==before);
}
void WoundedExcluded() {
    auto w=Base(); auto f=Muster(w); CHECK(ApplyOutcome(w,Losses(w,f)).ok); CHECK(Summarize(w).away==80);
    CHECK(Demobilize(w,f).ok); CHECK(!Mobilize(w,3,166).ok); CHECK(Mobilize(w,3,165).ok);
    CHECK(w.cohorts.at(3).recovering_home==15); CHECK(Summarize(w).total==200);
}
void OriginAndOccupations() {
    auto w=Base(); w.cohorts.clear(); w.initial_population=120; w.next_id=20;
    for (int i=0;i<6;++i) w.cohorts.emplace(5+i,Cohort{static_cast<EntityId>(5+i),1,2,static_cast<Occupation>(i),Skill::Master,static_cast<Estate>(i%4),20,0,0});
    for (int i=0;i<6;++i) {
        auto f=Muster(w,5+i,10); auto ids=w.formations.at(f).service_ids; auto origin=w.services.at(ids[0]).origin;
        CHECK(origin.cohort_id==static_cast<EntityId>(5+i) && origin.occupation==static_cast<Occupation>(i) && origin.skill==Skill::Master);
        CHECK(origin.estate==static_cast<Estate>(i%4)); CHECK(Demobilize(w,f).ok);
        CHECK(w.cohorts.at(5+i).available==20); CHECK(w.services.at(ids[0]).origin==origin);
        CHECK(w.services.at(ids[0]).status==ServiceStatus::ReturnedHealthy);
    }
    CHECK(ValidateWorld(w).ok); CHECK(Summarize(w).available==120);
}
void DistrictAndAlliedReturn() {
    auto w=Base(); w.settlements.emplace(5,Settlement{5,"Ally",{}}); w.districts.emplace(6,District{6,5,"Smith quarter"});
    w.cohorts.emplace(7,Cohort{7,5,6,Occupation::Smithing,Skill::Master,Estate::Merchant,100,0,0}); w.next_id=8; w.initial_population=300;
    auto f=Muster(w,7); CHECK(Summarize(w,2).available==200); CHECK(Summarize(w,6).away==100);
    CHECK(ApplyOutcome(w,Losses(w,f)).ok); CHECK(Demobilize(w,f).ok);
    CHECK(Summarize(w,2).available==200 && Summarize(w,2).dead==0);
    CHECK(Summarize(w,6).available==65 && Summarize(w,6).recovering==15 && Summarize(w,6).dead==20);
}
void SpeedsAndFixedDays() {
    for (int speed: {0,1,3,5,10}) { auto w=Base(); CHECK(SetSpeed(w,speed).ok); CHECK(AdvanceRealTime(w,3'000'000).ok); CHECK(w.campaign_day==speed); CHECK(w.subday_microseconds==0); }
    auto a=Base(),b=Base(); for(int i=0;i<360;++i) AdvanceOneDay(a);
    CHECK(AdvanceRealTime(b,1'080'000'000).ok); CHECK(a==b); CHECK(a.campaign_day==360);
    auto w=Base(); CHECK(AdvanceRealTime(w,1'250'000).ok); CHECK(SetSpeed(w,0).ok); CHECK(AdvanceRealTime(w,20'000'000).ok);
    CHECK(w.subday_microseconds==1'250'000); CHECK(SetSpeed(w,3).ok); CHECK(AdvanceRealTime(w,750'000).ok); CHECK(w.campaign_day==1 && w.subday_microseconds==500'000);
    auto before=w; CHECK(!SetSpeed(w,2).ok); CHECK(!AdvanceRealTime(w,-1).ok); CHECK(w==before);
}
void SnapshotFullState() {
    auto w=Base(); auto f=Muster(w); CHECK(ApplyOutcome(w,Losses(w,f)).ok); CHECK(Demobilize(w,f).ok);
    CHECK(SetSpeed(w,5).ok); CHECK(AdvanceRealTime(w,700'001).ok); NextRandom(w,RngStream::Combat);
    w.formation_substep_microseconds=12345; w.formations.at(f).x=123.5; w.formations.at(f).target_facing=1.2;
    auto bytes=EncodeSnapshot(w); CHECK(!bytes.empty()); auto r=DecodeSnapshot(bytes); CHECK(r.ok); CHECK(r.world==w); CHECK(EncodeSnapshot(r.world)==bytes);
    auto live=Base(); CHECK(LoadSnapshot(live,bytes).ok); CHECK(live==w); CHECK(Summarize(live).available==165); CHECK(Summarize(live).recovering==15);
    CHECK(AdvanceRealTime(w,10'000'000).ok && AdvanceRealTime(live,10'000'000).ok); CHECK(w==live);
}
void FormationMembership() {
    auto w=Base(); auto f=Muster(w); CHECK(ActiveFormationCount(w,f)==100); CHECK(ApplyOutcome(w,Losses(w,f)).ok);
    CHECK(ActiveFormationCount(w,f)==80 && w.formations.at(f).service_ids.size()==80); CHECK(Summarize(w).away==80);
    CHECK(Demobilize(w,f).ok); CHECK(ActiveFormationCount(w,f)==0 && Summarize(w).away==0);
}
void InvalidTransactionsAtomic() {
    auto w=Base(); CHECK(ValidateWorld(w).ok); auto before=w;
    CHECK(!Mobilize(w,3,0).ok && !Mobilize(w,3,-1).ok && !Mobilize(w,3,201).ok && !Mobilize(w,99,1).ok); CHECK(w==before);
    auto f=Muster(w); auto good=Losses(w,f);
    auto reject=[&](Outcome o) {auto state=w; CHECK(!ApplyOutcome(w,o).ok); CHECK(w==state);};
    auto bad=good; bad.dispositions.pop_back(); reject(bad);
    bad=good; bad.dispositions.back()=bad.dispositions.front(); reject(bad);
    bad=good; bad.dispositions.front().service_id=99999; reject(bad);
    bad=good; bad.expected_revision++; reject(bad);
    bad=good; bad.transaction_id=0; reject(bad);
    bad=good; bad.dispositions.front().status=static_cast<ServiceStatus>(99); reject(bad);
    bad=good; bad.dispositions.front().status=ServiceStatus::ReturnedHealthy; reject(bad);
    auto other=Muster(w,3,100); bad=Losses(w,f); bad.dispositions[0].service_id=w.formations.at(other).service_ids[0]; reject(bad);
    CHECK(ApplyOutcome(w,Losses(w,f)).ok); CHECK(ValidateWorld(w).ok);
}
void Rechecksum(std::vector<std::uint8_t>& data) {
    std::uint64_t hash=14695981039346656037ULL;
    for(std::size_t i=28;i<data.size();++i) {hash^=data[i]; hash*=1099511628211ULL;}
    for(int i=0;i<8;++i) data[20+i]=static_cast<std::uint8_t>(hash>>(i*8));
}
void InvalidWorldAndSaves() {
    auto w=Base(); CHECK(ValidateWorld(w).ok); auto f=Muster(w); auto bytes=EncodeSnapshot(w); CHECK(bytes.size()>28);
    auto live=w; auto reject=[&](std::vector<std::uint8_t> data) { CHECK(!LoadSnapshot(live,data).ok); CHECK(live==w); };
    reject({}); auto corrupt=bytes; corrupt.back()^=1; reject(corrupt); corrupt=bytes; corrupt.pop_back(); reject(corrupt);
    corrupt=bytes; corrupt[8]=99; reject(corrupt);
    corrupt=bytes; for(int i=0;i<8;++i) corrupt[28+i]=255; Rechecksum(corrupt); reject(corrupt); // Valid checksum, negative day.
    corrupt=bytes; for(int i=0;i<4;++i) corrupt[224+i]=255; Rechecksum(corrupt); reject(corrupt); // Bounded transaction count. corrupt=bytes; corrupt.push_back(0); reject(corrupt);
    for (std::size_t i=0;i<bytes.size();i+=97) reject(std::vector<std::uint8_t>(bytes.begin(),bytes.begin()+i));
    auto invalid=w; invalid.cohorts.at(3).available=-1; CHECK(!ValidateWorld(invalid).ok && EncodeSnapshot(invalid).empty());
    invalid=w; invalid.services.begin()->second.origin.district_id=999; CHECK(!ValidateWorld(invalid).ok);
    invalid=w; invalid.formations.at(f).service_ids.push_back(invalid.formations.at(f).service_ids[0]); CHECK(!ValidateWorld(invalid).ok);
    invalid=w; invalid.formations.at(f).x=std::numeric_limits<double>::quiet_NaN(); CHECK(!ValidateWorld(invalid).ok);
    invalid=w; invalid.settlements.at(1).resources.seed_grain=501; CHECK(!ValidateWorld(invalid).ok);
    invalid=w; invalid.next_id=3; CHECK(!ValidateWorld(invalid).ok);
    invalid=w; invalid.services.begin()->second.status=ServiceStatus::ReturnedHealthy; CHECK(!ValidateWorld(invalid).ok);
}
void ReloadRejectsDuplicate() {
    auto w=Base(); auto f=Muster(w); auto o=Losses(w,f); CHECK(ApplyOutcome(w,o).ok);
    auto r=DecodeSnapshot(EncodeSnapshot(w)); CHECK(r.ok); auto before=r.world; o.expected_revision=r.world.revision;
    CHECK(!ApplyOutcome(r.world,o).ok && before==r.world); CHECK(Demobilize(r.world,f).ok); CHECK(Summarize(r.world).available==165);
}
void StableIdsAndRng() {
    auto w=Base(); auto f=Muster(w); auto old=w.formations.at(f).service_ids; CHECK(Demobilize(w,f).ok); auto f2=Muster(w);
    for (auto id:w.formations.at(f2).service_ids) CHECK(std::find(old.begin(),old.end(),id)==old.end());
    auto initial=w.rng; auto value=NextRandom(w,RngStream::Combat); CHECK(value!=0); CHECK(w.rng[5].counter==initial[5].counter+1);
    for(std::size_t i=0;i<7;++i) if(i!=5) CHECK(w.rng[i]==initial[i]);
    auto loaded=DecodeSnapshot(EncodeSnapshot(w)); CHECK(loaded.ok); CHECK(NextRandom(w,RngStream::Combat)==NextRandom(loaded.world,RngStream::Combat)); CHECK(w==loaded.world);
}
void CaptiveMissingDeserted() {
    auto w=Base(); auto f=Muster(w); auto o=Losses(w,f);
    o.dispositions[35].status=ServiceStatus::Captive; o.dispositions[36].status=ServiceStatus::Missing; o.dispositions[37].status=ServiceStatus::DesertedAway;
    CHECK(ApplyOutcome(w,o).ok); CHECK(Demobilize(w,f).ok); auto s=Summarize(w);
    CHECK(s.available==162 && s.recovering==15 && s.away==3 && s.dead==20 && s.total==200); CHECK(ValidateWorld(w).ok);
}
void FormationRoleSave() {
    auto w=Base(); auto f=Muster(w); CHECK(w.formations.at(f).role==TroopRole::Polearm);
    for(auto role:{TroopRole::Polearm,TroopRole::Bow,TroopRole::RetainerInfantry,TroopRole::SamuraiFoot,TroopRole::MountedSamurai}) {
        w.formations.at(f).role=role; auto decoded=DecodeSnapshot(EncodeSnapshot(w)); CHECK(decoded.ok && decoded.world==w);
    }
    w.formations.at(f).role=static_cast<TroopRole>(99); CHECK(!ValidateWorld(w).ok && EncodeSnapshot(w).empty());
}
void CounterBoundaries() {
    auto w=Base(); w.revision=std::numeric_limits<std::uint64_t>::max()-1;
    CHECK(ValidateWorld(w).ok); auto before=w; CHECK(!Mobilize(w,3,1).ok); CHECK(w==before);
    w=Base(); auto f=Muster(w); w.revision=std::numeric_limits<std::uint64_t>::max()-1;
    auto o=Losses(w,f); before=w; CHECK(!ApplyOutcome(w,o).ok && w==before); CHECK(!Demobilize(w,f).ok && w==before);
    CHECK(!AdvanceRealTime(w,MicrosecondsPerDay).ok && w==before);
    w=Base(); before=w; CHECK(!AdvanceRealTime(w,std::numeric_limits<std::int64_t>::max()).ok && w==before);
    w.next_id=std::numeric_limits<EntityId>::max()-2; before=w; CHECK(!Mobilize(w,3,1).ok && w==before);
}
void ScaleFixtures() {
    for(Quantity n:{1000,4000,8000,20000}) { auto w=MakeScaleWorld(n); CHECK(ValidateWorld(w).ok); CHECK(Summarize(w).away==n && Summarize(w).total==n); CHECK(w.formations.size()==static_cast<std::size_t>(n/100)); for(auto& [id,f]:w.formations) CHECK(f.service_ids.size()==100); }
}
void ScaleGridFitsCamera() {
    auto w=MakeScaleWorld(1000); std::size_t index=0; constexpr std::size_t columns=4;
    for(const auto& [id,f]:w.formations) {
        CHECK(f.x==static_cast<double>(index%columns)*1500.0);
        CHECK(f.y==static_cast<double>(index/columns)*1500.0);
        CHECK(f.target_x==f.x && f.target_y==f.y); ++index;
    }
}
void FormationSlotsAndMove() {
    auto w=MakeScaleWorld(1000); CHECK(w.formations.size()==10); std::vector<EntityId> ids;
    for(auto& [id,f]:w.formations) { ids.push_back(id); auto slots=FormationSlots(w,id); CHECK(slots.size()==100); std::set<std::pair<double,double>> unique; for(auto s:slots) unique.emplace(s.x,s.y); CHECK(unique.size()==100); }
    CHECK(IssueMove(w,ids,1000,2000,0.5).ok); CHECK(AssignGroup(w,ids,3).ok);
    for(std::size_t i=0;i<ids.size();++i) { auto& f=w.formations.at(ids[i]); CHECK(f.control_group==3 && f.moving); for(std::size_t j=0;j<i;++j) {auto& g=w.formations.at(ids[j]); CHECK(std::hypot(f.target_x-g.target_x,f.target_y-g.target_y)>1400);} }
    auto before=w; CHECK(!IssueMove(w,{ids[0],999999},0,0,0).ok); CHECK(w==before); CHECK(!AssignGroup(w,ids,10).ok); CHECK(w==before);
    CHECK(StepFormations(w,50'000).ok); CHECK(w.formations.begin()->second.x!=before.formations.begin()->second.x || w.formations.begin()->second.y!=before.formations.begin()->second.y);
    CHECK(Summarize(w)==Summarize(before)); CHECK(StepFormations(w,120'000'000).ok);
    for(auto& [id,f]:w.formations) CHECK(!f.moving && f.x==f.target_x && f.y==f.target_y && f.facing==f.target_facing);
}
void CompactLargeArmyDestinations() {
    auto w=MakeScaleWorld(20000); std::vector<EntityId> all;
    for(const auto& [id,f]:w.formations) all.push_back(id);
    constexpr double x=4000, y=-3000, epsilon=1e-6;
    for(std::size_t count:{1,10,11,80,200}) {
        std::vector<EntityId> ids(all.begin(),all.begin()+count);
        CHECK(IssueMove(w,ids,x,y,0).ok);
        std::vector<Slot> unrotated; for(auto id:ids) {const auto& f=w.formations.at(id); unrotated.push_back({f.target_x-x,f.target_y-y});}
        for(double facing:{0.0,1.5707963267948966,0.7}) {
            CHECK(IssueMove(w,ids,x,y,facing).ok);
            double sum_x=0,sum_y=0,min_forward=1e9,max_forward=-1e9,min_across=1e9,max_across=-1e9;
            for(std::size_t i=0;i<ids.size();++i) {
                const auto& f=w.formations.at(ids[i]); double dx=f.target_x-x,dy=f.target_y-y;
                CHECK(f.moving && f.target_facing==facing);
                CHECK(std::abs(dx-(std::cos(facing)*unrotated[i].x-std::sin(facing)*unrotated[i].y))<epsilon);
                CHECK(std::abs(dy-(std::sin(facing)*unrotated[i].x+std::cos(facing)*unrotated[i].y))<epsilon);
                sum_x+=dx; sum_y+=dy;
                double forward=std::cos(facing)*dx+std::sin(facing)*dy;
                double across=-std::sin(facing)*dx+std::cos(facing)*dy;
                min_forward=std::min(min_forward,forward); max_forward=std::max(max_forward,forward);
                min_across=std::min(min_across,across); max_across=std::max(max_across,across);
                for(std::size_t j=0;j<i;++j) {const auto& g=w.formations.at(ids[j]); CHECK(std::hypot(f.target_x-g.target_x,f.target_y-g.target_y)>=1500-epsilon);}
            }
            CHECK(std::abs(sum_x/count)<epsilon && std::abs(sum_y/count)<epsilon);
            if(count<=10) {
                CHECK(max_forward-min_forward<epsilon);
                CHECK(std::abs(max_across-min_across-(count-1)*1500.0)<epsilon);
            } else {
                double maximum_width=(std::ceil(std::sqrt(static_cast<double>(count)))-1)*1500.0;
                CHECK(max_forward-min_forward<=maximum_width+epsilon);
                CHECK(max_across-min_across<=maximum_width+epsilon);
                CHECK(max_forward-min_forward>=1500-epsilon);
            }
        }
    }
    auto before=w;
    CHECK(!IssueMove(w,all,1e9,1e9,0.7).ok && w==before);
    CHECK(!IssueMove(w,all,0,0,std::numeric_limits<double>::quiet_NaN()).ok && w==before);
    auto invalid=all; invalid.back()=invalid.front(); CHECK(!IssueMove(w,invalid,0,0,0).ok && w==before);
    invalid=all; invalid.back()=w.next_id; CHECK(!IssueMove(w,invalid,0,0,0).ok && w==before);
}
void FixedMovementAndSave() {
    auto a=MakeScaleWorld(1000); auto ids=std::vector<EntityId>{a.formations.begin()->first}; CHECK(IssueMove(a,ids,50000,10000,1.2).ok); auto b=a;
    CHECK(StepFormations(a,125'001).ok); for(int i=0;i<5;++i) CHECK(StepFormations(b,25'000).ok); CHECK(StepFormations(b,1).ok); CHECK(a==b);
    auto d=DecodeSnapshot(EncodeSnapshot(a)); CHECK(d.ok && d.world==a); CHECK(StepFormations(a,175'000).ok && StepFormations(d.world,175'000).ok); CHECK(a==d.world);
}
int main() {
    std::vector<std::pair<const char*,std::function<void()>>> tests={
        {"population conservation and requested 200-person proof",Conservation},{"outcome and demobilization exactly once",ExactlyOnce},
        {"wounded excluded from labor and recruitment",WoundedExcluded},{"six occupations and exact skill/estate return origin",OriginAndOccupations},
        {"district loss attribution and allied return",DistrictAndAlliedReturn},{"fixed days and all five speeds",SpeedsAndFixedDays},
        {"snapshot all ledgers resources generals clock RNG",SnapshotFullState},{"formation membership matches attached away records",FormationMembership},
        {"invalid transactions are immutable",InvalidTransactionsAtomic},{"malformed worlds and saves rejected before replacement",InvalidWorldAndSaves},
        {"reload rejects duplicate applied outcome",ReloadRejectsDuplicate},{"stable service IDs and independent RNG streams",StableIdsAndRng},
        {"captivity missing and desertion remain living away",CaptiveMissingDeserted},{"formation troop role validated and persisted",FormationRoleSave},{"counter overflow rejects without mutation",CounterBoundaries},{"1000 4000 8000 20000 finite scale fixtures",ScaleFixtures},
        {"scale grid fits square camera framing",ScaleGridFitsCamera},{"unique slots and nonoverlapping group move targets",FormationSlotsAndMove},{"large army destinations compact centered rotated and atomic",CompactLargeArmyDestinations},{"fixed 20Hz movement survives save continuation",FixedMovementAndSave}};
    int failed=0;
    for(auto& [name,test]:tests) { try {test(); std::cout<<"PASS "<<name<<'\n';} catch(const std::exception& e) {++failed; std::cerr<<"FAIL "<<name<<": "<<e.what()<<'\n';} }
    std::cout<<tests.size()-failed<<" passed, "<<failed<<" failed\n"; return failed?1:0;
}
