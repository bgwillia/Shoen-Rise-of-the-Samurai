#include "domain/Terrain.h"
#include "domain/Prototype.h"
#include "domain/Buildings.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <limits>
#include <queue>
#include <set>

namespace domain {
namespace {
constexpr int Span=31,MinCell=-15,CellCount=Span*Span;
constexpr double Grid=1600,Pi=3.14159265358979323846;
thread_local TerrainTimingHook Timing=nullptr;
struct TimedNavigation {
 TerrainTimingHook hook=Timing;
 std::chrono::steady_clock::time_point start=hook?std::chrono::steady_clock::now():std::chrono::steady_clock::time_point{};
 ~TimedNavigation(){if(hook)hook(std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count());}
};
struct Cell {int x=0,y=0;bool operator==(const Cell&)const=default;};
int Index(Cell c){return (c.x-MinCell)*Span+c.y-MinCell;}
bool InGrid(Cell c){return c.x>=MinCell&&c.x<MinCell+Span&&c.y>=MinCell&&c.y<MinCell+Span;}
Cell FromIndex(int i){return {i/Span+MinCell,i%Span+MinCell};}
Cell Snap(Point2 p){return {static_cast<int>(std::llround(p.x/Grid)),static_cast<int>(std::llround(p.y/Grid))};}
Point2 Position(Cell c){return {c.x*Grid,c.y*Grid};}
bool Inside(const TerrainRect& r,double x,double y,double inset=0){return x>=r.min_x+inset&&x<=r.max_x-inset&&y>=r.min_y+inset&&y<=r.max_y-inset;}
int Distance(Cell a,Cell b){return std::abs(a.x-b.x)+std::abs(a.y-b.y);}
bool Passable(Cell c,CrossingRoute route){if(!InGrid(c))return false;auto p=Position(c);if(!TerrainWalkable(p.x,p.y))return false;if(std::abs(c.x)<=1){if(route==CrossingRoute::Bridge&&c.y!=0)return false;if(route==CrossingRoute::Ford&&(c.y<5||c.y>7))return false;}return true;}
using Occupancy=std::array<EntityId,CellCount>;
const std::array<Cell,4> Directions{{{1,0},{0,1},{0,-1},{-1,0}}};
std::vector<Point2> FindPath(Cell start,Cell goal,CrossingRoute route,const Occupancy& occupied,EntityId self) {
 auto can_pass=[&](Cell c){
  bool normal=Passable(c,route);
  // Fixed directional passing lanes: northbound frontage for eastward traffic,
  // south frontage for westward traffic. The bridge intentionally stays single lane.
  if(normal&&std::abs(c.x)<=1&&c.y>=5&&c.y<=7&&start.x!=goal.x)normal=c.y==(goal.x>start.x?7:5);
  return normal||(InGrid(c)&&std::abs(start.x)<=1&&std::abs(c.x)<=1&&c.y==start.y&&TerrainWalkable(c.x*Grid,c.y*Grid));
 };
 if(!can_pass(start)||!Passable(goal,route))return {};
 if(start==goal)return {Position(goal)};
 std::array<int,CellCount> distance,parent;distance.fill(100000);parent.fill(-1);
 using QueueNode=std::pair<int,int>;std::priority_queue<QueueNode,std::vector<QueueNode>,std::greater<QueueNode>> open;
 distance[Index(start)]=0;open.push({Distance(start,goal),Index(start)});
 while(!open.empty()) {
  const auto [score,index]=open.top();open.pop();const Cell here=FromIndex(index);if(score!=distance[index]+Distance(here,goal))continue;
  if(here==goal){std::vector<Point2> path;for(int i=index;i!=Index(start);i=parent[i])path.push_back(Position(FromIndex(i)));std::reverse(path.begin(),path.end());return path;}
  for(auto d:Directions){Cell next{here.x+d.x,here.y+d.y};if(!can_pass(next))continue;const auto ni=Index(next);if(occupied[ni]&&occupied[ni]!=self&&!(next==goal))continue;
   if(distance[ni]>distance[index]+1){distance[ni]=distance[index]+1;parent[ni]=index;open.push({distance[ni]+Distance(next,goal),ni});}}
 }
 return {};
}
TerrainPath NewPath(const Formation& f) {TerrainPath n;n.cell=Position(Snap({f.x,f.y}));n.transit=n.cell;n.destination=n.cell;return n;}
Occupancy Occupied(const World& w,const std::map<EntityId,CombatUnit>& units,const std::map<EntityId,TerrainPath>& paths) {
 Occupancy occupied{};for(const auto&[id,u]:units)if(u.alive>0){const auto& f=w.formations.at(id);auto p=paths.find(id);Cell c=Snap(p==paths.end()?Point2{f.x,f.y}:p->second.cell);if(InGrid(c))occupied[Index(c)]=id;if(p!=paths.end()&&p->second.in_transit){c=Snap(p->second.transit);if(InGrid(c))occupied[Index(c)]=id;}}
 return occupied;
}
Result PlanOrders(World& w,PrototypeState& p,const std::vector<EntityId>& ids,double x,double y,double facing,CrossingRoute route,bool enemy) {
 if(!p.terrain_enabled||p.phase!=BattlePhase::Fighting)return {false,"Terrain orders require a fighting terrain battle.",0};
 if(ids.empty()||ids.size()>100||!std::isfinite(x)||!std::isfinite(y)||!std::isfinite(facing)||std::abs(facing)>1e6||!TerrainWalkable(x,y)||route>CrossingRoute::Ford)return {false,"Order target is outside traversable terrain.",0};
 auto& units=enemy?p.enemy_units:p.player_units;auto& paths=enemy?p.navigation.enemy_paths:p.navigation.player_paths;
 std::set<EntityId> selected;std::vector<EntityId> ordered=ids;
 double center_x=0,center_y=0;
 for(auto id:ids){auto u=units.find(id);if(!selected.insert(id).second||u==units.end()||u->second.alive<=0||u->second.routed)return {false,"Selection has duplicate, missing, routed or dead formations.",0};const auto& f=w.formations.at(id);center_x+=f.x;center_y+=f.y;}
 center_x/=ids.size();center_y/=ids.size();
 // Current frontage ordering survives a translated or rotated line command.
 double facing_sine=0,facing_cosine=0;for(auto id:ids){facing_sine+=std::sin(w.formations.at(id).facing);facing_cosine+=std::cos(w.formations.at(id).facing);}const double old_facing=std::atan2(facing_sine,facing_cosine);
 auto projection=[&](EntityId id){const auto&f=w.formations.at(id);return -(f.x-center_x)*std::sin(old_facing)+(f.y-center_y)*std::cos(old_facing);};
 std::stable_sort(ordered.begin(),ordered.end(),[&](EntityId a,EntityId b){auto pa=projection(a),pb=projection(b);return std::abs(pa-pb)>1?pa<pb:a<b;});
 std::set<int> reserved;for(const auto&[id,u]:units)if(u.alive>0&&!selected.contains(id)){auto it=paths.find(id);auto point=it==paths.end()?Point2{w.formations.at(id).x,w.formations.at(id).y}:it->second.destination;auto c=Snap(point);if(InGrid(c))reserved.insert(Index(c));}
 const auto occupied=Occupied(w,units,paths);std::vector<std::pair<EntityId,TerrainPath>> plans;plans.reserve(ids.size());
 for(std::size_t i=0;i<ordered.size();++i){const auto id=ordered[i];const auto& f=w.formations.at(id);TerrainPath n=paths.contains(id)?paths.at(id):NewPath(f);
  const double across=(static_cast<double>(i)-(ordered.size()-1)*.5)*Grid;
  Cell ideal=Snap({x-std::sin(facing)*across,y+std::cos(facing)*across}),goal{};bool found=false;
  // Snap and reserve unique reachable spaces near the requested line, without editing live paths.
  int best=100000;for(int cx=MinCell;cx<MinCell+Span;++cx)for(int cy=MinCell;cy<MinCell+Span;++cy){Cell c{cx,cy};if(!Passable(c,route)||reserved.contains(Index(c)))continue;if((x<-2400&&c.x>=-1)||(x>2400&&c.x<=1))continue;const int cost=Distance(c,ideal);if(cost<best){best=cost;goal=c;found=true;}}
  if(!found)return {false,"No unreserved destination space for the whole line.",0};reserved.insert(Index(goal));
  const auto start=Snap(n.in_transit?n.transit:n.cell);n.route=route;n.destination=Position(goal);n.blocked_seconds=0;n.crossed=false;n.had_crossing=(start.x<0&&goal.x>0)||(start.x>0&&goal.x<0);
  // Static routes are valid even when a current friendly body is temporarily in the way.
  Occupancy empty{};n.waypoints=FindPath(start,goal,route,empty,id);n.next_waypoint=0;
  if(n.waypoints.empty())return {false,"No terrain route for formation "+std::to_string(id)+" from ("+std::to_string(start.x)+","+std::to_string(start.y)+") to ("+std::to_string(goal.x)+","+std::to_string(goal.y)+") grid cells.",0};
  if(n.in_transit)n.waypoints.insert(n.waypoints.begin(),n.transit);
  plans.push_back({id,std::move(n)});
 }
 (void)occupied;
 for(auto&[id,n]:plans){auto&f=w.formations.at(id);f.target_x=n.destination.x;f.target_y=n.destination.y;f.target_facing=facing;f.moving=true;paths[id]=std::move(n);}
 p.navigation.path_requests+=plans.size();if(!enemy)++p.battle.commands;return {true,{},0};
}
void PlaceSide(World& w,bool enemy) {
 int infantry=0,bows=0,elite=0;int infantry_count=0;
 for(const auto&[id,f]:w.formations)if(!f.demobilized&&!f.service_ids.empty()&&f.role==TroopRole::Polearm)++infantry_count;
 const double elite_x=std::max(9600.0,6400+((infantry_count+10)/11)*1600.0),bow_x=elite_x+1600;
 for(auto&[id,f]:w.formations)if(!f.demobilized&&!f.service_ids.empty()){
  int i=0;double x=0;
  if(enemy){if(f.role==TroopRole::Bow){i=bows++;x=bow_x+(i/11)*1600;}else if(f.role>=TroopRole::RetainerInfantry){i=elite++;x=elite_x;}else{i=infantry++;x=6400+(i/11)*1600;}}
  else {i=infantry++;x=-9600-(i/11)*1600;}
  f.x=x;f.y=(i%11-5)*1600;f.facing=enemy?Pi:0;f.target_x=f.x;f.target_y=f.y;f.target_facing=f.facing;f.moving=false;
 }
}
void NavigateSide(World& w,World& opposition,PrototypeState& p,bool enemy,double dt) {
 auto& units=enemy?p.enemy_units:p.player_units;auto& others=enemy?p.player_units:p.enemy_units;auto& paths=enemy?p.navigation.enemy_paths:p.navigation.player_paths;
 auto occupied=Occupied(w,units,paths);
 for(auto&[id,u]:units){if(u.alive<=0)continue;auto& f=w.formations.at(id);auto found=paths.find(id);if(found==paths.end()){paths.emplace(id,NewPath(f));found=paths.find(id);}auto& n=found->second;
  // A stationary formation may be deliberately repositioned by a development setup.
  if(!n.in_transit&&!f.moving&&std::hypot(f.x-n.cell.x,f.y-n.cell.y)>1)n=NewPath(f);
  const Formation* nearest=nullptr;double nearest_distance=1e100;
  for(const auto&[other_id,other]:others)if(other.alive>0&&!other.routed){const auto&of=opposition.formations.at(other_id);auto distance=std::hypot(f.x-of.x,f.y-of.y);if(distance<nearest_distance){nearest_distance=distance;nearest=&of;}}
  const bool escaped=enemy?f.x>=20000:f.x<=-20000;
  if(u.routed&&!f.moving&&!escaped){
   // Routed bodies still occupy space. Reserve distinct exit cells so the first
   // survivor reaching safety cannot permanently block every following retreat.
   std::set<int> exits;
   for(const auto&[other_id,other]:units)if(other_id!=id&&other.alive>0){auto it=paths.find(other_id);const auto&of=w.formations.at(other_id);auto c=Snap(it==paths.end()?Point2{of.x,of.y}:it->second.destination);if(InGrid(c))exits.insert(Index(c));}
   const Cell ideal{enemy?14:-14,Snap(n.cell).y};Cell exit=ideal;int best=100000;
   for(int column:{14,13})for(int row=MinCell;row<MinCell+Span;++row){Cell c{enemy?column:-column,row};if(exits.contains(Index(c)))continue;const int cost=Distance(c,ideal);if(cost<best){best=cost;exit=c;}}
   Occupancy empty{};n.destination=Position(exit);n.route=((enemy&&f.x<0)||(!enemy&&f.x>0))?CrossingRoute::Ford:CrossingRoute::Automatic;
   ++p.navigation.path_requests;n.waypoints=FindPath(Snap(n.in_transit?n.transit:n.cell),exit,n.route,empty,id);if(n.waypoints.empty())++p.navigation.path_failures;
   if(n.in_transit)n.waypoints.insert(n.waypoints.begin(),n.transit);n.next_waypoint=0;f.moving=!n.waypoints.empty();
  }
  // Defend the east bank; bows stand behind the line, samurai react earlier to a flank.
  if(enemy&&!u.routed&&nearest&&nearest->x>1600&&nearest_distance<(f.role==TroopRole::Bow?14000:f.role>=TroopRole::RetainerInfantry?11000:8000)){
   const bool bow=f.role==TroopRole::Bow;double desired_x=nearest->x,desired_y=nearest->y;
   if(bow){if(nearest_distance<2800){desired_x=f.x+3200;}else if(nearest_distance>p.config.troops[1].range_cm*.85){desired_x=f.x-1600;}else desired_x=f.x;}
   if((!bow||std::abs(desired_x-f.x)>1)&&(!f.moving||p.battle_steps%80==id%80)){
    auto r=PlanOrders(w,p,{id},desired_x,desired_y,std::atan2(nearest->y-f.y,nearest->x-f.x),CrossingRoute::Automatic,true);(void)r;
   }
   if(!f.moving)f.facing=std::atan2(nearest->y-f.y,nearest->x-f.x);
  }
  if(!f.moving){u.fatigue=std::max(0.0,u.fatigue-.15*dt);continue;}
  if(!n.in_transit){
   while(n.next_waypoint<n.waypoints.size()&&Snap(n.waypoints[n.next_waypoint])==Snap(n.cell))++n.next_waypoint;
   if(n.next_waypoint>=n.waypoints.size()){f.moving=false;f.facing=f.target_facing;continue;}
   auto next=Snap(n.waypoints[n.next_waypoint]);
   if(occupied[Index(next)]&&occupied[Index(next)]!=id){
    n.blocked_seconds+=dt;u.fatigue=std::max(0.0,u.fatigue-.15*dt);++p.navigation.waiting_formations;if(n.blocked_seconds>10)++p.navigation.stuck_formations;
    if(static_cast<int>(n.blocked_seconds/dt)%20==0){++p.navigation.path_requests;auto new_path=FindPath(Snap(n.cell),Snap(n.destination),n.route,occupied,id);if(!new_path.empty()){n.waypoints=std::move(new_path);n.next_waypoint=0;}else ++p.navigation.path_failures;}
    continue;
   }
   occupied[Index(next)]=id;n.transit=Position(next);n.in_transit=true;
  }
  const double dx=n.transit.x-f.x,dy=n.transit.y-f.y,distance=std::hypot(dx,dy);
  double travel=p.config.troops[static_cast<std::size_t>(f.role)].movement_cm_per_second*TerrainMovementFactor(f.x,f.y)*(1-u.fatigue*.003)*dt;
  if(!u.routed&&nearest&&nearest_distance<2400&&nearest_distance>.001&&distance>.001){const double toward=(dx*(nearest->x-f.x)+dy*(nearest->y-f.y))/(distance*nearest_distance);if(toward>.5)travel=std::min(travel,std::max(0.0,nearest_distance-1500));}
  travel=std::min(travel,distance);
  if(travel>.001){f.x+=dx/distance*travel;f.y+=dy/distance*travel;f.facing=std::atan2(dy,dx);n.blocked_seconds=0;u.fatigue=std::min(100.0,u.fatigue+.18*dt);}
  else if(distance>.001){u.fatigue=std::max(0.0,u.fatigue-.15*dt);n.blocked_seconds+=dt;++p.navigation.waiting_formations;/* enemy contact is engagement, not a traffic deadlock */}
  if(distance-travel<=.001){auto old=Snap(n.cell);if(occupied[Index(old)]==id)occupied[Index(old)]=0;n.cell=n.transit;n.in_transit=false;++n.next_waypoint;
   if(n.had_crossing&&!n.crossed&&((n.destination.x>0&&n.cell.x>=3200)||(n.destination.x<0&&n.cell.x<=-3200))){n.crossed=true;++p.navigation.crossing_completions;if(std::abs(f.y)<2000)++p.navigation.bridge_completions;else ++p.navigation.ford_completions;}
   if(n.next_waypoint>=n.waypoints.size()){f.moving=false;f.facing=f.target_facing;}
  }
 }
}
}
void SetTerrainTimingHook(TerrainTimingHook hook){Timing=hook;}
const TerrainGeometry& PrototypeTerrain(){static const TerrainGeometry g;return g;}
bool TerrainWalkable(double x,double y,double radius){const auto&g=PrototypeTerrain();if(!std::isfinite(x)||!std::isfinite(y)||!std::isfinite(radius)||radius<0||!Inside(g.bounds,x,y,radius))return false;if(x<-1000-radius||x>1000+radius)return true;return (y>=g.bridge.min_y+radius&&y<=g.bridge.max_y-radius)||(y>=g.ford.min_y+radius&&y<=g.ford.max_y-radius);}
double TerrainHeight(double x,double y){const auto&g=PrototypeTerrain();if(!Inside(g.hill,x,y))return 0;const auto edge=std::min({x-g.hill.min_x,g.hill.max_x-x,y-g.hill.min_y,g.hill.max_y-y});return g.hill_height_cm*std::clamp(edge/1600.0,0.0,1.0);}
double TerrainMovementFactor(double x,double y){return Inside(PrototypeTerrain().forest,x,y)?.55:1.0;}
Result MakeTerrainPrototype(World& w,PrototypeState& p){World candidate;PrototypeState state;if(auto r=MakePrototype(candidate,state);!r)return r;state.terrain_enabled=true;state.config.ordinary_formation_size=100;state.config.elite_formation_size=40;state.config.base_food_capacity=5000;state.config.granary_food_capacity=20000;for(std::size_t i=0;i<state.config.troops.size();++i)state.config.troops[i].range_cm=i==static_cast<std::size_t>(TroopRole::Bow)?7000:1650;
 candidate.cohorts.at(3).available=3400;candidate.cohorts.at(3).dependent_or_ineligible=1280;candidate.cohorts.at(5).available=1000;candidate.cohorts.at(6).available=200;candidate.cohorts.at(7).available=120;candidate.initial_population=6000;
 auto&s=candidate.settlements.at(1).resources;s.food=40000;s.timber=4000;s.iron=1600;s.fuel=2400;s.equipment=2200;state.elite_equipment=120;
 auto&a=candidate.build_areas.at(1);a.origin_x_cm=-16000;a.origin_y_cm=-12000;a.columns=33;a.rows=25;a.heights_cm.assign(825,0);
 for(int i=0;i<14;++i){const char*type=i<7?"house":i<10?"farm":i<12?"smithy":"granary";PlacementCommand c{candidate.next_transaction_id,type,1,2,-13600+(i%7)*2000,-9000+(i/7)*2000,0};auto r=PlaceBuilding(candidate,state.catalog,c);if(!r.ok)return {false,"Expanded terrain settlement setup failed.",0};}
 state.last_day=ForecastPrototype(candidate,state);if(auto r=ValidateWorld(candidate);!r)return r;w=std::move(candidate);p=std::move(state);return {true,{},0};}
Result MusterTerrainArmy(World& w,PrototypeState& p){if(!p.terrain_enabled||p.phase!=BattlePhase::Settlement)return {false,"Muster requires the terrain settlement.",0};for(const auto&[id,f]:w.formations)if(!f.demobilized&&!f.service_ids.empty())return {false,"Return the current army before a new muster.",0};World candidate=w;PrototypeState state=p;Quantity recruited=0;struct Request{EntityId cohort;Quantity count;TroopRole role;};for(auto r:std::array<Request,5>{{{3,1200,TroopRole::Polearm},{5,300,TroopRole::Polearm},{6,100,TroopRole::Polearm},{3,600,TroopRole::Bow},{7,120,TroopRole::SamuraiFoot}}}){auto gear=r.role==TroopRole::SamuraiFoot?state.elite_equipment:candidate.settlements.at(1).resources.equipment;const auto count=std::min({r.count,candidate.cohorts.at(r.cohort).available,gear});if(!count)continue;if(auto result=RecruitPrototype(candidate,state,r.cohort,count,r.role);!result)return result;recruited+=count;}if(!recruited)return {false,"No available people and equipment for a second army.",0};w=std::move(candidate);p=std::move(state);return {true,{},static_cast<EntityId>(recruited)};}
Result MakeTerrainCombatFixture(World& w,PrototypeState& p,Quantity count){if(count<500||count>4000||count%100)return {false,"Terrain fixture needs 500..4000 per side, in hundreds.",0};World candidate;PrototypeState state;if(auto r=MakeTerrainPrototype(candidate,state);!r)return r;const auto elite=std::min<Quantity>(120,(count/20/40)*40),bows=(count/5/100)*100,spears=count-bows-elite;candidate.settlements.at(1).resources.equipment=count;for(Quantity n=spears;n>0;n-=std::min<Quantity>(2000,n))if(auto r=RecruitPrototype(candidate,state,3,std::min<Quantity>(2000,n),TroopRole::Polearm);!r)return r;if(auto r=RecruitPrototype(candidate,state,5,bows,TroopRole::Bow);!r)return r;if(elite)if(auto r=RecruitPrototype(candidate,state,7,elite,TroopRole::SamuraiFoot);!r)return r;if(auto r=BeginPrototypeBattle(candidate,state,count);!r)return r;std::vector<EntityId> main,flank;for(const auto&[id,f]:candidate.formations)(f.role>=TroopRole::RetainerInfantry?flank:main).push_back(id);if(auto r=IssueTerrainOrder(candidate,state,main,8000,0,0,CrossingRoute::Bridge);!r)return r;if(!flank.empty())if(auto r=IssueTerrainOrder(candidate,state,flank,8000,9600,-Pi/2,CrossingRoute::Ford);!r)return r;w=std::move(candidate);p=std::move(state);return {true,{},0};}
Result IssueTerrainOrder(World& w,PrototypeState& p,const std::vector<EntityId>& ids,double x,double y,double facing,CrossingRoute route){return PlanOrders(w,p,ids,x,y,facing,route,false);}
void PrepareTerrainBattle(World& w,PrototypeState& p){p.navigation={};PlaceSide(w,false);PlaceSide(p.enemy,true);}
void StepTerrainMovement(World& w,PrototypeState& p,double seconds){TimedNavigation measured;p.navigation.waiting_formations=0;p.navigation.stuck_formations=0;p.navigation.friendly_overlap_pairs=0;NavigateSide(w,p.enemy,p,false,seconds);NavigateSide(p.enemy,w,p,true,seconds);auto overlaps=[&](const World& world,const auto&units){std::uint64_t count=0;for(auto a=units.begin();a!=units.end();++a)if(a->second.alive>0)for(auto b=std::next(a);b!=units.end();++b)if(b->second.alive>0){const auto&f=world.formations.at(a->first);const auto&g=world.formations.at(b->first);if(std::hypot(f.x-g.x,f.y-g.y)<1439)++count;}return count;};p.navigation.friendly_overlap_pairs=overlaps(w,p.player_units)+overlaps(p.enemy,p.enemy_units);p.navigation.peak_friendly_overlap_pairs=std::max(p.navigation.peak_friendly_overlap_pairs,p.navigation.friendly_overlap_pairs);}
}
