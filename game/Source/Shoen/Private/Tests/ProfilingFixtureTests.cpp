#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "ShoenSimulationSubsystem.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenProfilingFixtureIsolation,"Shoen.Profiling.FixtureIsolation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenProfilingFixtureIsolation::RunTest(const FString& Parameters)
{
    FTestWorldWrapper Fixture;
    if (!TestTrue(TEXT("world"),Fixture.CreateTestWorld(EWorldType::Game))) return false;
    auto* Sim=Fixture.GetTestWorld()->GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    if (!TestTrue(TEXT("settlement content"),Sim->ResetSettlement())) return false;
    const auto Original=Sim->State;
    const auto Catalog=Sim->BuildingDefinitions();
    const FString Path=FPaths::ProjectSavedDir()/TEXT("Automation/ProfilingIsolation.sav");
    TestTrue(TEXT("ordinary save before fixture"),Sim->SaveToPath(Path));
    const FString Message=Sim->Message;
    TArray<uint8> Bytes; FFileHelper::LoadFileToArray(Bytes,*Path);
    TestFalse(TEXT("invalid fixture rejected"),Sim->BeginProfilingFixture(2));
    TestTrue(TEXT("invalid fixture leaves World"),Sim->State==Original);
    if (!TestTrue(TEXT("ten-building fixture"),Sim->BeginProfilingFixture(10))) return false;
    const auto Baseline=Sim->State;
    TestEqual(TEXT("exact count"),int32(Baseline.buildings.size()),10);
    TestFalse(TEXT("nested fixture cannot overwrite original"),Sim->BeginProfilingFixture(1));
    TestFalse(TEXT("fixture cannot save to any path"),Sim->SaveToPath(Path));
    TestFalse(TEXT("fixture cannot load normal state"),Sim->LoadFromPath(Path));
    TestFalse(TEXT("normal reset blocked"),Sim->ResetSettlement());
    Sim->ResetScenario(1000);
    TestTrue(TEXT("blocked operations leave fixture state"),Sim->State==Baseline);
    TArray<uint8> After; FFileHelper::LoadFileToArray(After,*Path);
    TestTrue(TEXT("existing save bytes unchanged"),After==Bytes);
    domain::PlacementCommand Command{Sim->State.next_transaction_id,"small_storehouse",1,2,0,3350,15};
    TestTrue(TEXT("fixture uses authoritative transaction"),Sim->PlaceBuilding(Command).ok);
    TestTrue(TEXT("restore baseline"),Sim->RestoreProfilingBaseline());
    TestTrue(TEXT("baseline exact"),Sim->State==Baseline);
    Sim->EndProfilingFixture();
    TestFalse(TEXT("fixture flag cleared"),Sim->IsProfilingFixture());
    TestTrue(TEXT("original World and catalog restored"),Sim->State==Original && Sim->BuildingDefinitions()==Catalog);
    TestEqual(TEXT("original presentation message restored"),Sim->Message,Message);
    TestTrue(TEXT("normal save works again"),Sim->SaveToPath(Path));
    TestTrue(TEXT("normal load works again"),Sim->LoadFromPath(Path));
    TestTrue(TEXT("restored normal save contains no fixture"),Sim->State==Original);
    IFileManager::Get().Delete(*Path); IFileManager::Get().Delete(*(Path+TEXT(".bak")));
    Fixture.DestroyTestWorld(false);
    return true;
}
#endif
