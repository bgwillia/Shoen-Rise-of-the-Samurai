#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Engine/World.h"
#include "SettlementView.h"
#include "FoundationGameMode.h"
#include "ShoenSimulationSubsystem.h"
#include "FoundationPlayerController.h"
#include "BuildingContent.h"
#include "Engine/GameInstance.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "domain/Buildings.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenBuildingView, "Shoen.Placement.PassiveViewRecreation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenBuildingView::RunTest(const FString& Parameters)
{
    FTestWorldWrapper Fixture;
    if (!TestTrue(TEXT("test world created"), Fixture.CreateTestWorld(EWorldType::Game))) return false;
    domain::World State = domain::MakeFoundationWorld();
    domain::BuildArea Area;
    Area.settlement_id=1; Area.origin_x_cm=-2000; Area.origin_y_cm=-2000;
    Area.cell_size_cm=1000; Area.columns=5; Area.rows=5; Area.heights_cm.resize(25,0);
    State.build_areas.emplace(1,Area);
    domain::Building Building;
    Building.id=State.next_id++; Building.settlement_id=1; Building.district_id=2;
    Building.definition_id="small_storehouse"; Building.definition_version=1;
    Building.width_cm=800; Building.depth_cm=600; Building.height_cm=450;
    Building.x_cm=400; Building.y_cm=-300; Building.yaw_degrees=45;
    Building.placement_transaction_id=State.next_transaction_id++;
    State.applied_transaction_ids.insert(Building.placement_transaction_id);
    State.buildings.emplace(Building.id,Building);
    const auto Before=State;
    FTransform First;
    for (int Pass=0; Pass<2; ++Pass)
    {
        auto* View=Fixture.GetTestWorld()->SpawnActor<ASettlementView>();
        View->Rebuild(State);
        TestFalse(TEXT("ordinary buildings require no actor tick"),View->PrimaryActorTick.bCanEverTick);
        TestEqual(TEXT("one authoritative building rendered"),View->BuildingCount(),1);
        TestEqual(TEXT("same terrain triangles as core"),View->TerrainTriangleCount(),32);
        FTransform Actual;
        TestTrue(TEXT("stable ID resolves to view transform"),View->GetBuildingTransform(Building.id,Actual));
        const FTransform Expected(FRotator(0,45,0),FVector(400,-300,0));
        TestTrue(TEXT("saved base transform rendered exactly"),Actual.Equals(Expected));
        if (Pass==0) First=Actual;
        else TestTrue(TEXT("recreated view preserves transform"),Actual.Equals(First));
        View->Rebuild(State);
        TestEqual(TEXT("rebuild does not duplicate instances"),View->BuildingCount(),1);
        View->Destroy();
    }
    TestTrue(TEXT("view creation never changes simulation"),State==Before);
    Fixture.DestroyTestWorld(false);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenBuildingIntegration, "Shoen.Placement.ContentTransactionAndSave",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenBuildingIntegration::RunTest(const FString& Parameters)
{
    auto* Sim=NewObject<UShoenSimulationSubsystem>(NewObject<UGameInstance>());
    Sim->ResetScenario(0);
    if (!TestTrue(TEXT("real data imports into settlement fixture"),Sim->PrepareSettlementForLevel())) return false;
    Sim->SetGameSpeed(0);
    const auto& Definition=Sim->BuildingDefinitions().at("small_storehouse");
    TestEqual(TEXT("configured timber cost"),int64(Definition.timber_cost),int64(20));
    TestEqual(TEXT("configured treasury cost"),int64(Definition.treasury_cost),int64(5));
    TestEqual(TEXT("configured footprint width"),Definition.width_cm,800);
    const auto Before=Sim->State;
    domain::PlacementCommand Command{Sim->State.next_transaction_id,"small_storehouse",1,2,-2000,0,30};
    TestTrue(TEXT("valid preview"),Sim->PreviewBuilding(Command).ok);
    TestTrue(TEXT("preview never mutates authoritative state"),Sim->State==Before);
    const uint64 Generation=Sim->WorldGeneration;
    const auto Placed=Sim->PlaceBuilding(Command);
    TestTrue(TEXT("valid configured placement"),Placed.ok);
    if (!Placed.ok) return false;
    TestEqual(TEXT("exact timber debit"),int64(Sim->State.settlements.at(1).resources.timber),int64(180));
    TestEqual(TEXT("exact treasury debit"),int64(Sim->State.settlements.at(1).resources.treasury),int64(95));
    TestEqual(TEXT("placing an empty building creates no workers"),int64(domain::Summarize(Sim->State).available),int64(200));
    TestEqual(TEXT("placement keeps active world generation"),Sim->WorldGeneration,Generation);
    const auto Once=Sim->State;
    TestTrue(TEXT("duplicate delivery acknowledged"),Sim->PlaceBuilding(Command).ok);
    TestTrue(TEXT("duplicate neither spends nor creates"),Sim->State==Once);
    Command.transaction_id=Sim->State.next_transaction_id;
    const auto Overlap=Sim->PlaceBuilding(Command);
    TestTrue(TEXT("overlap reason typed"),Overlap.code==domain::PlacementCode::OverlapsBuilding);
    TestTrue(TEXT("failed attempt fully atomic"),Sim->State==Once);
    Command.x_cm=5000;
    TestTrue(TEXT("visible ramp is invalid terrain"),Sim->PreviewBuilding(Command).code==domain::PlacementCode::TerrainTooSteep);
    Command.x_cm=6000;
    TestTrue(TEXT("whole footprint must fit boundary"),Sim->PreviewBuilding(Command).code==domain::PlacementCode::OutsideBuildArea);
    const FString File=FPaths::ProjectSavedDir()/TEXT("Automation/SettlementProof.sav");
    TestTrue(TEXT("save real file"),Sim->SaveToPath(File));
    Command.x_cm=0;
    TestTrue(TEXT("alter with second building"),Sim->PlaceBuilding(Command).ok);
    TestTrue(TEXT("load saved layout"),Sim->LoadFromPath(File));
    TestTrue(TEXT("all IDs transforms types resources and time restored"),Sim->State==Once);
    TestTrue(TEXT("load invalidates stale input gestures"),Sim->WorldGeneration>Generation);
    const auto Restored=Sim->State;
    Sim->PrepareForLevel(8000);
    TestTrue(TEXT("reopening foundation map preserves settlement"),Sim->State==Restored);
    Sim->State.buildings.begin()->second.definition_id="unavailable_building";
    TestTrue(TEXT("write otherwise valid unknown-type snapshot"),Sim->SaveToPath(File));
    Sim->State=Restored;
    const uint64 BeforeRejectedLoad=Sim->WorldGeneration;
    TestFalse(TEXT("unavailable content rejected on load"),Sim->LoadFromPath(File));
    TestTrue(TEXT("rejected content preserves entire current world"),Sim->State==Restored);
    TestEqual(TEXT("rejected load preserves generation"),Sim->WorldGeneration,BeforeRejectedLoad);
    IFileManager::Get().Delete(*File); IFileManager::Get().Delete(*(File+TEXT(".bak")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenPlacementInput, "Shoen.Placement.InputCancelRotateAndConfirm",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenPlacementInput::RunTest(const FString& Parameters)
{
    FTestWorldWrapper Fixture;
    if (!TestTrue(TEXT("test world created"),Fixture.CreateTestWorld(EWorldType::Game))) return false;
    auto* World=Fixture.GetTestWorld();
    auto* Sim=World->GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    auto* PC=World->SpawnActor<AFoundationPlayerController>();
    Sim->ResetScenario(1000);
    const auto Foundation=Sim->State;
    PC->BeginPlacement();
    TestFalse(TEXT("building control cannot silently reset formation fixture"),PC->IsPlacing());
    TestTrue(TEXT("foundation unchanged"),Sim->State==Foundation);
    if (!TestTrue(TEXT("settlement fixture"),Sim->ResetSettlement())) return false;
    const auto Before=Sim->State;
    PC->BeginPlacement();
    TestTrue(TEXT("selected building enters placement mode"),PC->IsPlacing());
    PC->RotatePlacement(-1);
    TestEqual(TEXT("rotate negative wraps configured step"),PC->Placement().yaw_degrees,345);
    PC->CancelPlacement();
    PC->ConfirmPlacement();
    TestTrue(TEXT("rotation cancel and confirm after cancel cost nothing"),Sim->State==Before);
    PC->BeginPlacement();
    PC->bHasPlacementPoint=true; PC->PendingPlacement.x_cm=-2000;
    PC->ConfirmPlacement();
    const auto Placed=Sim->State;
    TestEqual(TEXT("UI command creates one record"),int32(Placed.buildings.size()),1);
    // A second delivery in the same frame cannot obtain a new transaction ID.
    PC->PendingPlacement.x_cm=0;
    PC->ConfirmPlacement();
    TestTrue(TEXT("same-frame confirm duplication suppressed"),Sim->State==Placed);
    Sim->ResetSettlement();
    PC->LastConfirmFrame=MAX_uint64;
    PC->ConfirmPlacement();
    TestTrue(TEXT("stale preview cannot place into replacement world"),Sim->State.buildings.empty());
    Fixture.DestroyTestWorld(false);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenContentRejection, "Shoen.Placement.ContentValidation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenContentRejection::RunTest(const FString& Parameters)
{
    FString Json,Error;
    TestTrue(TEXT("read real definition data"),FFileHelper::LoadFileToString(Json,*(FPaths::ProjectContentDir()/TEXT("Domain/Data/buildings.json"))));
    domain::BuildingCatalog Catalog;
    if (!TestTrue(TEXT("parse actual catalog"),ParseBuildingCatalog(Json,Catalog,Error))) return false;
    const auto Before=Catalog;
    const TArray<FString> Invalid={TEXT("{}"),TEXT("{\"schema_version\":1,\"buildings\":[null]}"),
        Json.Replace(TEXT("800"),TEXT("800.5")),Json.Replace(TEXT("timber_cost"),TEXT("misspelled_cost")),
        Json.Replace(TEXT("800"),TEXT("-800"))};
    for (const auto& Bad : Invalid)
    {
        TestFalse(TEXT("malformed definition rejected"),ParseBuildingCatalog(Bad,Catalog,Error));
        TestFalse(TEXT("readable content error"),Error.IsEmpty());
        TestTrue(TEXT("failed import preserves previous catalog"),Catalog==Before);
    }
    return true;
}
#endif
