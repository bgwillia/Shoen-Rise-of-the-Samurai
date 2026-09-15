#include "domain/Buildings.h"
#include <algorithm>
#include <cmath>
#include <limits>
#include <set>

namespace domain {
namespace {
constexpr double CoordinateLimit=1e9;
constexpr std::int32_t DimensionLimit=1'000'000;
constexpr double Pi=3.14159265358979323846;
using Rectangle=std::array<Point2,4>;
struct Triangle {Point3 a,b,c;};
Result Invalid(const char* error) {return {false,error,0};}
PlacementResult Rejected(PlacementCode code) {return {false,code,0,0};}
bool Coordinate(double n) {return std::isfinite(n) && std::abs(n)<=CoordinateLimit;}
bool GoodString(const std::string& s,std::size_t limit=256) {return !s.empty() && s.size()<=limit && s.find('\0')==std::string::npos;}
bool GoodDefinition(const BuildingDefinition& d) {
    return GoodString(d.id,64) && GoodString(d.display_name) && d.version>0 && d.width_cm>0 && d.width_cm<=DimensionLimit && d.depth_cm>0 && d.depth_cm<=DimensionLimit && d.height_cm>0 && d.height_cm<=DimensionLimit && d.rotation_step_degrees>0 && d.rotation_step_degrees<=360 && d.max_height_variation_cm>=0 && d.max_height_variation_cm<=DimensionLimit && d.max_slope_permille>=0 && d.max_slope_permille<=DimensionLimit && d.timber_cost>=0 && d.timber_cost<=1'000'000'000 && d.treasury_cost>=0 && d.treasury_cost<=1'000'000'000;
}
bool GoodArea(const BuildArea& a) {
    const auto count=static_cast<std::uint64_t>(a.columns)*a.rows;
    if(a.settlement_id==0 || a.columns<2 || a.rows<2 || count>MaxTerrainVertices || count!=a.heights_cm.size() || a.cell_size_cm<=0 || a.cell_size_cm>DimensionLimit || !Coordinate(a.origin_x_cm) || !Coordinate(a.origin_y_cm)) return false;
    if(!Coordinate(static_cast<double>(a.origin_x_cm)+static_cast<double>(a.columns-1)*a.cell_size_cm) || !Coordinate(static_cast<double>(a.origin_y_cm)+static_cast<double>(a.rows-1)*a.cell_size_cm)) return false;
    for(auto height:a.heights_cm) if(!Coordinate(height)) return false;
    return true;
}
bool GoodCommand(const World& w,const PlacementCommand& c) {
    if(!GoodString(c.definition_id,64) || !Coordinate(c.x_cm) || !Coordinate(c.y_cm) || c.yaw_degrees<0 || c.yaw_degrees>=360 || !w.settlements.contains(c.settlement_id)) return false;
    auto d=w.districts.find(c.district_id);
    return c.district_id==0 || (d!=w.districts.end() && d->second.settlement_id==c.settlement_id);
}
Point3 Vertex(const BuildArea& a,std::uint32_t x,std::uint32_t y) {
    return {static_cast<double>(a.origin_x_cm)+static_cast<double>(x)*a.cell_size_cm,static_cast<double>(a.origin_y_cm)+static_cast<double>(y)*a.cell_size_cm,static_cast<double>(a.heights_cm[static_cast<std::size_t>(y)*a.columns+x])};
}
std::array<Triangle,2> CellTriangles(const BuildArea& a,std::uint32_t x,std::uint32_t y) {
    auto p00=Vertex(a,x,y),p10=Vertex(a,x+1,y),p11=Vertex(a,x+1,y+1),p01=Vertex(a,x,y+1);
    return {{{p00,p10,p11},{p00,p11,p01}}};
}
double Cross(Point2 a,Point2 b,Point2 p) {return (b.x-a.x)*(p.y-a.y)-(b.y-a.y)*(p.x-a.x);}
Point2 XY(Point3 p) {return {p.x,p.y};}
Point3 Sub(Point3 a,Point3 b) {return {a.x-b.x,a.y-b.y,a.z-b.z};}
Point3 Cross3(Point3 a,Point3 b) {return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
double Dot(Point3 a,Point3 b) {return a.x*b.x+a.y*b.y+a.z*b.z;}
struct Plane {double dx,dy;};
Plane Gradient(const Triangle& t) {
    const auto u=Sub(t.b,t.a),v=Sub(t.c,t.a); const auto denominator=u.x*v.y-u.y*v.x;
    return {(u.z*v.y-v.z*u.y)/denominator,(u.x*v.z-v.x*u.z)/denominator};
}
double TriangleHeight(const Triangle& t,Point2 p) {auto g=Gradient(t); return t.a.z+g.dx*(p.x-t.a.x)+g.dy*(p.y-t.a.y);}
bool InsideArea(const BuildArea& a,const Rectangle& corners) {
    double right=static_cast<double>(a.origin_x_cm)+static_cast<double>(a.columns-1)*a.cell_size_cm;
    double top=static_cast<double>(a.origin_y_cm)+static_cast<double>(a.rows-1)*a.cell_size_cm;
    for(auto p:corners) if(p.x<a.origin_x_cm-PlacementToleranceCm || p.y<a.origin_y_cm-PlacementToleranceCm || p.x>right+PlacementToleranceCm || p.y>top+PlacementToleranceCm) return false;
    return true;
}
bool Overlaps(const Rectangle& a,const Rectangle& b) {
    for(const auto* rectangle:{&a,&b}) for(std::size_t i=0;i<2;++i) {
        auto p=(*rectangle)[i],q=(*rectangle)[i+1]; double nx=-(q.y-p.y),ny=q.x-p.x; double length=std::hypot(nx,ny); nx/=length; ny/=length;
        double amin=std::numeric_limits<double>::infinity(),amax=-amin,bmin=amin,bmax=-amin;
        for(auto v:a) {double d=v.x*nx+v.y*ny; amin=std::min(amin,d); amax=std::max(amax,d);}
        for(auto v:b) {double d=v.x*nx+v.y*ny; bmin=std::min(bmin,d); bmax=std::max(bmax,d);}
        if(amax<=bmin+PlacementToleranceCm || bmax<=amin+PlacementToleranceCm) return false;
    }
    return true;
}
std::vector<Point2> ClipToTriangle(const Rectangle& corners,const Triangle& t) {
    std::vector<Point2> polygon(corners.begin(),corners.end()); const std::array<Point2,3> vertices={XY(t.a),XY(t.b),XY(t.c)};
    for(std::size_t edge=0;edge<3 && !polygon.empty();++edge) {
        auto a=vertices[edge],b=vertices[(edge+1)%3]; std::vector<Point2> clipped;
        auto previous=polygon.back(); auto previous_distance=Cross(a,b,previous);
        for(auto current:polygon) {
            auto distance=Cross(a,b,current); bool inside=distance>=0,previous_inside=previous_distance>=0;
            if(inside!=previous_inside) {double alpha=previous_distance/(previous_distance-distance); clipped.push_back({previous.x+alpha*(current.x-previous.x),previous.y+alpha*(current.y-previous.y)});}
            if(inside) clipped.push_back(current);
            previous=current; previous_distance=distance;
        }
        polygon=std::move(clipped);
    }
    return polygon;
}
bool TerrainFits(const BuildArea& a,const Rectangle& corners,std::int32_t max_height_variation_cm,std::int32_t max_slope_permille) {
    double left=corners[0].x,right=left,bottom=corners[0].y,top=bottom;
    for(auto p:corners) {left=std::min(left,p.x);right=std::max(right,p.x);bottom=std::min(bottom,p.y);top=std::max(top,p.y);}
    auto cell=[](double value,std::int32_t origin,std::int32_t size,std::uint32_t count) {return static_cast<std::uint32_t>(std::clamp(std::floor((value-origin)/size),0.0,static_cast<double>(count-2)));};
    auto x0=cell(left,a.origin_x_cm,a.cell_size_cm,a.columns),x1=cell(right,a.origin_x_cm,a.cell_size_cm,a.columns);
    auto y0=cell(bottom,a.origin_y_cm,a.cell_size_cm,a.rows),y1=cell(top,a.origin_y_cm,a.cell_size_cm,a.rows);
    double minimum=std::numeric_limits<double>::infinity(),maximum=-minimum;
    for(auto y=y0;y<=y1;++y) for(auto x=x0;x<=x1;++x) for(auto t:CellTriangles(a,x,y)) {
        auto polygon=ClipToTriangle(corners,t); if(polygon.size()<3) continue;
        double twice_area=0; for(std::size_t i=1;i+1<polygon.size();++i) twice_area+=Cross(polygon[0],polygon[i],polygon[i+1]);
        if(std::abs(twice_area)<=1e-10) continue;
        auto g=Gradient(t); if(std::hypot(g.dx,g.dy)*1000>max_slope_permille+PlacementToleranceCm) return false;
        for(auto point:polygon) {double height=TriangleHeight(t,point); minimum=std::min(minimum,height);maximum=std::max(maximum,height);}
    }
    return std::isfinite(minimum) && maximum-minimum<=max_height_variation_cm+PlacementToleranceCm;
}
bool SameCommand(const Building& b,const PlacementCommand& c) {
    return b.definition_id==c.definition_id && b.settlement_id==c.settlement_id && b.district_id==c.district_id && b.x_cm==c.x_cm && b.y_cm==c.y_cm && b.yaw_degrees==c.yaw_degrees;
}
}
const char* PlacementReason(PlacementCode code) {
    switch(code) {
    case PlacementCode::Valid:return "Valid placement";
    case PlacementCode::AlreadyApplied:return "Placement already completed";
    case PlacementCode::UnknownDefinition:return "Unknown building definition";
    case PlacementCode::InvalidCommand:return "Invalid placement command or definition";
    case PlacementCode::InvalidWorld:return "Invalid settlement state";
    case PlacementCode::NoBuildArea:return "Settlement has no buildable area";
    case PlacementCode::OverlapsBuilding:return "Overlaps an existing building";
    case PlacementCode::OutsideBuildArea:return "Footprint extends outside the buildable area";
    case PlacementCode::TerrainTooSteep:return "Ground slope or height variation is too large";
    case PlacementCode::InsufficientResources:return "Insufficient timber or treasury";
    case PlacementCode::TransactionConflict:return "Transaction ID was already used for another command";
    case PlacementCode::CapacityExceeded:return "Building, transaction or ID capacity reached";
    } return "Unknown placement result";
}
std::array<Point2,4> FootprintCorners(std::int32_t x,std::int32_t y,std::int32_t width,std::int32_t depth,std::int32_t yaw) {
    const double c=std::cos(yaw*Pi/180.0),s=std::sin(yaw*Pi/180.0),hx=width/2.0,hy=depth/2.0;
    Rectangle result={Point2{-hx,-hy},Point2{hx,-hy},Point2{hx,hy},Point2{-hx,hy}};
    for(auto& p:result) p={x+c*p.x-s*p.y,y+s*p.x+c*p.y}; return result;
}
Result ValidateBuildingCatalog(const BuildingCatalog& catalog) {
    if(catalog.empty() || catalog.size()>256) return Invalid("Building catalog must contain 1 through 256 definitions.");
    for(const auto& [key,d]:catalog) if(key!=d.id || !GoodDefinition(d)) return Invalid("Building definition has invalid identity, dimensions, rotation, terrain tolerance or costs.");
    return {true,{},0};
}
double TerrainHeightAt(const BuildArea& a,double x,double y) {
    const double nan=std::numeric_limits<double>::quiet_NaN(); if(!GoodArea(a) || !std::isfinite(x) || !std::isfinite(y)) return nan;
    double fx=(x-a.origin_x_cm)/a.cell_size_cm,fy=(y-a.origin_y_cm)/a.cell_size_cm;
    if(fx<0 || fy<0 || fx>a.columns-1 || fy>a.rows-1) return nan;
    auto ix=std::min(static_cast<std::uint32_t>(std::floor(fx)),a.columns-2),iy=std::min(static_cast<std::uint32_t>(std::floor(fy)),a.rows-2);
    const auto triangles=CellTriangles(a,ix,iy); return TriangleHeight(triangles[(fx-ix)>=(fy-iy)?0:1],{x,y});
}
bool RaycastBuildArea(const BuildArea& a,Point3 origin,Point3 direction,Point3& hit) {
    if(!GoodArea(a) || !Coordinate(origin.x) || !Coordinate(origin.y) || !Coordinate(origin.z)) return false;
    double length=std::hypot(direction.x,direction.y,direction.z); if(!std::isfinite(length) || length<=1e-12) return false;
    direction={direction.x/length,direction.y/length,direction.z/length}; double nearest=std::numeric_limits<double>::infinity(); Point3 result;
    for(std::uint32_t y=0;y<a.rows-1;++y) for(std::uint32_t x=0;x<a.columns-1;++x) for(const auto& t:CellTriangles(a,x,y)) {
        auto edge1=Sub(t.b,t.a),edge2=Sub(t.c,t.a),p=Cross3(direction,edge2); double determinant=Dot(edge1,p);
        if(std::abs(determinant)<1e-10) continue;
        double inverse=1/determinant; auto offset=Sub(origin,t.a); double u=Dot(offset,p)*inverse; if(u<-1e-10 || u>1+1e-10) continue;
        auto q=Cross3(offset,edge1); double v=Dot(direction,q)*inverse; if(v<-1e-10 || u+v>1+1e-10) continue;
        double distance=Dot(edge2,q)*inverse; if(distance<-1e-8 || distance>=nearest) continue;
        distance=std::max(0.0,distance); nearest=distance; result={origin.x+direction.x*distance,origin.y+direction.y*distance,origin.z+direction.z*distance};
    }
    if(!std::isfinite(nearest)) return false; hit=result; return true;
}
Result ValidateBuildingState(const World& w) {
    if(w.buildings.size()>MaxBuildings || w.build_areas.size()>MaxBuildAreas) return Invalid("Building or build-area registry exceeds its limit.");
    for(const auto& [id,a]:w.build_areas) if(id!=a.settlement_id || !w.settlements.contains(id) || !GoodArea(a)) return Invalid("Build area has invalid dimensions, heights or settlement reference.");
    std::set<EntityId> transactions; std::vector<Rectangle> footprints;
    for(const auto& [id,b]:w.buildings) {
        if(id==0 || id!=b.id || id>=w.next_id || w.settlements.contains(id) || w.districts.contains(id) || w.cohorts.contains(id) || w.services.contains(id) || w.formations.contains(id) || w.generals.contains(id)) return Invalid("Building ID conflicts with the global entity registry.");
        auto area=w.build_areas.find(b.settlement_id); PlacementCommand command{b.placement_transaction_id,b.definition_id,b.settlement_id,b.district_id,b.x_cm,b.y_cm,b.yaw_degrees};
        if(area==w.build_areas.end() || !GoodCommand(w,command) || b.definition_version==0 || b.state!=ConstructionState::Completed || b.width_cm<=0 || b.width_cm>DimensionLimit || b.depth_cm<=0 || b.depth_cm>DimensionLimit || b.height_cm<=0 || b.height_cm>DimensionLimit || b.max_height_variation_cm<0 || b.max_height_variation_cm>DimensionLimit || b.max_slope_permille<0 || b.max_slope_permille>DimensionLimit || !Coordinate(b.z_cm)) return Invalid("Building has invalid definition, dimensions, construction state or location.");
        if(b.placement_transaction_id==0 || b.placement_transaction_id>=w.next_transaction_id || !w.applied_transaction_ids.contains(b.placement_transaction_id) || !transactions.insert(b.placement_transaction_id).second) return Invalid("Building placement transaction is absent or duplicated.");
        auto corners=FootprintCorners(b.x_cm,b.y_cm,b.width_cm,b.depth_cm,b.yaw_degrees);
        if(!InsideArea(area->second,corners)) return Invalid("Building footprint extends outside its saved build area.");
        if(!TerrainFits(area->second,corners,b.max_height_variation_cm,b.max_slope_permille)) return Invalid("Building footprint exceeds its frozen terrain limits.");
        double ground=TerrainHeightAt(area->second,b.x_cm,b.y_cm); if(!std::isfinite(ground) || std::llround(ground)!=b.z_cm) return Invalid("Building elevation differs from its saved terrain.");
        for(const auto& previous:footprints) if(Overlaps(corners,previous)) return Invalid("Saved building footprints overlap.");
        footprints.push_back(corners);
    }
    return {true,{},0};
}
PlacementResult ValidatePlacementGeometry(const World& w,const BuildingDefinition& d,const PlacementCommand& c) {
    if(!GoodDefinition(d) || d.id!=c.definition_id || !GoodCommand(w,c)) return Rejected(PlacementCode::InvalidCommand);
    auto area=w.build_areas.find(c.settlement_id); if(area==w.build_areas.end()) return Rejected(PlacementCode::NoBuildArea);
    if(!GoodArea(area->second)) return Rejected(PlacementCode::InvalidWorld);
    const double height=TerrainHeightAt(area->second,c.x_cm,c.y_cm);
    const auto ground=std::isfinite(height)?static_cast<std::int32_t>(std::llround(height)):0;
    auto rejected=[ground](PlacementCode code) {return PlacementResult{false,code,0,ground};};
    const auto corners=FootprintCorners(c.x_cm,c.y_cm,d.width_cm,d.depth_cm,c.yaw_degrees);
    if(!InsideArea(area->second,corners) || !std::isfinite(height)) return rejected(PlacementCode::OutsideBuildArea);
    for(const auto& [id,b]:w.buildings) if(Overlaps(corners,FootprintCorners(b.x_cm,b.y_cm,b.width_cm,b.depth_cm,b.yaw_degrees))) return rejected(PlacementCode::OverlapsBuilding);
    if(!TerrainFits(area->second,corners,d.max_height_variation_cm,d.max_slope_permille)) return rejected(PlacementCode::TerrainTooSteep);
    return {true,PlacementCode::Valid,0,ground};
}
PlacementResult EvaluatePlacement(const World& w,const BuildingCatalog& catalog,const PlacementCommand& c) {
    if(!ValidateWorld(w).ok) return Rejected(PlacementCode::InvalidWorld);
    auto definition=catalog.find(c.definition_id); if(definition==catalog.end()) return Rejected(PlacementCode::UnknownDefinition);
    if(!ValidateBuildingCatalog(catalog).ok) return Rejected(PlacementCode::InvalidCommand);
    auto geometry=ValidatePlacementGeometry(w,definition->second,c); if(!geometry.ok) return geometry;
    const auto& stock=w.settlements.at(c.settlement_id).resources; const auto& d=definition->second;
    if(stock.timber<d.timber_cost || stock.treasury<d.treasury_cost) return {false,PlacementCode::InsufficientResources,0,geometry.ground_z_cm};
    if(w.buildings.size()>=MaxBuildings || w.applied_transaction_ids.size()>=MaxServiceRecords || w.next_id>=std::numeric_limits<EntityId>::max()-1 || w.next_transaction_id>=std::numeric_limits<EntityId>::max()-1 || w.revision>=std::numeric_limits<std::uint64_t>::max()-1) return {false,PlacementCode::CapacityExceeded,0,geometry.ground_z_cm};
    return geometry;
}
PlacementResult PlaceBuilding(World& w,const BuildingCatalog& catalog,const PlacementCommand& c,const PlacementObserver& observer) {
    const auto stage=[&observer](PlacementTraceStage value) {if(observer.on_stage) observer.on_stage(value,observer.context);};
    stage(PlacementTraceStage::InitialValidationBegin);
    const auto initial_validation=ValidateWorld(w);
    stage(PlacementTraceStage::InitialValidationEnd);
    if(!initial_validation.ok) return Rejected(PlacementCode::InvalidWorld);
    if(c.transaction_id==0) return Rejected(PlacementCode::InvalidCommand);
    if(w.applied_transaction_ids.contains(c.transaction_id)) {
        for(const auto& [id,b]:w.buildings) if(b.placement_transaction_id==c.transaction_id) {
            if(SameCommand(b,c)) return {true,PlacementCode::AlreadyApplied,id,b.z_cm};
            return Rejected(PlacementCode::TransactionConflict);
        }
        return Rejected(PlacementCode::TransactionConflict);
    }
    if(c.transaction_id>=std::numeric_limits<EntityId>::max()-1) return Rejected(PlacementCode::CapacityExceeded);
    stage(PlacementTraceStage::PlacementValidationBegin);
    auto result=EvaluatePlacement(w,catalog,c);
    stage(PlacementTraceStage::PlacementValidationEnd);
    if(!result.ok) return result;
    const auto& d=catalog.at(c.definition_id);
    stage(PlacementTraceStage::CandidateCopyBegin);
    World candidate=w;
    stage(PlacementTraceStage::CandidateCopyEnd);
    auto id=candidate.next_id++;
    Building building{id,c.settlement_id,c.district_id,c.transaction_id,c.definition_id,d.version,c.x_cm,c.y_cm,result.ground_z_cm,c.yaw_degrees,d.width_cm,d.depth_cm,d.height_cm,ConstructionState::Completed,d.max_height_variation_cm,d.max_slope_permille};
    candidate.buildings.emplace(id,std::move(building)); auto& stocks=candidate.settlements.at(c.settlement_id).resources; stocks.timber-=d.timber_cost; stocks.treasury-=d.treasury_cost;
    candidate.applied_transaction_ids.insert(c.transaction_id); candidate.next_transaction_id=std::max(candidate.next_transaction_id,c.transaction_id+1); ++candidate.revision;
    stage(PlacementTraceStage::CandidateValidationBegin);
    const auto candidate_validation=ValidateWorld(candidate);
    stage(PlacementTraceStage::CandidateValidationEnd);
    if(!candidate_validation.ok) return Rejected(PlacementCode::InvalidWorld);
    w=std::move(candidate);
    stage(PlacementTraceStage::Committed);
    result.building_id=id; return result;
}
}
