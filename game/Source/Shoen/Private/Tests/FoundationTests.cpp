#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "ShoenSimulationSubsystem.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Engine/GameInstance.h"
#include "GameFramework/InputSettings.h"
#include "GameFramework/PlayerInput.h"
#include "Components/InputComponent.h"
#include "FoundationPlayerController.h"
#include "Tests/AutomationCommon.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenSelectionProjectionFailure, "Shoen.Foundation.SelectionProjectionFailure",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenSelectionProjectionFailure::RunTest(const FString& Parameters)
{
    FTestWorldWrapper Fixture;
    if (!TestTrue(TEXT("test world created"),Fixture.CreateTestWorld(EWorldType::Game))) return false;
    auto* World = Fixture.GetTestWorld();
    auto* Sim = World->GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    Sim->ResetScenario(1000);
    auto* Controller = World->SpawnActor<AFoundationPlayerController>();
    Controller->SelectAll();
    const TSet<uint64> Before = Controller->Selected;
    Controller->SelectionStart = Controller->SelectionEnd = FVector2D(600,400);
    Controller->bSelecting = true;
    FVector Ground = FVector::ZeroVector;
    TestFalse(TEXT("no player viewport means cursor projection fails"),Controller->GroundAtCursor(Ground));
    Controller->FinishSelection();
    TestFalse(TEXT("invalid selection gesture is cancelled"),Controller->bSelecting);
    TestEqual(TEXT("failed projection preserves selection"),Controller->Selected.Num(),Before.Num());
    for (const uint64 Id : Before) TestTrue(TEXT("selected formation preserved"),Controller->Selected.Contains(Id));
    // PlayerTick formerly replaced a failed mouse query with (0,0), converting
    // an outside-window release into a box selection rather than cancelling it.
    Controller->SelectAll();
    Controller->SelectionStart = FVector2D(600,400);
    Controller->SelectionEnd = FVector2D::ZeroVector;
    Controller->bSelecting = true;
    Controller->FinishSelection();
    TestFalse(TEXT("invalid box gesture is cancelled"),Controller->bSelecting);
    TestEqual(TEXT("invalid box endpoint preserves selection"),Controller->Selected.Num(),Before.Num());
    Fixture.DestroyTestWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenInputConfiguration, "Shoen.Foundation.InputConfiguration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenInputConfiguration::RunTest(const FString& Parameters)
{
    TestTrue(TEXT("player input works without optional plugins"),UInputSettings::GetDefaultPlayerInputClass()==UPlayerInput::StaticClass());
    TestTrue(TEXT("native input component"),UInputSettings::GetDefaultInputComponentClass()==UInputComponent::StaticClass());
    TestEqual(TEXT("speed keys do not also change render modes"),GetDefault<UPlayerInput>()->DebugExecBindings.Num(),0);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenPopulationProof, "Shoen.Foundation.PopulationAndSave",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenPopulationProof::RunTest(const FString& Parameters)
{
    auto* Sim = NewObject<UShoenSimulationSubsystem>(NewObject<UGameInstance>());
    Sim->ResetScenario(0);
    TestEqual(TEXT("200 workers"), domain::Summarize(Sim->State).available, int64(200));
    TestTrue(TEXT("mobilize"), Sim->MobilizeProof());
    TestEqual(TEXT("100 available"), domain::Summarize(Sim->State).available, int64(100));
    TestTrue(TEXT("scripted exact result"), Sim->ResolveProof());
    TestTrue(TEXT("demobilize"), Sim->DemobilizeProof());
    const auto Summary = domain::Summarize(Sim->State);
    TestEqual(TEXT("165 workers return"), Summary.available, int64(165));
    TestEqual(TEXT("15 recovering"), Summary.recovering, int64(15));
    TestEqual(TEXT("20 dead"), Summary.dead, int64(20));
    const auto Before = Sim->State;
    const FString File = FPaths::ProjectSavedDir() / TEXT("Automation/FoundationProof.sav");
    TestTrue(TEXT("save actual file"), Sim->SaveToPath(File));
    Sim->ResetScenario(1000);
    TestTrue(TEXT("load actual file"), Sim->LoadFromPath(File));
    TestTrue(TEXT("full model restored"), Sim->State == Before);
    IFileManager::Get().Delete(*File);
    IFileManager::Get().Delete(*(File + TEXT(".bak")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenSpeedTest, "Shoen.Foundation.ClockBinding",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenSpeedTest::RunTest(const FString& Parameters)
{
    auto* Sim = NewObject<UShoenSimulationSubsystem>(NewObject<UGameInstance>());
    Sim->ResetScenario(0);
    Sim->SetGameSpeed(0);
    Sim->Advance(30.0f);
    TestEqual(TEXT("pause"), Sim->State.campaign_day, int64(0));
    Sim->SetGameSpeed(10);
    Sim->Advance(3.0f);
    TestEqual(TEXT("ten fixed days"), Sim->State.campaign_day, int64(10));
    TestTrue(TEXT("valid world"), domain::ValidateWorld(Sim->State).ok);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenViewPersistence, "Shoen.Foundation.ViewDoesNotResetPopulation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenViewPersistence::RunTest(const FString& Parameters)
{
    auto* Sim = NewObject<UShoenSimulationSubsystem>(NewObject<UGameInstance>());
    Sim->ResetScenario(0);
    Sim->PrepareForLevel(0);
    Sim->MobilizeProof();
    Sim->ResolveProof();
    Sim->Advance(3.0f);
    const auto Before = Sim->State;
    Sim->PrepareForLevel(8000);
    TestTrue(TEXT("Reopening view preserves campaign and ignores startup fixture"),Sim->State == Before);
    return true;
}
#endif
