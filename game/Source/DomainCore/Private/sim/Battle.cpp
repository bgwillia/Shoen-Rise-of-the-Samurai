#include "domain/Battle.h"
#include <algorithm>
#include <cmath>
#include <limits>
#include <set>

namespace domain {
namespace {
constexpr std::int64_t StepMicroseconds=50'000;
constexpr double Spacing=110.0;
constexpr double FormationSpacing=1500.0;
constexpr double DistancePerStep=600.0/20.0;
Result ValidateSelection(const World& w,const std::vector<EntityId>& ids) {
    if(ids.empty() || ids.size()>MaxServiceRecords) return {false,"Select at least one active formation.",0};
    std::set<EntityId> unique;
    for(auto id:ids) {
        auto f=w.formations.find(id);
        if(f==w.formations.end() || f->second.demobilized || f->second.service_ids.empty() || !unique.insert(id).second) return {false,"Selection contains an absent, empty, demobilized or duplicate formation.",0};
    }
    return {true,{},0};
}
bool GoodPose(double n) {return std::isfinite(n) && std::abs(n)<=1.0e9;}
}
std::vector<Slot> FormationSlots(const World& w,EntityId id) {
    auto it=w.formations.find(id); if(it==w.formations.end()) return {};
    std::vector<Slot> slots; slots.reserve(it->second.service_ids.size());
    auto count=it->second.service_ids.size(); auto columns=std::min<std::size_t>(10,count); if(columns==0) return slots;
    auto rows=(count+columns-1)/columns;
    for(std::size_t i=0;i<count;++i) slots.push_back({(static_cast<double>(i%columns)-(static_cast<double>(columns)-1.0)/2.0)*Spacing,(static_cast<double>(i/columns)-(static_cast<double>(rows)-1.0)/2.0)*Spacing});
    return slots;
}
Result IssueMove(World& w,const std::vector<EntityId>& ids,double x,double y,double facing) {
    if(auto validation=ValidateSelection(w,ids); !validation.ok) return validation;
    if(!GoodPose(x) || !GoodPose(y) || !GoodPose(facing)) return {false,"Move target or facing is invalid.",0};
    // Small selections retain one frontage line. Large armies use a compact grid;
    // a short final row is centered, and the army centroid lands on the order target.
    const auto columns=ids.size()<=10 ? ids.size() : static_cast<std::size_t>(std::ceil(std::sqrt(static_cast<double>(ids.size()))));
    std::vector<Slot> targets; targets.reserve(ids.size());
    double mean_forward=0;
    for(std::size_t i=0;i<ids.size();++i) {
        const auto row=i/columns;
        const auto row_members=std::min(columns,ids.size()-row*columns);
        const double forward=static_cast<double>(row)*FormationSpacing;
        const double across=(static_cast<double>(i%columns)-(static_cast<double>(row_members)-1.0)/2.0)*FormationSpacing;
        targets.push_back({forward,across}); mean_forward+=forward;
    }
    mean_forward/=static_cast<double>(ids.size());
    const double cosine=std::cos(facing),sine=std::sin(facing);
    for(auto& target:targets) {
        const double forward=target.x-mean_forward,across=target.y;
        target={x+cosine*forward-sine*across,y+sine*forward+cosine*across};
        if(!GoodPose(target.x) || !GoodPose(target.y)) return {false,"Group move exceeds laboratory bounds.",0};
    }
    for(std::size_t i=0;i<ids.size();++i) {
        auto& f=w.formations.at(ids[i]); f.target_x=targets[i].x; f.target_y=targets[i].y; f.target_facing=facing; f.moving=true;
    }
    return {true,{},0};
}
Result AssignGroup(World& w,const std::vector<EntityId>& ids,std::uint8_t group) {
    if(group>9) return {false,"Control group must be 0 through 9 (0 clears assignment).",0};
    if(auto validation=ValidateSelection(w,ids); !validation.ok) return validation;
    // Assignment replaces this numbered group, matching RTS control-group semantics.
    if(group!=0) for(auto& [id,f]:w.formations) if(f.control_group==group) f.control_group=0;
    for(auto id:ids) w.formations.at(id).control_group=group;
    return {true,{},0};
}
Result StepFormations(World& w,std::int64_t us) {
    if(us<0 || us>3'600'000'000LL || w.formation_substep_microseconds<0 || w.formation_substep_microseconds>=StepMicroseconds) return {false,"Invalid formation elapsed time; maximum batch is one hour.",0};
    auto elapsed=us+w.formation_substep_microseconds; auto steps=elapsed/StepMicroseconds;
    for(std::int64_t step=0;step<steps;++step) {
        for(auto& [id,f]:w.formations) {
            if(!f.moving || f.demobilized || f.service_ids.empty()) continue;
            auto dx=f.target_x-f.x,dy=f.target_y-f.y; auto distance=std::hypot(dx,dy);
            if(distance<=DistancePerStep) {f.x=f.target_x; f.y=f.target_y; f.facing=f.target_facing; f.moving=false;}
            else {f.x+=dx/distance*DistancePerStep; f.y+=dy/distance*DistancePerStep; f.facing=std::atan2(dy,dx);}
        }
    }
    w.formation_substep_microseconds=elapsed%StepMicroseconds;
    return {true,{},static_cast<EntityId>(steps)};
}
}
