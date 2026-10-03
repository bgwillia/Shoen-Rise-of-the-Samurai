#pragma once
// Centimetres, degrees, and speed multipliers. No terrain storage or engine dependency.
namespace domain::suitability {
enum class Water { Dry, MainRiver, Tributary, StandingWater, WetFlat };
enum class Quality { Ideal, Usable, Marginal, Unsuitable };
enum class BuildingResult { Valid, TooSteep, TooUneven, InWater, OutsideBuildableTerrain };
struct MovementRules { double normal, slow, maximum, slow_speed, difficult_speed, wet_speed; };
struct Rules {
 double building_ideal=4, building_max=8, building_marginal=12, building_variation_cm=65;
 double rice_ideal=3, rice_max=5, dry_ideal=5, dry_usable=8, dry_max=12;
 double water_access_cm=6000, wet_bank_cm=2000, wet_height_cm=350, rice_lowland_cm=1200;
 MovementRules infantry{20,35,45,.65,.3,.65}, cavalry{15,25,35,.55,.2,.35};
};
inline bool Standing(Water w) { return w==Water::MainRiver || w==Water::Tributary || w==Water::StandingWater; }
inline BuildingResult Building(double slope,double variation,Water water,bool inside,const Rules& r) {
 if(!inside) return BuildingResult::OutsideBuildableTerrain;
 if(Standing(water)) return BuildingResult::InWater;
 if(slope>r.building_max) return BuildingResult::TooSteep;
 if(variation>r.building_variation_cm) return BuildingResult::TooUneven;
 return BuildingResult::Valid;
}
inline Quality Rice(double slope,bool near_low_water,Water water,bool inside,const Rules& r) {
 if(!inside || Standing(water) || slope>r.rice_max) return Quality::Unsuitable;
 if(slope<=r.rice_ideal && near_low_water) return Quality::Ideal;
 return Quality::Marginal;
}
inline Quality DryFarm(double slope,Water water,bool inside,const Rules& r) {
 if(!inside || Standing(water) || slope>r.dry_max) return Quality::Unsuitable;
 if(water==Water::WetFlat) return Quality::Marginal;
 return slope<=r.dry_ideal ? Quality::Ideal : slope<=r.dry_usable ? Quality::Usable : Quality::Marginal;
}
struct Traversal { Quality quality=Quality::Unsuitable; double speed=0; };
inline Traversal Traverse(double slope,Water water,bool inside,const MovementRules& m,const Rules&) {
 if(!inside || Standing(water) || slope>m.maximum) return {};
 Traversal t=slope<=m.normal ? Traversal{Quality::Ideal,1} : slope<=m.slow ? Traversal{Quality::Usable,m.slow_speed} : Traversal{Quality::Marginal,m.difficult_speed};
 if(water==Water::WetFlat) { t.speed*=m.wet_speed; if(t.quality==Quality::Ideal) t.quality=Quality::Usable; }
 return t;
}
}
