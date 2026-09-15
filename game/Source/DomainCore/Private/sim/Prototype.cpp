#include "domain/Prototype.h"
#include "domain/Battle.h"
#include "domain/Buildings.h"
#include <algorithm>
#include <cmath>
#include <limits>

namespace domain {
namespace {
constexpr double Pi=3.14159265358979323846, Dt=.05;
constexpr std::int64_t StepUs=50'000;
constexpr Quantity StockLimit=1'000'000'000;
Result Fail(const char* message) {return {false,message,0};}
bool Elite(TroopRole role) {return role>=TroopRole::RetainerInfantry && role<=TroopRole::MountedSamurai;}
Quantity Buildings(const World& w,const char* type) {Quantity n=0;for(const auto& [id,b]:w.buildings) if(b.definition_id==type) ++n;return n;}
Quantity Bounded(Quantity n) {return std::clamp<Quantity>(n,0,StockLimit);}
bool GoodConfig(const PrototypeConfig& c) {
 if(c.food_per_farmer<0 || c.food_per_farmer>100 || c.food_per_person<0 || c.food_per_person>100 || c.labor_per_timber<=0 || c.labor_per_iron<=0 || c.labor_per_fuel<=0 || c.smiths_per_equipment<=0 || c.timber_per_equipment<=0 || c.iron_per_equipment<=0 || c.fuel_per_equipment<=0 || c.elite_iron_cost<=0 || c.elite_timber_cost<=0 || c.elite_fuel_cost<=0 || c.ordinary_formation_size<=0 || c.ordinary_formation_size>100 || c.elite_formation_size<=0 || c.elite_formation_size>100 || c.recovery_days<=0 || c.elite_production_period_days<=0 || c.base_food_capacity<0 || c.granary_food_capacity<0) return false;
 for(const auto& t:c.troops) if(!std::isfinite(t.attack_per_soldier) || t.attack_per_soldier<0 || t.attack_per_soldier>10 || !std::isfinite(t.damage_received) || t.damage_received<=0 || t.damage_received>10 || !std::isfinite(t.movement_cm_per_second) || t.movement_cm_per_second<=0 || t.movement_cm_per_second>5000 || !std::isfinite(t.range_cm) || t.range_cm<700 || t.range_cm>10000 || !std::isfinite(t.starting_morale) || t.starting_morale<=20 || t.starting_morale>200) return false;
 return true;
}
void PositionArmy(World& w,bool enemy) {
 std::size_t n=0;for(const auto& [id,f]:w.formations) if(!f.demobilized && !f.service_ids.empty()) ++n;
 const auto columns=std::min<std::size_t>(8,n);std::size_t i=0;
 for(auto& [id,f]:w.formations) if(!f.demobilized && !f.service_ids.empty()) {
  const auto row=i/columns,col=i%columns;
  f.x=(enemy?1:-1)*(2200.0+row*1500.0); f.y=(static_cast<double>(col)-(static_cast<double>(columns)-1)/2)*1400;
  f.facing=enemy?Pi:0;f.target_x=f.x;f.target_y=f.y;f.target_facing=f.facing;f.moving=false;++i;
 }
}
void SnapshotUnits(const World& w,PrototypeState& p,CombatSide side) {
 auto& units=side==CombatSide::Player?p.player_units:p.enemy_units;units.clear();
 for(const auto& [id,f]:w.formations) if(!f.demobilized && !f.service_ids.empty()) {
  CombatUnit u;u.formation_id=id;u.side=side;u.starting=static_cast<Quantity>(f.service_ids.size());u.alive=u.starting;
  u.morale=p.config.troops[static_cast<std::size_t>(f.role)].starting_morale;
  u.service_states.assign(f.service_ids.size(),ServiceStatus::Active);units.emplace(id,std::move(u));
 }
}
void UpdateReport(PrototypeState& p) {
 auto& r=p.battle;r.player_started=r.player_alive=r.player_dead=r.player_wounded=0;r.enemy_started=r.enemy_alive=r.enemy_dead=r.enemy_wounded=0;
 for(const auto& [id,u]:p.player_units) {r.player_started+=u.starting;r.player_alive+=u.alive;r.player_dead+=u.dead;r.player_wounded+=u.wounded;}
 for(const auto& [id,u]:p.enemy_units) {r.enemy_started+=u.starting;r.enemy_alive+=u.alive;r.enemy_dead+=u.dead;r.enemy_wounded+=u.wounded;}
 r.seconds=static_cast<double>(p.battle_steps)*Dt;
}
void DayEconomy(World& w,PrototypeState& p) {
 // Recovery restores the original cohort; the immutable service origin remains unchanged.
 for(auto it=p.recovery.begin();it!=p.recovery.end();) {
  if(it->due_day>w.campaign_day) {++it;continue;}
  auto& c=w.cohorts.at(it->cohort_id);auto& s=w.services.at(it->service_id);
  if(s.status==ServiceStatus::ReturnedWounded && c.recovering_home>0) {--c.recovering_home;++c.available;s.status=ServiceStatus::ReturnedHealthy;}
  it=p.recovery.erase(it);
 }
 p.last_day=ForecastPrototype(w,p);const auto& d=p.last_day;const auto& c=p.config;auto& s=w.settlements.at(1).resources;
 s.food=std::min(d.food_capacity,Bounded(s.food+d.food_produced-d.food_consumed));
 s.timber=Bounded(s.timber+d.timber_produced-d.basic_equipment_produced*c.timber_per_equipment-d.elite_equipment_produced*c.elite_timber_cost);
 s.iron=Bounded(s.iron+d.iron_produced-d.basic_equipment_produced*c.iron_per_equipment-d.elite_equipment_produced*c.elite_iron_cost);
 s.fuel=Bounded(s.fuel+d.fuel_produced-d.basic_equipment_produced*c.fuel_per_equipment-d.elite_equipment_produced*c.elite_fuel_cost);
 s.equipment=Bounded(s.equipment+d.basic_equipment_produced);p.elite_equipment=Bounded(p.elite_equipment+d.elite_equipment_produced);
}
struct Fighter {CombatUnit* unit;Formation* formation;const CombatTuning* tuning;double damage=0,ranged_damage=0;bool flanked=false;};
void MoveTowards(Formation& f,double x,double y,double distance,bool face) {
 auto dx=x-f.x,dy=y-f.y,remaining=std::hypot(dx,dy);if(remaining<.001)return;
 const auto move=std::min(distance,remaining);f.x+=dx/remaining*move;f.y+=dy/remaining*move;if(face)f.facing=std::atan2(dy,dx);
}
void BattleStep(World& w,PrototypeState& p) {
 std::vector<Fighter> fighters;fighters.reserve(p.player_units.size()+p.enemy_units.size());
 for(auto& [id,u]:p.player_units) fighters.push_back({&u,&w.formations.at(id),&p.config.troops[static_cast<std::size_t>(w.formations.at(id).role)]});
 for(auto& [id,u]:p.enemy_units) fighters.push_back({&u,&p.enemy.formations.at(id),&p.config.troops[static_cast<std::size_t>(p.enemy.formations.at(id).role)]});
 for(auto& a:fighters) {
  auto& u=*a.unit;auto& f=*a.formation;u.engaged=false;u.target_formation_id=0;u.ranged_attacking=false;if(u.alive==0)continue;
  Fighter* nearest=nullptr;double best=1e100;
  for(auto& b:fighters) if(u.side!=b.unit->side && b.unit->alive>0 && !b.unit->routed) {const auto d=std::hypot(f.x-b.formation->x,f.y-b.formation->y);if(d<best){best=d;nearest=&b;}}
  if(u.routed) {f.moving=false;f.x+=(u.side==CombatSide::Player?-1:1)*850*Dt;continue;}
  bool moved=false;
  if(f.moving) {
   const auto remaining=std::hypot(f.target_x-f.x,f.target_y-f.y);
   double distance=a.tuning->movement_cm_per_second*(1-u.fatigue*.003)*Dt;
   if(nearest && best<1000 && remaining>.001 && best>.001) {
    const double approaching=((f.target_x-f.x)*(nearest->formation->x-f.x)+(f.target_y-f.y)*(nearest->formation->y-f.y))/(remaining*best);
    // Contact locks forward travel, but a fresh lateral/away order can disengage.
    if(approaching>.5)distance=std::min(distance,std::max(0.0,best-650));
   }
   MoveTowards(f,f.target_x,f.target_y,distance,true);moved=remaining>.001 && distance>.001;
   if(remaining<=a.tuning->movement_cm_per_second*Dt) {f.moving=false;f.facing=f.target_facing;}
  } else if(u.side==CombatSide::Enemy && nearest) {
   f.facing=std::atan2(nearest->formation->y-f.y,nearest->formation->x-f.x);
   if(best>a.tuning->range_cm*.9) {
    const auto distance=std::min(a.tuning->movement_cm_per_second*(1-u.fatigue*.003)*Dt,std::max(0.0,best-650));
    MoveTowards(f,nearest->formation->x,nearest->formation->y,distance,true);moved=distance>.001;
   }
  }
  u.fatigue=std::clamp(u.fatigue+(moved?.25:-.15)*Dt,0.0,100.0);
 }
 // Simultaneous attacks: casualties are applied only after every formation has attacked.
 for(auto& a:fighters) {
  auto& u=*a.unit;auto& f=*a.formation;if(u.alive==0 || u.routed)continue;
  Fighter* target=nullptr;double best=1e100;
  for(auto& b:fighters) if(u.side!=b.unit->side && b.unit->alive>0 && !b.unit->routed) {auto d=std::hypot(f.x-b.formation->x,f.y-b.formation->y);if(d<best){best=d;target=&b;}}
  if(!target || best>a.tuning->range_cm)continue;
  const bool ranged=f.role==TroopRole::Bow && best>700;
  // A forward firing arc makes facing and flanking matter for ranged formations too.
  const auto dx=target->formation->x-f.x,dy=target->formation->y-f.y;
  if(ranged && best>.01 && (dx*std::cos(f.facing)+dy*std::sin(f.facing))/best<.2)continue;
  u.target_formation_id=target->unit->formation_id;u.ranged_attacking=ranged;
  auto& victim=*target->unit;auto& tf=*target->formation;
  const double toward_attacker=best>.01 ? ((f.x-tf.x)*std::cos(tf.facing)+(f.y-tf.y)*std::sin(tf.facing))/best : 1;
  const bool flank=!ranged && toward_attacker<.25;target->flanked|=flank;
  double defense=target->tuning->damage_received+(flank?.75:0);
  double attack=a.tuning->attack_per_soldier;if(f.role==TroopRole::Bow && !ranged)attack*=.5;
  const double damage=u.alive*attack*(1-u.fatigue*.008)*defense*(1+victim.fatigue*.01)*Dt;
  target->damage+=damage;if(ranged){target->ranged_damage+=damage;++p.battle.ranged_attacks;}else{++p.battle.contact_events;u.engaged=true;victim.engaged=true;}
  u.fatigue=std::min(100.0,u.fatigue+(ranged?.2:.9)*Dt);
 }
 std::uint64_t congestion=0;
 for(std::size_t i=0;i<fighters.size();++i)for(std::size_t j=i+1;j<fighters.size();++j)
  if(fighters[i].unit->side==fighters[j].unit->side && fighters[i].unit->alive>0 && fighters[j].unit->alive>0 && std::hypot(fighters[i].formation->x-fighters[j].formation->x,fighters[i].formation->y-fighters[j].formation->y)<650)++congestion;
 p.battle.peak_congestion_pairs=std::max(p.battle.peak_congestion_pairs,congestion);
 for(auto& a:fighters) {
  auto& u=*a.unit;if(u.alive==0)continue;
  u.casualty_fraction+=a.damage;auto losses=std::min(u.alive,static_cast<Quantity>(u.casualty_fraction));u.casualty_fraction-=losses;
  for(Quantity n=0;n<losses;++n) {
   auto index=static_cast<std::size_t>(u.dead+u.wounded);const bool wound=(index%3)==2;
   u.service_states[index]=wound?ServiceStatus::WoundedAway:ServiceStatus::Dead;if(wound)++u.wounded;else++u.dead;--u.alive;
  }
  if(a.damage>0) {
   const auto ranged=static_cast<std::uint64_t>(std::llround(losses*a.ranged_damage/a.damage));
   p.battle.ranged_casualties+=ranged;p.battle.melee_casualties+=static_cast<std::uint64_t>(losses)-ranged;
  }
  u.morale=std::max(0.0,u.morale-losses*140.0/std::max<Quantity>(1,u.starting)-(a.flanked?3.0*Dt:0));
  if(u.morale<20 || u.alive*5<u.starting) {u.routed=true;a.formation->moving=false;}
 }
 ++p.battle_steps;UpdateReport(p);
 bool player=false,enemy=false;for(const auto& [id,u]:p.player_units)player|=u.alive>0&&!u.routed;for(const auto& [id,u]:p.enemy_units)enemy|=u.alive>0&&!u.routed;
 if(!player || !enemy) {p.phase=player?BattlePhase::Victory:BattlePhase::Defeat;p.battle.victory=player;}
}
}
const char* BattlePhaseName(BattlePhase phase) {switch(phase){case BattlePhase::Settlement:return "Settlement";case BattlePhase::Fighting:return "Battle";case BattlePhase::Victory:return "Victory";case BattlePhase::Defeat:return "Defeat";}return "Unknown";}
Result MakePrototype(World& w,PrototypeState& p) {
 World candidate=MakeFoundationWorld();PrototypeState state;state.enabled=true;
 candidate.settlements.at(1).name="Shoen prototype village";
 candidate.cohorts.at(3).available=320;candidate.cohorts.at(3).dependent_or_ineligible=80;
 candidate.cohorts.emplace(5,Cohort{5,1,2,Occupation::GeneralLabor,Skill::Trained,Estate::Ordinary,160});
 candidate.cohorts.emplace(6,Cohort{6,1,2,Occupation::Smithing,Skill::Expert,Estate::Ordinary,40});
 candidate.cohorts.emplace(7,Cohort{7,1,2,Occupation::RetainerService,Skill::Expert,Estate::Warrior,40});
 candidate.initial_population=640;candidate.next_id=8;
 auto& stocks=candidate.settlements.at(1).resources;stocks.seed_grain=0;stocks.food=3000;stocks.timber=400;stocks.iron=160;stocks.fuel=200;stocks.equipment=250;stocks.treasury=500;
 state.elite_equipment=40;
 BuildArea area{1,-6000,-4000,1000,13,9,{}};area.heights_cm.assign(117,0);candidate.build_areas.emplace(1,std::move(area));
 const char* ids[]={"house","farm","granary","smithy","manor","training"};
 const char* names[]={"Village houses","Agricultural fields","Granary","Smithy","Manor","Retainer training"};
 for(int i=0;i<6;++i) {
  BuildingDefinition d;d.id=ids[i];d.display_name=names[i];d.width_cm=1000;d.depth_cm=800;d.height_cm=i==1?100:i==4?650:400;
  state.catalog.emplace(d.id,d);
  PlacementCommand command{candidate.next_transaction_id,d.id,1,2,-3000+(i%3)*2400,-1600+(i/3)*2800,0};
  auto result=PlaceBuilding(candidate,state.catalog,command);if(!result.ok)return Fail("Prototype building setup failed.");
 }
 state.last_day=ForecastPrototype(candidate,state);w=std::move(candidate);p=std::move(state);return {true,{},0};
}
DailyEconomy ForecastPrototype(const World& w,const PrototypeState& p) {
 DailyEconomy d;if(!p.enabled || !GoodConfig(p.config) || !w.settlements.contains(1))return d;
 const auto& c=p.config;const auto& s=w.settlements.at(1).resources;
 for(const auto& [id,cohort]:w.cohorts) switch(cohort.occupation) {
  case Occupation::Agriculture:d.farmers+=cohort.available;break;case Occupation::GeneralLabor:d.laborers+=cohort.available;break;
  case Occupation::Smithing:d.smiths+=cohort.available;break;case Occupation::RetainerService:d.retainers+=cohort.available;break;default:break;
 }
 const auto population=Summarize(w).living;d.housing_capacity=Buildings(w,"house")*800;
 const double housed=population?std::min(1.0,static_cast<double>(d.housing_capacity)/population):1;
 d.food_produced=Buildings(w,"farm")?static_cast<Quantity>(d.farmers*c.food_per_farmer*housed):0;d.food_consumed=population*c.food_per_person;
 d.food_capacity=Bounded(c.base_food_capacity+Buildings(w,"granary")*c.granary_food_capacity);
 d.timber_produced=static_cast<Quantity>(d.laborers/c.labor_per_timber*housed);d.iron_produced=static_cast<Quantity>(d.laborers/c.labor_per_iron*housed);d.fuel_produced=static_cast<Quantity>(d.laborers/c.labor_per_fuel*housed);
 auto timber=s.timber+d.timber_produced,iron=s.iron+d.iron_produced,fuel=s.fuel+d.fuel_produced;
 if(Buildings(w,"smithy")) d.basic_equipment_produced=std::min({d.smiths/c.smiths_per_equipment,timber/c.timber_per_equipment,iron/c.iron_per_equipment,fuel/c.fuel_per_equipment,StockLimit-s.equipment});
 timber-=d.basic_equipment_produced*c.timber_per_equipment;iron-=d.basic_equipment_produced*c.iron_per_equipment;fuel-=d.basic_equipment_produced*c.fuel_per_equipment;
 if(Buildings(w,"smithy") && Buildings(w,"manor") && Buildings(w,"training") && w.campaign_day%c.elite_production_period_days==0)
  d.elite_equipment_produced=std::min({d.smiths/20,timber/c.elite_timber_cost,iron/c.elite_iron_cost,fuel/c.elite_fuel_cost,StockLimit-p.elite_equipment});
 d.food_shortfall=std::max<Quantity>(0,d.food_consumed-s.food-d.food_produced);return d;
}
Result RecruitPrototype(World& w,PrototypeState& p,EntityId cohort,Quantity count,TroopRole role) {
 if(!p.enabled || p.phase!=BattlePhase::Settlement || !GoodConfig(p.config))return Fail("Recruitment requires an active prototype settlement.");
 if(role>TroopRole::MountedSamurai || count<=0 || count>2000)return Fail("Choose a positive recruitment count up to 2000.");
 auto it=w.cohorts.find(cohort);if(it==w.cohorts.end() || it->second.available<count)return Fail("Not enough available workers in this occupation.");
 const bool elite=Elite(role);if(elite && (it->second.occupation!=Occupation::RetainerService || it->second.estate!=Estate::Warrior || !Buildings(w,"manor") || !Buildings(w,"training")))return Fail("Elite troops need warrior retainers, a manor and training ground.");
 if((elite?p.elite_equipment:w.settlements.at(1).resources.equipment)<count)return Fail("Not enough suitable military equipment.");
 World candidate=w;EntityId first=0;const auto size=elite?p.config.elite_formation_size:p.config.ordinary_formation_size;
 for(Quantity remaining=count;remaining>0;remaining-=std::min(size,remaining)) {
  auto r=Mobilize(candidate,cohort,std::min(size,remaining));if(!r)return r;if(!first)first=r.id;auto& f=candidate.formations.at(r.id);f.role=role;f.name=(elite?"Samurai ":role==TroopRole::Bow?"Archers ":"Polearms ")+std::to_string(r.id);
 }
 if(elite)p.elite_equipment-=count;else candidate.settlements.at(1).resources.equipment-=count;
 w=std::move(candidate);return {true,{},first};
}
Result BeginPrototypeBattle(World& w,PrototypeState& p,Quantity enemy_count) {
 if(!p.enabled || p.phase!=BattlePhase::Settlement || !GoodConfig(p.config))return Fail("A prototype battle is already active or tuning is invalid.");
 if(auto valid=ValidateWorld(w);!valid)return valid;
 Quantity soldiers=0;for(const auto& [id,f]:w.formations)if(!f.demobilized)for(auto service:f.service_ids){if(w.services.at(service).status!=ServiceStatus::Active)return Fail("Only healthy equipped formations can enter this battle.");++soldiers;}
 if(!soldiers)return Fail("Recruit an army first.");if(enemy_count==0)enemy_count=soldiers;if(enemy_count<=0 || enemy_count>4000)return Fail("Enemy count must be 1 through 4000.");
 World enemy=MakeFoundationWorld();enemy.initial_population=enemy_count;enemy.cohorts.at(3).available=enemy_count;
 int index=0;for(Quantity remaining=enemy_count;remaining>0;remaining-=std::min<Quantity>(50,remaining)) {auto r=Mobilize(enemy,3,std::min<Quantity>(50,remaining));if(!r)return r;enemy.formations.at(r.id).role=(++index%4==0)?TroopRole::Bow:TroopRole::Polearm;}
 p.enemy=std::move(enemy);PositionArmy(w,false);PositionArmy(p.enemy,true);p.phase=BattlePhase::Fighting;p.battle={};p.battle_steps=0;p.battle_substep_microseconds=0;
 SnapshotUnits(w,p,CombatSide::Player);SnapshotUnits(p.enemy,p,CombatSide::Enemy);UpdateReport(p);return {true,{},0};
}
Result MakeCombatFixture(World& w,PrototypeState& p,Quantity count) {
 if(count<50 || count>4000 || count%50)return Fail("Combat fixture needs a multiple of 50 from 50 through 4000 per side.");
 World candidate;PrototypeState state;if(auto r=MakePrototype(candidate,state);!r)return r;
 candidate.cohorts.at(3).available=count;candidate.cohorts.at(3).dependent_or_ineligible=0;candidate.initial_population=count+240;candidate.settlements.at(1).resources.equipment=count;
 int i=0;for(Quantity n=0;n<count;n+=50)if(auto r=RecruitPrototype(candidate,state,3,50,(++i%4==0)?TroopRole::Bow:TroopRole::Polearm);!r)return r;
 if(auto r=BeginPrototypeBattle(candidate,state,count);!r)return r;
 // Scale fixture is a real attacking army; ordinary player battles leave orders to the player.
 for(auto& [id,f]:candidate.formations)if(f.role!=TroopRole::Bow){f.target_x=1800;f.target_y=f.y;f.target_facing=0;f.moving=true;}
 w=std::move(candidate);p=std::move(state);return {true,{},0};
}
const CombatUnit* LookupCombatUnit(const PrototypeState& p,CombatSide side,EntityId id) {const auto& units=side==CombatSide::Player?p.player_units:p.enemy_units;auto it=units.find(id);return it==units.end()?nullptr:&it->second;}
Result IssuePrototypeOrder(World& w,PrototypeState& p,const std::vector<EntityId>& ids,double x,double y,double facing) {
 if(!p.enabled || p.phase!=BattlePhase::Fighting)return Fail("Movement orders require a fighting battle.");
 for(auto id:ids){auto it=p.player_units.find(id);if(it==p.player_units.end() || it->second.routed || it->second.alive==0)return Fail("Dead or routing formations cannot take orders.");}
 auto r=IssueMove(w,ids,x,y,facing);if(r)++p.battle.commands;return r;
}
Result AdvancePrototype(World& w,PrototypeState& p,std::int64_t us) {
 if(!p.enabled || !GoodConfig(p.config) || us<0 || us>600'000'000)return Fail("Prototype elapsed time or tuning is invalid; maximum batch is ten minutes.");
 if(p.phase==BattlePhase::Fighting) {
  if(w.speed==0)return {true,{},0};
  const auto total=p.battle_substep_microseconds+us;const auto steps=total/StepUs;p.battle_substep_microseconds=total%StepUs;
  for(std::int64_t i=0;i<steps && p.phase==BattlePhase::Fighting;++i)BattleStep(w,p);
  // Finished battles have no pending fractional combat time, independent of input chunking.
  if(p.phase!=BattlePhase::Fighting)p.battle_substep_microseconds=0;
  return {true,{},static_cast<EntityId>(steps)};
 }
 if(p.phase!=BattlePhase::Settlement)return {true,{},0};
 if(w.speed!=0 && w.speed!=1 && w.speed!=3 && w.speed!=5 && w.speed!=10)return Fail("Invalid campaign speed.");
 const auto total=w.subday_microseconds+us*w.speed;const auto days=total/MicrosecondsPerDay;w.subday_microseconds=total%MicrosecondsPerDay;
 for(Day i=0;i<days;++i){AdvanceOneDay(w);DayEconomy(w,p);}return {true,{},static_cast<EntityId>(days)};
}
Result ReturnFromPrototypeBattle(World& w,PrototypeState& p,bool retreat) {
 if(!p.enabled || p.phase==BattlePhase::Settlement)return Fail("There is no battle to return from.");
 if(p.phase==BattlePhase::Fighting && !retreat)return Fail("The battle is still fighting; use retreat to return now.");
 World candidate=w;PrototypeState state=p;auto recovery=p.recovery;Quantity elite_refund=0;
 for(const auto& [id,u]:p.player_units) {
  auto it=candidate.formations.find(id);if(it==candidate.formations.end() || it->second.service_ids.size()!=u.service_states.size())return Fail("Battle formation membership changed before return.");
  Outcome outcome;outcome.transaction_id=candidate.next_transaction_id;outcome.formation_id=id;outcome.expected_revision=candidate.revision;
  Quantity survivors=0;for(std::size_t i=0;i<u.service_states.size();++i) {
   const auto service=it->second.service_ids[i];const auto status=u.service_states[i];outcome.dispositions.push_back({service,status});
   if(status==ServiceStatus::Active || status==ServiceStatus::WoundedAway)++survivors;
   if(status==ServiceStatus::WoundedAway)recovery.push_back({service,candidate.services.at(service).origin.cohort_id,candidate.campaign_day+1+p.config.recovery_days});
  }
  if(Elite(it->second.role))elite_refund+=survivors;else candidate.settlements.at(1).resources.equipment=Bounded(candidate.settlements.at(1).resources.equipment+survivors);
  if(auto r=ApplyOutcome(candidate,outcome);!r)return r;if(auto r=Demobilize(candidate,id);!r)return r;
 }
 state.elite_equipment=Bounded(state.elite_equipment+elite_refund);state.recovery=std::move(recovery);state.last_outcome=state.battle;state.last_outcome.retreated=retreat;state.phase=BattlePhase::Settlement;
 // One operational campaign day per resolved battle, inside the same candidate commit.
 AdvanceOneDay(candidate);DayEconomy(candidate,state);
 if(auto r=ValidateWorld(candidate);!r)return r;
 w=std::move(candidate);p=std::move(state);return {true,{},0};
}
}
