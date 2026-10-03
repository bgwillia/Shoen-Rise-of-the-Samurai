#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "TerrainSuitability.h"
#include "ShoenSimulationSubsystem.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "WaterBodyActor.h"
#include "WaterSplineComponent.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenTerrainSuitabilityLiveMap,"Shoen.TerrainSuitability.LiveMap",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenTerrainSuitabilityLiveMap::RunTest(const FString&)
{
    ATerrainSuitability* Terrain=nullptr;
    for(const auto& Context:GEngine->GetWorldContexts()) if(Context.WorldType==EWorldType::Editor) {
        Terrain=ATerrainSuitability::Find(Context.World()); if(Terrain) break;
    }
    if(!TestNotNull(TEXT("Open TerrainBase_01 with TerrainSuitability_01"),Terrain)) return false;
    Terrain->InitializeSources();
    const FVector Village(22000,-23000,0),Hill(-50000,-35000,0),Ridge(-46500,39500,0);
    TestTrue(TEXT("actual village shelf builds"),Terrain->EvaluateBuildingFootprint(FTransform(Village),FVector2D(800,600)).Result==domain::suitability::BuildingResult::Valid);
    TestTrue(TEXT("actual hill rejects buildings"),Terrain->EvaluateBuildingFootprint(FTransform(Hill),FVector2D(800,600)).Result==domain::suitability::BuildingResult::TooSteep);
    TestTrue(TEXT("ridge blocks cavalry first"),Terrain->GetCavalryTraversal(Ridge).speed==0 && Terrain->GetInfantryTraversal(Ridge).speed>0);
    bool RiceIdeal=false;
    for(int Y=20000;Y<=50000 && !RiceIdeal;Y+=2500) for(int X=-25000;X<=20000;X+=2500) {
        // Small probe grid across the authored southern lowlands.
        const FVector P(X,Y,0);
        if(Terrain->EvaluateRiceSuitability(P)==domain::suitability::Quality::Ideal) { RiceIdeal=true; AddInfo(Terrain->DescribeLocation(P)); break; }
    }
    TestTrue(TEXT("southern rice flats include ideal wet lowland"),RiceIdeal);
    bool RiverBlocked=false;
    for(TActorIterator<AWaterBody> It(Terrain->GetWorld());It;++It) if(It->GetActorNameOrLabel().Contains(TEXT("MainRiver"))) {
        auto* S=It->GetWaterSpline();
        for(float F:{.2f,.5f,.8f}) {
            const auto P=S->GetLocationAtDistanceAlongSpline(S->GetSplineLength()*F,ESplineCoordinateSpace::World);
            if(Terrain->Query(P).Water==domain::suitability::Water::MainRiver) {
                RiverBlocked=Terrain->GetInfantryTraversal(P).speed==0 && Terrain->GetCavalryTraversal(P).speed==0;
                TestTrue(TEXT("river also rejects dry farming"),Terrain->EvaluateDryFarmSuitability(P)==domain::suitability::Quality::Unsuitable);
                break;
            }
        }
    }
    TestTrue(TEXT("main river blocks ordinary movement"),RiverBlocked);
    auto* Sim=NewObject<UShoenSimulationSubsystem>(NewObject<UGameInstance>());
    TestTrue(TEXT("existing settlement content loaded"),Sim->ResetSettlement());
    Sim->State.build_areas.at(1)=Terrain->MakeBuildArea(1);
    domain::PlacementCommand C{Sim->State.next_transaction_id,"small_storehouse",1,2,22000,-23000,15};
    const auto Before=Sim->State;
    const auto Preview=Sim->PreviewBuilding(C);
    TestTrue(TEXT("existing rotated building preview uses landscape"),Preview.ok && Preview.ground_z_cm>1900);
    TestTrue(TEXT("preview does not mutate settlement"),Sim->State==Before);
    C.x_cm=-50000; C.y_cm=-35000;
    TestTrue(TEXT("existing preview rejects hill"),Sim->PreviewBuilding(C).code==domain::PlacementCode::TerrainTooSteep);
    TestFalse(TEXT("commit also rejects hill"),Sim->PlaceBuilding(C).ok);
    TestTrue(TEXT("invalid landscape placement preserves ledger"),Sim->State==Before);
    return true;
}
#endif
