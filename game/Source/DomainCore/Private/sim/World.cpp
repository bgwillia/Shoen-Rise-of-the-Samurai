#include "domain/World.h"
#include "domain/Buildings.h"
#include <algorithm>
#include <cmath>
#include <limits>

namespace domain {
namespace {
constexpr Quantity MaxQuantity = 1'000'000'000;
constexpr Day MaxDay = 10'000'000;
bool GoodQuantity(Quantity q) { return q>=0 && q<=MaxQuantity; }
bool GoodSpeed(int speed) { return speed==0 || speed==1 || speed==3 || speed==5 || speed==10; }
bool Attached(ServiceStatus s) { return s==ServiceStatus::Active || s==ServiceStatus::WoundedAway; }
bool Away(ServiceStatus s) { return s<=ServiceStatus::DesertedAway; }
bool GoodOriginEnums(Occupation o, Skill s, Estate e) { return o<=Occupation::RetainerService && s<=Skill::Expert && e<=Estate::Religious; }
Origin CohortOrigin(const Cohort& c) { return {c.settlement_id,c.district_id,c.id,c.occupation,c.skill,c.estate}; }
Result Fail(const char* message) { return {false,message,0}; }
bool GoodName(const std::string& name) { return name.size()<=256 && name.find('\0')==std::string::npos; }
}
const char* OccupationName(Occupation value) {
    switch(value) {
    case Occupation::Agriculture:return "Agriculture";
    case Occupation::GeneralLabor:return "General labor";
    case Occupation::Smithing:return "Smithing";
    case Occupation::Commerce:return "Commerce";
    case Occupation::MaritimeWork:return "Maritime work";
    case Occupation::RetainerService:return "Retainer service";
    } return "Invalid occupation";
}
const char* StatusName(ServiceStatus value) {
    switch(value) {
    case ServiceStatus::Active:return "Active";
    case ServiceStatus::WoundedAway:return "Wounded away";
    case ServiceStatus::Captive:return "Captive";
    case ServiceStatus::Missing:return "Missing";
    case ServiceStatus::DesertedAway:return "Deserted away";
    case ServiceStatus::Dead:return "Dead";
    case ServiceStatus::ReturnedHealthy:return "Returned healthy";
    case ServiceStatus::ReturnedWounded:return "Returned wounded";
    } return "Invalid service status";
}
World MakeFoundationWorld() {
    World w;
    w.settlements.emplace(1,Settlement{1,"Foundation manor",{10'000,500,200,1'000,1'000,300,200}});
    w.districts.emplace(2,District{2,1,"Agricultural district"});
    w.cohorts.emplace(3,Cohort{3,1,2,Occupation::Agriculture,Skill::Trained,Estate::Ordinary,200,0,0});
    w.generals.emplace(4,General{4,"Foundation commander",60,55,50,45,65,60});
    w.next_id=5; w.initial_population=200;
    for(std::size_t i=0;i<w.rng.size();++i) w.rng[i].state=0x9e3779b97f4a7c15ULL*(i+1);
    return w;
}
World MakeScaleWorld(Quantity soldiers) {
    if(soldiers<=0 || soldiers>20'000 || soldiers%100!=0) return {};
    auto w=MakeFoundationWorld();
    w.cohorts.at(3).available=soldiers; w.initial_population=soldiers;
    const auto columns=static_cast<Quantity>(std::ceil(std::sqrt(static_cast<double>(soldiers/100))));
    for(Quantity i=0;i<soldiers/100;++i) {
        auto r=Mobilize(w,3,100); if(!r.ok) return {};
        auto& f=w.formations.at(r.id);
        f.x=static_cast<double>(i%columns)*1500.0; f.y=static_cast<double>(i/columns)*1500.0;
        f.target_x=f.x; f.target_y=f.y;
    }
    return w;
}
PopulationSummary Summarize(const World& w,EntityId district) {
    PopulationSummary s;
    for(const auto& [id,c]:w.cohorts) if(district==0 || c.district_id==district) {
        s.available+=c.available; s.dependent+=c.dependent_or_ineligible; s.recovering+=c.recovering_home;
    }
    for(const auto& [id,r]:w.services) if(district==0 || r.origin.district_id==district) {
        if(Away(r.status)) ++s.away;
        else if(r.status==ServiceStatus::Dead) ++s.dead;
    }
    s.living=s.available+s.dependent+s.recovering+s.away; s.total=s.living+s.dead;
    return s;
}
Quantity ActiveFormationCount(const World& w,EntityId id) {
    auto f=w.formations.find(id); if(f==w.formations.end()) return 0;
    Quantity count=0;
    for(auto service_id:f->second.service_ids) {
        auto s=w.services.find(service_id);
        if(s!=w.services.end() && s->second.formation_id==id && Attached(s->second.status)) ++count;
    }
    return count;
}
Result ValidateWorld(const World& w) {
    if(w.settlements.empty() || w.districts.empty() || w.cohorts.empty()) return Fail("World requires a settlement, district and cohort.");
    if(w.services.size()>MaxServiceRecords || w.formations.size()>MaxServiceRecords || w.cohorts.size()>MaxServiceRecords || w.districts.size()>MaxServiceRecords || w.settlements.size()>MaxServiceRecords || w.generals.size()>MaxServiceRecords || w.applied_transaction_ids.size()>MaxServiceRecords) return Fail("World exceeds the foundation record limit.");
    if(w.campaign_day<0 || w.campaign_day>MaxDay || !GoodSpeed(w.speed) || w.subday_microseconds<0 || w.subday_microseconds>=MicrosecondsPerDay || w.formation_substep_microseconds<0 || w.formation_substep_microseconds>=50'000) return Fail("Invalid campaign or formation clock.");
    if(w.revision==std::numeric_limits<std::uint64_t>::max() || w.next_id==0 || w.next_id==std::numeric_limits<EntityId>::max() || w.next_transaction_id==0 || w.next_transaction_id==std::numeric_limits<EntityId>::max()) return Fail("ID or revision counter exhausted.");
    if(!GoodQuantity(w.initial_population) || !GoodQuantity(w.births) || !GoodQuantity(w.admitted_immigrants) || !GoodQuantity(w.recorded_emigrants)) return Fail("Invalid population source accounting.");
    std::set<EntityId> ids;
    auto record=[&](EntityId key,EntityId id) { return key!=0 && key==id && id<w.next_id && ids.insert(id).second; };
    for(const auto& [id,s]:w.settlements) {
        if(!record(id,s.id) || !GoodName(s.name)) return Fail("Invalid or duplicate settlement ID/name.");
        const auto& r=s.resources;
        if(!GoodQuantity(r.food) || !GoodQuantity(r.timber) || !GoodQuantity(r.iron) || !GoodQuantity(r.treasury) || !GoodQuantity(r.seed_grain) || !GoodQuantity(r.fuel) || !GoodQuantity(r.equipment) || r.seed_grain>r.food) return Fail("Invalid resource stock or reserved seed exceeds food.");
    }
    for(const auto& [id,d]:w.districts) if(!record(id,d.id) || !GoodName(d.name) || !w.settlements.contains(d.settlement_id)) return Fail("Invalid district ID, name or settlement reference.");
    for(const auto& [id,c]:w.cohorts) {
        auto d=w.districts.find(c.district_id);
        if(!record(id,c.id) || d==w.districts.end() || d->second.settlement_id!=c.settlement_id || !GoodOriginEnums(c.occupation,c.skill,c.estate) || !GoodQuantity(c.available) || !GoodQuantity(c.dependent_or_ineligible) || !GoodQuantity(c.recovering_home)) return Fail("Invalid cohort origin, enum or population count.");
    }
    for(const auto& [id,g]:w.generals) {
        if(!record(id,g.id) || !GoodName(g.name)) return Fail("Invalid general ID or name.");
        for(int a:{g.command,g.coordination,g.scouting,g.secrecy,g.terrain_knowledge,g.logistics}) if(a<0 || a>100) return Fail("General attribute must be in 0..100.");
    }
    std::set<EntityId> attached;
    for(const auto& [id,f]:w.formations) {
        if(!record(id,f.id) || !GoodName(f.name) || f.service_ids.size()>MaxServiceRecords || f.control_group>9 || f.role>TroopRole::MountedSamurai || (f.demobilized && (!f.service_ids.empty() || f.moving))) return Fail("Invalid formation metadata or demobilized membership.");
        for(double v:{f.x,f.y,f.facing,f.target_x,f.target_y,f.target_facing}) if(!std::isfinite(v) || std::abs(v)>1.0e9) return Fail("Formation pose is invalid or outside lab bounds.");
        for(auto sid:f.service_ids) {
            auto r=w.services.find(sid);
            if(r==w.services.end() || !attached.insert(sid).second || r->second.formation_id!=id || !Attached(r->second.status)) return Fail("Formation contains a foreign, duplicate or non-attached service record.");
        }
    }
    for(const auto& [id,r]:w.services) {
        auto c=w.cohorts.find(r.origin.cohort_id);
        if(!record(id,r.id) || c==w.cohorts.end() || r.origin!=CohortOrigin(c->second) || r.status>ServiceStatus::ReturnedWounded) return Fail("Invalid service ID, immutable origin or status.");
        if(Attached(r.status)) {if(r.formation_id==0 || !attached.contains(id)) return Fail("Active or wounded service record lacks exclusive formation membership.");}
        else if(r.formation_id!=0 || attached.contains(id)) return Fail("Non-attached service record still belongs to a formation.");
    }
    for(auto id:w.applied_transaction_ids) if(id==0 || id>=w.next_transaction_id) return Fail("Invalid applied transaction ID or next counter.");
    for(const auto& r:w.rng) if(r.state==0 || r.counter==std::numeric_limits<std::uint64_t>::max()) return Fail("Invalid or exhausted RNG stream.");
    auto s=Summarize(w);
    if(auto buildings=ValidateBuildingState(w); !buildings.ok) return buildings;
    if(s.total+w.recorded_emigrants!=w.initial_population+w.births+w.admitted_immigrants) return Fail("Population conservation failed: home + away + dead + emigrants must equal all sources.");
    return {true,{},0};
}
Result Mobilize(World& w,EntityId cohort,Quantity count) {
    if(auto validation=ValidateWorld(w); !validation.ok) return validation;
    if(w.revision>=std::numeric_limits<std::uint64_t>::max()-1) return Fail("World revision counter is exhausted.");
    auto it=w.cohorts.find(cohort);
    if(it==w.cohorts.end()) return Fail("Recruitment cohort does not exist.");
    if(count<=0) return Fail("Mobilization requires a positive person count.");
    if(count>it->second.available) return Fail("Not enough available healthy workers in that cohort.");
    if(static_cast<std::uint64_t>(count)>MaxServiceRecords-w.services.size() || w.formations.size()==MaxServiceRecords || w.next_id>std::numeric_limits<EntityId>::max()-static_cast<EntityId>(count)-2) return Fail("Mobilization exceeds the record or ID limit.");
    Formation f; f.id=w.next_id++; f.name="Formation "+std::to_string(f.id); f.service_ids.reserve(static_cast<std::size_t>(count));
    for(Quantity i=0;i<count;++i) {
        auto id=w.next_id++; f.service_ids.push_back(id);
        w.services.emplace(id,ServiceRecord{id,CohortOrigin(it->second),ServiceStatus::Active,f.id});
    }
    it->second.available-=count; auto formation_id=f.id; w.formations.emplace(formation_id,std::move(f)); ++w.revision;
    return {true,{},formation_id};
}
Result ApplyOutcome(World& w,const Outcome& o) {
    if(auto validation=ValidateWorld(w); !validation.ok) return validation;
    if(w.revision>=std::numeric_limits<std::uint64_t>::max()-1) return Fail("World revision counter is exhausted.");
    if(o.transaction_id==0 || o.transaction_id>=std::numeric_limits<EntityId>::max()-1 || w.applied_transaction_ids.contains(o.transaction_id)) return Fail("Outcome transaction is invalid or already applied.");
    if(w.applied_transaction_ids.size()==MaxServiceRecords) return Fail("Applied transaction ledger is full.");
    if(o.expected_revision!=w.revision) return Fail("Outcome is stale: the world revision changed.");
    auto fit=w.formations.find(o.formation_id);
    if(fit==w.formations.end() || fit->second.demobilized || fit->second.service_ids.empty()) return Fail("Outcome formation is absent, empty or demobilized.");
    if(o.dispositions.size()!=fit->second.service_ids.size()) return Fail("Outcome must assign exactly one disposition to every formation member.");
    std::set<EntityId> seen;
    for(const auto& d:o.dispositions) {
        auto it=w.services.find(d.service_id);
        if(it==w.services.end() || it->second.formation_id!=o.formation_id || !Attached(it->second.status) || !seen.insert(d.service_id).second) return Fail("Outcome has a foreign, stale or duplicate service ID.");
        if(d.status>ServiceStatus::Dead || (it->second.status==ServiceStatus::WoundedAway && d.status==ServiceStatus::Active)) return Fail("Outcome has an invalid disposition or silently heals a wounded soldier.");
    }
    // All references and dispositions are valid before the first ledger write.
    for(const auto& d:o.dispositions) {
        auto& r=w.services.at(d.service_id); r.status=d.status; if(!Attached(r.status)) r.formation_id=0;
    }
    auto& members=fit->second.service_ids;
    members.erase(std::remove_if(members.begin(),members.end(),[&](EntityId id){return !Attached(w.services.at(id).status);}),members.end());
    if(members.empty()) fit->second.moving=false;
    w.applied_transaction_ids.insert(o.transaction_id); w.next_transaction_id=std::max(w.next_transaction_id,o.transaction_id+1); ++w.revision;
    return {true,{},o.transaction_id};
}
Result Demobilize(World& w,EntityId formation) {
    if(auto validation=ValidateWorld(w); !validation.ok) return validation;
    if(w.revision>=std::numeric_limits<std::uint64_t>::max()-1) return Fail("World revision counter is exhausted.");
    auto it=w.formations.find(formation);
    if(it==w.formations.end() || it->second.demobilized) return Fail("Formation is absent or already demobilized.");
    std::map<EntityId,std::pair<Quantity,Quantity>> returns;
    for(auto id:it->second.service_ids) {
        const auto& r=w.services.at(id); auto& counts=returns[r.origin.cohort_id];
        if(r.status==ServiceStatus::Active) ++counts.first; else ++counts.second;
    }
    for(const auto& [id,counts]:returns) {const auto& c=w.cohorts.at(id); if(c.available>MaxQuantity-counts.first || c.recovering_home>MaxQuantity-counts.second) return Fail("Returning population exceeds cohort limits.");}
    for(const auto& [id,counts]:returns) {auto& c=w.cohorts.at(id); c.available+=counts.first; c.recovering_home+=counts.second;}
    for(auto id:it->second.service_ids) {auto& r=w.services.at(id); r.status=r.status==ServiceStatus::Active?ServiceStatus::ReturnedHealthy:ServiceStatus::ReturnedWounded; r.formation_id=0;}
    it->second.service_ids.clear(); it->second.demobilized=true; it->second.moving=false; ++w.revision;
    return {true,{},formation};
}
Result SetSpeed(World& w,int speed) {
    if(!GoodSpeed(speed)) return Fail("Speed must be pause, 1, 3, 5 or 10.");
    w.speed=speed; return {true,{},0};
}
void AdvanceOneDay(World& w) {
    if(w.campaign_day>=MaxDay || w.revision>=std::numeric_limits<std::uint64_t>::max()-1) return;
    ++w.campaign_day; ++w.revision;
    // Foundation intentionally has no economy, births, recovery or weather rolls.
}
Result AdvanceRealTime(World& w,std::int64_t us) {
    if(us<0 || !GoodSpeed(w.speed) || w.subday_microseconds<0 || w.subday_microseconds>=MicrosecondsPerDay) return Fail("Invalid elapsed time or clock state.");
    if(w.speed==0) return {true,{},0};
    if(us>(std::numeric_limits<std::int64_t>::max()-w.subday_microseconds)/w.speed) return Fail("Elapsed time exceeds clock bounds.");
    auto scaled=w.subday_microseconds+us*w.speed; auto days=scaled/MicrosecondsPerDay;
    if(days>1'000'000 || w.campaign_day<0 || w.campaign_day>MaxDay-days || static_cast<std::uint64_t>(days)>=std::numeric_limits<std::uint64_t>::max()-w.revision) return Fail("Elapsed time exceeds campaign bounds; submit smaller batches.");
    for(Day i=0;i<days;++i) AdvanceOneDay(w);
    w.subday_microseconds=scaled%MicrosecondsPerDay; return {true,{},static_cast<EntityId>(days)};
}
std::uint64_t NextRandom(World& w,RngStream stream) {
    auto i=static_cast<std::size_t>(stream); if(i>=w.rng.size()) return 0;
    auto& r=w.rng[i]; if(r.state==0 || r.counter>=std::numeric_limits<std::uint64_t>::max()-1) return 0;
    r.state^=r.state>>12; r.state^=r.state<<25; r.state^=r.state>>27; ++r.counter;
    return r.state*2685821657736338717ULL;
}
}
