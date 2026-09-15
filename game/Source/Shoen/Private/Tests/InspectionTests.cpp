#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "FoundationPlayerController.h"
#include "FoundationGameMode.h"
#include "ShoenSimulationSubsystem.h"
#include "SettlementView.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "domain/Inspection.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenInspectionLifecycle, "Shoen.Inspection.SelectionLifecycleAndReload",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenInspectionLifecycle::RunTest(const FString& Parameters)
{
    FTestWorldWrapper Fixture;
    if (!TestTrue(TEXT("test world created"),Fixture.CreateTestWorld(EWorldType::Game))) return false;
    auto* World=Fixture.GetTestWorld();
    FURL URL; URL.AddOption(TEXT("game=/Script/Shoen.FoundationGameMode"));
    if (!TestTrue(TEXT("real game mode"),World->SetGameMode(URL))) return false;
    auto* Mode=Cast<AFoundationGameMode>(World->GetAuthGameMode());
    if (!TestNotNull(TEXT("foundation game mode"),Mode)) return false;
    // Controller registration occurs in PostInitializeComponents. A bare test
    // World defers that until actors initialize, unlike the running game.
    World->InitializeActorsForPlay(URL);
    auto* Sim=World->GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    auto* PC=World->SpawnActor<AFoundationPlayerController>();
    if (!TestTrue(TEXT("game mode can find the initialized player controller"),World->GetFirstPlayerController()==PC)) return false;
    if (!TestTrue(TEXT("real settlement content"),Sim->ResetSettlement())) return false;
    Sim->SetGameSpeed(0);
    const domain::PlacementCommand Commands[]={
        {1,"small_storehouse",1,2,-2000,-1000,0},
        {2,"small_storehouse",1,2,0,1000,30},
        {3,"small_storehouse",1,2,2000,-1000,75}};
    TArray<uint64> Ids;
    for (auto Command : Commands)
    {
        Command.transaction_id=Sim->State.next_transaction_id;
        const auto Placed=Sim->PlaceBuilding(Command);
        if (!TestTrue(TEXT("distinct valid placement"),Placed.ok)) return false;
        Ids.Add(Placed.building_id);
    }
    TestTrue(TEXT("three unique stable IDs"),Ids[0]!=Ids[1] && Ids[1]!=Ids[2] && Ids[0]!=Ids[2]);
    const auto PlacedWorld=Sim->State;
    Mode->RebuildViews();
    auto* View=Mode->SettlementPresentation();
    for (int32 I=0; I<3; ++I)
    {
        uint64 HitId=0;
        const auto& Command=Commands[I];
        TestTrue(TEXT("visual roof hit"),View->PickBuilding(FVector(Command.x_cm,Command.y_cm,2000),FVector(0,0,-1),HitId));
        PC->InspectBuilding(HitId);
        TestEqual(TEXT("controller applies highlight to clicked building"),View->SelectedBuildingId(),Ids[I]);
        const auto* Record=domain::ResolveBuilding(Sim->State,PC->InspectionSelection());
        TestTrue(TEXT("hit resolves to clicked authoritative record, never another"),Record==&Sim->State.buildings.at(Ids[I]));
    }
    PC->InspectBuilding(0);
    TestTrue(TEXT("empty hit clears selection"),PC->InspectionSelection().kind==domain::EntityKind::None);
    PC->InspectBuilding(Ids[0]);
    PC->BeginPlacement();
    TestTrue(TEXT("placement entry clears selection"),PC->InspectionSelection().kind==domain::EntityKind::None);
    TestEqual(TEXT("placement entry clears highlight"),View->SelectedBuildingId(),uint64(0));
    PC->InspectBuilding(Ids[1]);
    TestTrue(TEXT("ordinary picking cannot select during placement"),PC->InspectionSelection().kind==domain::EntityKind::None);
    PC->CancelPlacement();
    PC->InspectBuilding(Ids[1]);
    TestEqual(TEXT("selection restored after cancel"),uint64(PC->InspectionSelection().id),Ids[1]);
    View->Destroy();
    Mode->RebuildViews();
    View=Mode->SettlementPresentation();
    TestEqual(TEXT("recreated view reacquires same stable selection"),View->SelectedBuildingId(),Ids[1]);
    TestTrue(TEXT("all inspection and recreation leaves simulation unchanged"),Sim->State==PlacedWorld);

    const FString File=FPaths::ProjectSavedDir()/TEXT("Automation/InspectionProof.sav");
    TestTrue(TEXT("save selected building layout"),Sim->SaveToPath(File));
    TestEqual(TEXT("save keeps selection"),uint64(PC->InspectionSelection().id),Ids[1]);
    auto Extra=Commands[0]; Extra.x_cm=-2000; Extra.y_cm=2000;
    Extra.transaction_id=Sim->State.next_transaction_id;
    TestTrue(TEXT("alter world after save"),Sim->PlaceBuilding(Extra).ok);
    Mode->RebuildViews();
    TestEqual(TEXT("same-world placement does not change selection"),uint64(PC->InspectionSelection().id),Ids[1]);
    TestTrue(TEXT("load accepted layout"),Sim->LoadFromPath(File));
    Mode->RebuildViews();
    TestTrue(TEXT("load intentionally clears UI selection"),PC->InspectionSelection().kind==domain::EntityKind::None);
    TestEqual(TEXT("load clears highlight even if ID remains"),View->SelectedBuildingId(),uint64(0));
    TestTrue(TEXT("exact saved world restored"),Sim->State==PlacedWorld);
    View->Rebuild(Sim->State);
    uint64 RestoredHit=0;
    TestTrue(TEXT("restored visual still pickable"),View->PickBuilding(FVector(0,1000,2000),FVector(0,0,-1),RestoredHit));
    PC->InspectBuilding(RestoredHit);
    const auto* Restored=domain::ResolveBuilding(Sim->State,PC->InspectionSelection());
    TestTrue(TEXT("restored click has same ID type and transform"),Restored && *Restored==PlacedWorld.buildings.at(Ids[1]));

    Sim->State.buildings.erase(Ids[1]); // Missing-record resilience, not a demolition feature.
    PC->RefreshInspection();
    TestTrue(TEXT("missing selected record clears safely"),PC->InspectionSelection().kind==domain::EntityKind::None);
    PC->InspectBuilding(Ids[1]);
    TestTrue(TEXT("stale visual ID cannot resolve another building"),PC->InspectionSelection().kind==domain::EntityKind::None);
    PC->InspectBuilding(Ids[0]);
    TestTrue(TEXT("reset settlement"),Sim->ResetSettlement());
    Extra.transaction_id=Sim->State.next_transaction_id;
    TestTrue(TEXT("replacement fixture can reuse a numeric ID"),Sim->PlaceBuilding(Extra).ok);
    PC->RefreshInspection();
    TestTrue(TEXT("replacement world never silently selects reused numeric ID"),PC->InspectionSelection().kind==domain::EntityKind::None);
    IFileManager::Get().Delete(*File); IFileManager::Get().Delete(*(File+TEXT(".bak")));
    Fixture.DestroyTestWorld(false);
    return true;
}
#endif
