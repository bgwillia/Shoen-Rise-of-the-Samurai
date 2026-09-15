#include "domain/Prototype.h"
#include <chrono>
#include <cmath>
#include <functional>
#include <iostream>
#include <stdexcept>
using namespace domain;
#define REQUIRE(x) do { if(!(x)) throw std::runtime_error(#x); } while(false)
void Economy() {
 World w; PrototypeState p; REQUIRE(MakePrototype(w,p)); REQUIRE(ValidateWorld(w));
 REQUIRE(Summarize(w).total==640); REQUIRE(w.buildings.size()==6); REQUIRE(p.catalog.size()==6);
 auto before=ForecastPrototype(w,p); REQUIRE(before.farmers==320); REQUIRE(before.food_produced==960); REQUIRE(before.food_consumed==640);
 REQUIRE(RecruitPrototype(w,p,3,100,TroopRole::Polearm));
 auto after=ForecastPrototype(w,p); REQUIRE(after.farmers==220); REQUIRE(after.food_produced==660); REQUIRE(Summarize(w).away==100);
 const auto food=w.settlements.at(1).resources.food;
 REQUIRE(AdvancePrototype(w,p,MicrosecondsPerDay)); REQUIRE(w.campaign_day==1);
 REQUIRE(w.settlements.at(1).resources.food==food+20); REQUIRE(p.last_day.basic_equipment_produced>0);
 REQUIRE(ValidateWorld(w));
 const auto equipment=ForecastPrototype(w,p).basic_equipment_produced;
 REQUIRE(RecruitPrototype(w,p,6,20,TroopRole::Polearm));
 REQUIRE(ForecastPrototype(w,p).smiths==20);
 REQUIRE(ForecastPrototype(w,p).basic_equipment_produced<equipment);
 auto without=w;for(auto it=without.buildings.begin();it!=without.buildings.end();) {
  if(it->second.definition_id=="farm" || it->second.definition_id=="smithy")it=without.buildings.erase(it);else ++it;
 }
 REQUIRE(ForecastPrototype(without,p).food_produced==0);
 REQUIRE(ForecastPrototype(without,p).basic_equipment_produced==0);
 REQUIRE(AdvancePrototype(without,p,MicrosecondsPerDay*7));
 REQUIRE(without.settlements.at(1).resources.food==0);
 REQUIRE(ValidateWorld(without));
}
void Recruitment() {
 World w; PrototypeState p; REQUIRE(MakePrototype(w,p)); auto original=w; auto old=p;
 REQUIRE(!RecruitPrototype(w,p,3,20,TroopRole::SamuraiFoot)); REQUIRE(w==original && p==old);
 w.settlements.at(1).resources.equipment=0; original=w;
 REQUIRE(!RecruitPrototype(w,p,3,50,TroopRole::Polearm)); REQUIRE(w==original);
 auto gear=p.elite_equipment; REQUIRE(RecruitPrototype(w,p,7,20,TroopRole::SamuraiFoot)); REQUIRE(p.elite_equipment==gear-20);
 const auto& f=w.formations.begin()->second; REQUIRE(f.role==TroopRole::SamuraiFoot);
 for(auto id:f.service_ids) {const auto& o=w.services.at(id).origin; REQUIRE(o.cohort_id==7 && o.occupation==Occupation::RetainerService && o.estate==Estate::Warrior && o.district_id==2);}
 REQUIRE(ValidateWorld(w));
}
void DeterministicBattle() {
 World a,b; PrototypeState p,q; REQUIRE(MakeCombatFixture(a,p,500)); b=a;q=p;
 REQUIRE(SetSpeed(a,0));const auto paused=a;const auto paused_battle=p;
 REQUIRE(AdvancePrototype(a,p,20'000'000));REQUIRE(a==paused && p==paused_battle);
 REQUIRE(SetSpeed(a,1));
 const auto day=a.campaign_day;
 REQUIRE(AdvancePrototype(a,p,20'000'000));
 for(int i=0;i<400;++i) REQUIRE(AdvancePrototype(b,q,50'000));
 REQUIRE(a==b && p==q); REQUIRE(a.campaign_day==day);
 REQUIRE(p.battle.player_dead+p.battle.enemy_dead+p.battle.player_wounded+p.battle.enemy_wounded>0);
 REQUIRE(LookupCombatUnit(p,CombatSide::Player,p.player_units.begin()->first));
 REQUIRE(ValidateWorld(a)); REQUIRE(ValidateWorld(p.enemy));
}
void ReturnRecovery() {
 World w; PrototypeState p; REQUIRE(MakePrototype(w,p)); REQUIRE(RecruitPrototype(w,p,3,100,TroopRole::Polearm));
 REQUIRE(BeginPrototypeBattle(w,p,100)); REQUIRE(AdvancePrototype(w,p,30'000'000));
 REQUIRE(p.battle.player_dead>0 && p.battle.player_wounded>0);
 const auto dead=p.battle.player_dead, wounded=p.battle.player_wounded;
 const auto before_return_day=w.campaign_day;
 REQUIRE(ReturnFromPrototypeBattle(w,p,true)); REQUIRE(p.phase==BattlePhase::Settlement);
 REQUIRE(w.campaign_day==before_return_day+1);
 REQUIRE(w.settlements.at(1).resources.equipment==250-dead+p.last_day.basic_equipment_produced);
 auto summary=Summarize(w); REQUIRE(summary.dead==dead && summary.recovering==wounded && summary.away==0 && summary.total==640);
 REQUIRE(ForecastPrototype(w,p).farmers==320-dead-wounded);
 const auto once=w; REQUIRE(!ReturnFromPrototypeBattle(w,p,true)); REQUIRE(w==once);
 REQUIRE(SetSpeed(w,10)); REQUIRE(AdvancePrototype(w,p,MicrosecondsPerDay*p.config.recovery_days/10));
 summary=Summarize(w); REQUIRE(summary.recovering==0 && summary.dead==dead && summary.total==640);
 REQUIRE(ForecastPrototype(w,p).farmers==320-dead); REQUIRE(p.recovery.empty()); REQUIRE(ValidateWorld(w));
 for(const auto& [id,s]:w.services) REQUIRE(s.origin.cohort_id==3 && s.origin.occupation==Occupation::Agriculture);
}
Quantity Duel(bool Exhausted,bool Flanked) {
 World w; PrototypeState p; REQUIRE(MakePrototype(w,p)); REQUIRE(RecruitPrototype(w,p,7,20,TroopRole::SamuraiFoot)); REQUIRE(BeginPrototypeBattle(w,p,50));
 auto& f=w.formations.begin()->second;auto& e=p.enemy.formations.begin()->second;
 f.x=0;f.y=0;f.facing=Flanked?3.141592653589793:0;f.moving=false;
 e.x=650;e.y=0;e.facing=3.141592653589793;e.moving=false;
 if(Exhausted) p.player_units.begin()->second.fatigue=100;
 REQUIRE(AdvancePrototype(w,p,25'000'000));
 return p.battle.enemy_dead+p.battle.enemy_wounded-p.battle.player_dead-p.battle.player_wounded;
}
void EliteAndCounters() {
 auto strong=Duel(false,false); REQUIRE(strong>10); REQUIRE(Duel(true,false)<strong); REQUIRE(Duel(false,true)<strong);
 World w;PrototypeState p;REQUIRE(MakePrototype(w,p));REQUIRE(RecruitPrototype(w,p,7,20,TroopRole::SamuraiFoot));
 REQUIRE(BeginPrototypeBattle(w,p,200));REQUIRE(AdvancePrototype(w,p,80'000'000));REQUIRE(p.phase==BattlePhase::Defeat);
}
void RangedAndOrders() {
 World w;PrototypeState p;REQUIRE(MakePrototype(w,p)); REQUIRE(RecruitPrototype(w,p,3,50,TroopRole::Bow)); REQUIRE(BeginPrototypeBattle(w,p,50));
 REQUIRE(IssuePrototypeOrder(w,p,{w.formations.begin()->first},-2200,0,0)); REQUIRE(AdvancePrototype(w,p,1'000'000));
 REQUIRE(p.battle.enemy_dead+p.battle.enemy_wounded>0); REQUIRE(p.battle.player_dead+p.battle.player_wounded==0);
 const auto* bow=LookupCombatUnit(p,CombatSide::Player,w.formations.begin()->first);
 REQUIRE(bow && bow->ranged_attacking && bow->target_formation_id==p.enemy.formations.begin()->first);
 auto& bow_pose=w.formations.begin()->second;bow_pose.x=-20000;bow_pose.moving=false;
 REQUIRE(AdvancePrototype(w,p,50'000));
 REQUIRE(!bow->ranged_attacking && bow->target_formation_id==0);
 auto original=w; REQUIRE(!IssuePrototypeOrder(w,p,{9999999},0,0,0)); REQUIRE(w==original);
 World contact;PrototypeState fight;REQUIRE(MakeCombatFixture(contact,fight,50));
 auto& friendly=contact.formations.begin()->second;auto& hostile=fight.enemy.formations.begin()->second;
 friendly.x=-400;friendly.y=0;friendly.target_x=400;friendly.target_y=0;friendly.moving=true;
 hostile.x=400;hostile.y=0;
 REQUIRE(AdvancePrototype(contact,fight,2'000'000));
 REQUIRE(friendly.x<hostile.x && std::hypot(friendly.x-hostile.x,friendly.y-hostile.y)>=649.99);
 REQUIRE(IssuePrototypeOrder(contact,fight,{friendly.id},-2400,0,3.141592653589793));
 const auto old_x=friendly.x;REQUIRE(AdvancePrototype(contact,fight,500'000));REQUIRE(friendly.x<old_x);
}
void ScaleSmoke() {
 for(Quantity n:{500,1000,2000}) {World w;PrototypeState p; REQUIRE(MakeCombatFixture(w,p,n));
  auto start=std::chrono::steady_clock::now(); REQUIRE(AdvancePrototype(w,p,30'000'000));
  auto ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
  REQUIRE(p.battle.player_started==n && p.battle.enemy_started==n); REQUIRE(p.battle.player_dead+p.battle.enemy_dead>0);
  REQUIRE(p.battle.player_alive+p.battle.player_dead+p.battle.player_wounded==n);
  REQUIRE(p.battle.enemy_alive+p.battle.enemy_dead+p.battle.enemy_wounded==n);
  REQUIRE(ValidateWorld(w)); std::cout<<"COMBAT "<<n<<"v"<<n<<" 30s simulation "<<ms<<"ms, mean per 20Hz step "<<ms/600<<"ms\n";
 }
}
int main(){int failed=0;for(auto [name,test]:std::vector<std::pair<const char*,std::function<void()>>>{{"daily economy and worker removal",Economy},{"recruitment gear estate and origins",Recruitment},{"deterministic combat and frozen campaign",DeterministicBattle},{"return exactly once and recovery",ReturnRecovery},{"elite strength and counters",EliteAndCounters},{"ranged damage and real orders",RangedAndOrders},{"actual combat scale",ScaleSmoke}}){try{test();std::cout<<"PASS "<<name<<'\n';}catch(const std::exception& e){++failed;std::cout<<"FAIL "<<name<<": "<<e.what()<<'\n';}}return failed?1:0;}
