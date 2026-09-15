#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "ShoenSimulationSubsystem.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Engine/GameInstance.h"
#include "GameFramework/InputSettings.h"
#include "GameFramework/PlayerInput.h"
#include "Components/InputComponent.h"

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
