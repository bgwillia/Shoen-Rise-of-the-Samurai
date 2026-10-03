#include "TerrainSuitability.h"
#include "LandscapeProxy.h"
#include "WaterBodyActor.h"
#include "WaterSplineComponent.h"
#include "WaterSplineMetadata.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "domain/Buildings.h"

using namespace domain::suitability;
namespace {
FColor Colors[]={FColor(35,230,70),FColor(250,220,35),FColor(255,125,15),FColor(230,35,30),FColor(25,130,255)};
int32 QualityColor(Quality Q) { return Q==Quality::Ideal ? 0 : Q==Quality::Usable ? 1 : Q==Quality::Marginal ? 2 : 3; }
struct FLiveBuildingTerrain final : domain::BuildingTerrain {
    TWeakObjectPtr<ATerrainSuitability> Service;
    explicit FLiveBuildingTerrain(ATerrainSuitability* In) : Service(In) {}
    domain::PlacementResult Evaluate(const domain::PlacementCommand& C,const domain::BuildingDefinition& D) const override {
        if(!Service.IsValid()) return {false,domain::PlacementCode::OutsideBuildArea};
        const auto R=Service->EvaluateBuildingFootprint(FTransform(FRotator(0,C.yaw_degrees,0),FVector(C.x_cm,C.y_cm,0)),FVector2D(D.width_cm,D.depth_cm));
        domain::PlacementCode Code=domain::PlacementCode::Valid;
        switch(R.Result) {
        case BuildingResult::TooSteep: Code=domain::PlacementCode::TerrainTooSteep; break;
        case BuildingResult::TooUneven: Code=domain::PlacementCode::TerrainTooUneven; break;
        case BuildingResult::InWater: Code=domain::PlacementCode::InWater; break;
        case BuildingResult::OutsideBuildableTerrain: Code=domain::PlacementCode::OutsideBuildArea; break;
        default: break;
        }
        return {Code==domain::PlacementCode::Valid,Code,0,FMath::RoundToInt(R.GroundZ)};
    }
};
}
ATerrainSuitability::ATerrainSuitability()
{
    PrimaryActorTick.bCanEverTick=false;
    RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("TerrainSuitability_01"));
}
ATerrainSuitability* ATerrainSuitability::Find(UWorld* World)
{
    if(World) { TActorIterator<ATerrainSuitability> It(World); if(It) return *It; }
    return nullptr;
}
void ATerrainSuitability::InitializeSources()
{
    Rules={};
    FString Text; TSharedPtr<FJsonObject> Config;
    if(FFileHelper::LoadFileToString(Text,*(FPaths::ProjectConfigDir()/TEXT("TerrainSuitability_01.json"))) && FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Config)) {
        auto Read=[&](const TCHAR* Key,double& Value) { double N; if(Config->TryGetNumberField(Key,N) && FMath::IsFinite(N) && N>=0) Value=N; };
#define READ_RULE(Name) Read(TEXT(#Name),Rules.Name)
        READ_RULE(building_ideal); READ_RULE(building_max); READ_RULE(building_marginal); READ_RULE(building_variation_cm);
        READ_RULE(rice_ideal); READ_RULE(rice_max); READ_RULE(dry_ideal); READ_RULE(dry_usable); READ_RULE(dry_max);
        READ_RULE(water_access_cm); READ_RULE(wet_bank_cm); READ_RULE(wet_height_cm); READ_RULE(rice_lowland_cm);
#undef READ_RULE
        auto Movement=[&](const TCHAR* Key,MovementRules& R) { const TSharedPtr<FJsonObject>* Obj; if(Config->TryGetObjectField(Key,Obj)) {
            auto ReadM=[&](const TCHAR* K,double& V) { double N; if((*Obj)->TryGetNumberField(K,N) && FMath::IsFinite(N) && N>=0) V=N; };
            ReadM(TEXT("normal"),R.normal); ReadM(TEXT("slow"),R.slow); ReadM(TEXT("maximum"),R.maximum);
            ReadM(TEXT("slow_speed"),R.slow_speed); ReadM(TEXT("difficult_speed"),R.difficult_speed); ReadM(TEXT("wet_speed"),R.wet_speed);
        }};
        Movement(TEXT("infantry"),Rules.infantry); Movement(TEXT("cavalry"),Rules.cavalry);
        Read(TEXT("debug_spacing_cm"),DebugSpacingCm); Read(TEXT("footprint_spacing_cm"),FootprintSpacingCm); Read(TEXT("debug_footprint_cm"),DebugFootprintCm);
    }
    DebugSpacingCm=FMath::Clamp(DebugSpacingCm,500.,1000.); FootprintSpacingCm=FMath::Clamp(FootprintSpacingCm,50.,300.);
    DebugFootprintCm=FMath::Clamp(DebugFootprintCm,100.,3000.);
    LandscapeBounds=FBox(ForceInit); WaterOutlines.Reset(); DebugSamples.Reset();
    GroundTrace=FCollisionQueryParams(SCENE_QUERY_STAT(TerrainSuitability),true);
    for(TActorIterator<AActor> It(GetWorld());It;++It) {
        if(auto* Land=Cast<ALandscapeProxy>(*It)) LandscapeBounds+=Land->GetComponentsBoundingBox(true);
        else GroundTrace.AddIgnoredActor(*It);
        auto* Water=Cast<AWaterBody>(*It); if(!Water) continue;
        const FString Identity=Water->GetName()+Water->GetActorNameOrLabel();
        FWaterOutline Outline;
        Outline.bClosed=Water->GetWaterBodyType()==EWaterBodyType::Lake;
        if(!Outline.bClosed && Water->GetWaterBodyType()!=EWaterBodyType::River) continue;
        Outline.Type=Outline.bClosed ? Water::StandingWater : (Identity.Contains(TEXT("Tributary")) || Water->ActorHasTag(TEXT("Suitability.Tributary"))) ? Water::Tributary : Water::MainRiver;
        auto* Spline=Water->GetWaterSpline(); const auto* Meta=Water->GetWaterSplineMetadata();
        // Cache only existing water outlines, at the landscape's ~3m geometric resolution.
        const int32 Steps=FMath::Max(2,FMath::CeilToInt(Spline->GetSplineLength()/300.));
        for(int32 I=0;I<=Steps;++I) {
            const float Distance=Spline->GetSplineLength()*I/Steps;
            Outline.Points.Add(Spline->GetLocationAtDistanceAlongSpline(Distance,ESplineCoordinateSpace::World));
            const float Key=Spline->GetInputKeyValueAtDistanceAlongSpline(Distance);
            Outline.HalfWidths.Add(Meta ? Meta->RiverWidth.Eval(Key)*.5 : 0.);
        }
        WaterOutlines.Add(MoveTemp(Outline));
    }
    bSourcesReady=LandscapeBounds.IsValid;
}
bool ATerrainSuitability::TraceGround(const FVector& Start,const FVector& End,FHitResult& Hit) const
{
    return bSourcesReady && GetWorld()->LineTraceSingleByChannel(Hit,Start,End,ECC_Visibility,GroundTrace) && Cast<ALandscapeProxy>(Hit.GetActor());
}
FTerrainSuitabilitySample ATerrainSuitability::Query(FVector Location) const
{
    FTerrainSuitabilitySample R; R.Position=Location;
    FHitResult Hit;
    if(!TraceGround(FVector(Location.X,Location.Y,LandscapeBounds.Max.Z+10000),FVector(Location.X,Location.Y,LandscapeBounds.Min.Z-10000),Hit)) return R;
    R.bInside=true; R.Position=Hit.ImpactPoint; R.Normal=Hit.ImpactNormal;
    R.SlopeDegrees=FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(double(Hit.ImpactNormal.Z),0.,1.)));
    double NearestBank=TNumericLimits<double>::Max(),WaterZ=0;
    for(const auto& Outline:WaterOutlines) {
        bool bInPolygon=false; double Distance=TNumericLimits<double>::Max(),SurfaceZ=0;
        for(int32 I=1;I<Outline.Points.Num();++I) {
            const auto& A=Outline.Points[I-1]; const auto& B=Outline.Points[I];
            const FVector2D P(Location),AA(A),BB(B),Delta=BB-AA;
            const double T=FMath::Clamp(FVector2D::DotProduct(P-AA,Delta)/FMath::Max(Delta.SizeSquared(),.001),0.,1.);
            const double D=(P-(AA+T*Delta)).Size()-(Outline.bClosed ? 0 : FMath::Lerp(Outline.HalfWidths[I-1],Outline.HalfWidths[I],T));
            if(D<Distance) { Distance=D; SurfaceZ=FMath::Lerp(A.Z,B.Z,T); }
            if(Outline.bClosed && ((A.Y>Location.Y)!=(B.Y>Location.Y)) && Location.X<(B.X-A.X)*(Location.Y-A.Y)/(B.Y-A.Y)+A.X) bInPolygon=!bInPolygon;
        }
        const bool bInside=Outline.bClosed ? bInPolygon : Distance<=0;
        // The actual bed must be at/below the authored surface. Exposed bars stay land.
        if(bInside && R.Position.Z<=SurfaceZ+10) {
            R.Water=Outline.Type; R.WaterSurfaceZ=SurfaceZ; return R;
        }
        if(Distance<NearestBank) { NearestBank=Distance; WaterZ=SurfaceZ; }
    }
    const double HeightAboveWater=R.Position.Z-WaterZ;
    R.bNearLowWater=NearestBank<=Rules.water_access_cm && R.Position.Z<=Rules.rice_lowland_cm && HeightAboveWater<=Rules.wet_height_cm;
    if(NearestBank<=Rules.wet_bank_cm && R.Position.Z<=Rules.rice_lowland_cm && HeightAboveWater<=Rules.wet_height_cm) R.Water=Water::WetFlat;
    return R;
}
float ATerrainSuitability::GetSlopeDegrees(FVector P) const { const auto S=Query(P); return S.bInside ? S.SlopeDegrees : -1; }
FBuildingSuitability ATerrainSuitability::EvaluateBuildingFootprint(const FTransform& Transform,FVector2D SizeCm) const
{
    FBuildingSuitability R; const auto Center=Query(Transform.GetLocation()); R.GroundZ=Center.Position.Z;
    if(!Center.bInside || !FMath::IsFinite(SizeCm.X) || !FMath::IsFinite(SizeCm.Y) || SizeCm.X<=0 || SizeCm.Y<=0) return R;
    const int32 NX=FMath::Max(2,FMath::CeilToInt(SizeCm.X*FMath::Abs(Transform.GetScale3D().X)/FootprintSpacingCm));
    const int32 NY=FMath::Max(2,FMath::CeilToInt(SizeCm.Y*FMath::Abs(Transform.GetScale3D().Y)/FootprintSpacingCm));
    if(int64(NX+1)*(NY+1)>65536) return R; // malformed/unbounded query, never silently undersample
    double Low=Center.Position.Z,High=Low; bool bInside=true; Water WaterType=Center.Water;
    for(int32 Y=0;Y<=NY;++Y) for(int32 X=0;X<=NX;++X) {
        const auto S=Query(Transform.TransformPosition(FVector((double(X)/NX-.5)*SizeCm.X,(double(Y)/NY-.5)*SizeCm.Y,0)));
        bInside&=S.bInside; R.MaxSlopeDegrees=FMath::Max(R.MaxSlopeDegrees,S.SlopeDegrees);
        Low=FMath::Min(Low,S.Position.Z); High=FMath::Max(High,S.Position.Z);
        if(Standing(S.Water)) WaterType=S.Water;
    }
    R.HeightVariationCm=High-Low;
    R.Result=Building(R.MaxSlopeDegrees,R.HeightVariationCm,WaterType,bInside,Rules); return R;
}
Quality ATerrainSuitability::EvaluateRiceSuitability(FVector P) const { const auto S=Query(P); return Rice(S.SlopeDegrees,S.bNearLowWater,S.Water,S.bInside,Rules); }
Quality ATerrainSuitability::EvaluateDryFarmSuitability(FVector P) const { const auto S=Query(P); return DryFarm(S.SlopeDegrees,S.Water,S.bInside,Rules); }
Traversal ATerrainSuitability::GetInfantryTraversal(FVector P) const { const auto S=Query(P); return Traverse(S.SlopeDegrees,S.Water,S.bInside,Rules.infantry,Rules); }
Traversal ATerrainSuitability::GetCavalryTraversal(FVector P) const { const auto S=Query(P); return Traverse(S.SlopeDegrees,S.Water,S.bInside,Rules.cavalry,Rules); }
domain::BuildArea ATerrainSuitability::MakeBuildArea(uint64 SettlementId)
{
    if(!bSourcesReady) InitializeSources();
    domain::BuildArea A; A.settlement_id=SettlementId;
    A.origin_x_cm=FMath::CeilToInt(LandscapeBounds.Min.X); A.origin_y_cm=FMath::CeilToInt(LandscapeBounds.Min.Y);
    A.columns=A.rows=2; A.cell_size_cm=FMath::CeilToInt(FMath::Max(LandscapeBounds.GetSize().X,LandscapeBounds.GetSize().Y)); A.heights_cm={0,0,0,0};
    A.live_terrain=std::make_shared<FLiveBuildingTerrain>(this); return A;
}
void ATerrainSuitability::BuildDebugSamples()
{
    // Temporary 10m point grid; building mode additionally samples a representative 6m lot.
    for(double Y=LandscapeBounds.Min.Y+DebugSpacingCm*.5;Y<LandscapeBounds.Max.Y;Y+=DebugSpacingCm)
        for(double X=LandscapeBounds.Min.X+DebugSpacingCm*.5;X<LandscapeBounds.Max.X;X+=DebugSpacingCm) {
            FDebugSample S; S.Terrain=Query(FVector(X,Y,0)); if(!S.Terrain.bInside) continue;
            DebugSamples.Add(S);
        }
}
void ATerrainSuitability::SetDebugMode(int32 Mode)
{
    if(!bSourcesReady) InitializeSources();
    DebugMode=FMath::Clamp(Mode,0,5);
    for(const auto& C:Markers) C->ClearInstances();
    if(!DebugMode) return;
    if(DebugSamples.IsEmpty()) BuildDebugSamples();
    if(Markers.IsEmpty()) for(int32 I=0;I<5;++I) {
        auto* C=NewObject<UInstancedStaticMeshComponent>(this,NAME_None,RF_Transient); C->SetupAttachment(RootComponent);
        C->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Plane.Plane")));
        C->SetCollisionEnabled(ECollisionEnabled::NoCollision); C->SetCanEverAffectNavigation(false); C->SetCastShadow(false);
        auto* Mat=UMaterialInstanceDynamic::Create(LoadObject<UMaterialInterface>(nullptr,TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")),this);
        Mat->SetVectorParameterValue(TEXT("Color"),FLinearColor(Colors[I])); C->SetMaterial(0,Mat);
        C->RegisterComponent(); Markers.Add(C);
    }
    TArray<FTransform> Instances[5];
    for(auto& D:DebugSamples) {
        const auto& S=D.Terrain; int32 Color=3;
        if(DebugMode==1) {
            double Low=S.Position.Z,High=Low,Slope=S.SlopeDegrees; bool Inside=true; Water W=S.Water;
            for(const FVector2D Offset:{FVector2D(-1,-1),FVector2D(1,-1),FVector2D(1,1),FVector2D(-1,1)}) {
                const auto Corner=Query(S.Position+FVector(Offset.X,Offset.Y,0)*DebugFootprintCm*.5);
                Inside&=Corner.bInside; Low=FMath::Min(Low,Corner.Position.Z); High=FMath::Max(High,Corner.Position.Z); Slope=FMath::Max(Slope,Corner.SlopeDegrees);
                if(Standing(Corner.Water)) W=Corner.Water;
            }
            D.Building={Building(Slope,High-Low,W,Inside,Rules),Slope,High-Low,S.Position.Z};
            Color=D.Building.Result==BuildingResult::Valid ? 0 : D.Building.Result==BuildingResult::InWater ? 4 :
                (D.Building.Result==BuildingResult::TooSteep && D.Building.MaxSlopeDegrees<=Rules.building_marginal && D.Building.HeightVariationCm<=Rules.building_variation_cm) ? 1 : 3;
        }
        if(DebugMode==2) { Color=QualityColor(Rice(S.SlopeDegrees,S.bNearLowWater,S.Water,true,Rules)); if(Color==2) Color=1; }
        if(DebugMode==3) Color=QualityColor(DryFarm(S.SlopeDegrees,S.Water,true,Rules));
        if(DebugMode>=4) Color=QualityColor(Traverse(S.SlopeDegrees,S.Water,true,DebugMode==4 ? Rules.infantry : Rules.cavalry,Rules).quality);
        const FVector P(S.Position.X,S.Position.Y,FMath::Max(S.Position.Z,S.WaterSurfaceZ)+100);
        Instances[Color].Add(FTransform(FRotationMatrix::MakeFromZ(S.Normal).ToQuat(),P,FVector(DebugSpacingCm*.0055,DebugSpacingCm*.0055,1)));
    }
    for(int32 I=0;I<5;++I) Markers[I]->AddInstances(Instances[I],false,true,false);
}
void ATerrainSuitability::CycleDebugMode() { SetDebugMode((DebugMode+1)%6); }
FString ATerrainSuitability::DebugLabel() const
{
    const TCHAR* Names[]={TEXT("Off"),TEXT("BUILDING (6m lot)"),TEXT("RICE"),TEXT("DRY FARM"),TEXT("INFANTRY"),TEXT("CAVALRY")};
    return Names[DebugMode];
}
FString ATerrainSuitability::DescribeLocation(FVector P) const
{
    const auto S=Query(P); const auto B=EvaluateBuildingFootprint(FTransform(P),FVector2D(DebugFootprintCm,DebugFootprintCm));
    return FString::Printf(TEXT("xy=(%.0f,%.0f) z=%.1f slope=%.2f footprint_slope=%.2f variation=%.1f water=%d building=%d rice=%d dry=%d infantry=%.2f cavalry=%.2f"),P.X,P.Y,S.Position.Z,S.SlopeDegrees,B.MaxSlopeDegrees,B.HeightVariationCm,int32(S.Water),int32(B.Result),int32(EvaluateRiceSuitability(P)),int32(EvaluateDryFarmSuitability(P)),GetInfantryTraversal(P).speed,GetCavalryTraversal(P).speed);
}
void ATerrainSuitability::WriteQuickCheck()
{
    if(!bSourcesReady) InitializeSources();
    if(DebugSamples.IsEmpty()) BuildDebugSamples();
    FString Report; double MaxSlope=0; int32 Split=0,WaterCount=0;
    for(const auto& D:DebugSamples) {
        const auto& S=D.Terrain; MaxSlope=FMath::Max(MaxSlope,S.SlopeDegrees);
        if(Standing(S.Water)) ++WaterCount;
        if(S.SlopeDegrees>Rules.cavalry.maximum && S.SlopeDegrees<=Rules.infantry.maximum && !Standing(S.Water)) { if(Split==0) Report+=TEXT("Cavalry blocked / infantry difficult: ")+DescribeLocation(S.Position)+TEXT("\n"); ++Split; }
    }
    for(const auto P:{FVector(22000,-23000,0),FVector(10000,30000,0),FVector(-50000,-35000,0)}) Report+=DescribeLocation(P)+TEXT("\n");
    Report+=FString::Printf(TEXT("grid=%d max_slope=%.2f cavalry_only_blocked=%d water=%d\n"),DebugSamples.Num(),MaxSlope,Split,WaterCount);
    FFileHelper::SaveStringToFile(Report,*(FPaths::ProjectDir()/TEXT("../artifacts/terrainsuitability01/map-check.txt")));
    UE_LOG(LogTemp,Display,TEXT("TerrainSuitability quick check:\n%s"),*Report);
}
