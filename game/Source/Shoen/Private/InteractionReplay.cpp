#include "InteractionReplay.h"
#include "InteractionProfiler.h"
#include "FoundationPlayerController.h"
#include "ShoenSimulationSubsystem.h"
#include "Engine/GameInstance.h"
#include "Camera/PlayerCameraManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

FInteractionReplay::FInteractionReplay(AFoundationPlayerController& PC) : Controller(PC)
{
#if !UE_BUILD_SHIPPING
    bConfigured=FParse::Value(FCommandLine::Get(),TEXT("ShoenProfileBuildings="),Count);
    FParse::Value(FCommandLine::Get(),TEXT("ShoenProfileIterations="),Iterations);
    FParse::Value(FCommandLine::Get(),TEXT("ShoenProfileOutput="),Output);
    bDisabled=FParse::Param(FCommandLine::Get(),TEXT("ShoenProfileDisabled"));
    if (bConfigured && ((Count!=1 && Count!=10 && Count!=100) || Iterations<1 || Iterations>100 || Output.IsEmpty()))
    {
        UE_LOG(LogTemp,Error,TEXT("SHOEN_PROFILE invalid development replay arguments"));
        bConfigured=false;
    }
#endif
}
void FInteractionReplay::Point(int32 X,int32 Y,int32 Yaw)
{
    Controller.PendingPlacement.x_cm=X; Controller.PendingPlacement.y_cm=Y;
    Controller.PendingPlacement.yaw_degrees=Yaw; Controller.bHasPlacementPoint=true;
    Controller.RefreshPlacement(true);
}
void FInteractionReplay::Pick(double X,double Y)
{
    const FVector Origin=Controller.PlayerCameraManager->GetCameraLocation();
    Controller.PickAndInspect(Origin,(FVector(X,Y,225)-Origin).GetSafeNormal());
}
void FInteractionReplay::Step(int32 Phase)
{
    // Preparations have no input samples. Each observed state is held for ten
    // frames; the matching renderer hook decides whether it actually appeared.
    auto* Sim=Controller.GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    ShoenProfile::SetSamplingEnabled(true);
    switch (Phase)
    {
    case 0: { ShoenProfile::FActionScope Action(TEXT("select")); Pick(2250,2300); break; }
    case 1: { ShoenProfile::FActionScope Action(TEXT("clear")); Pick(4500,3350); break; }
    case 2:
        ShoenProfile::SetSamplingEnabled(false); Pick(2250,2300); break;
    case 3:
        if (Count>1) { ShoenProfile::FActionScope Action(TEXT("switch")); Pick(1400,2300); }
        break;
    case 4: { ShoenProfile::FActionScope Action(TEXT("enter")); Controller.BeginPlacement(); break; }
    case 5: { ShoenProfile::FActionScope Action(TEXT("preview")); Point(0,3350,0); break; }
    case 6: { ShoenProfile::FActionScope Action(TEXT("rotate")); Controller.RotatePlacement(1); break; }
    case 7:
        ShoenProfile::SetSamplingEnabled(false); Point(2250,2300,0); break;
    case 8: { ShoenProfile::FActionScope Action(TEXT("confirm")); Controller.ConfirmPlacement(); break; }
    case 9: { ShoenProfile::FActionScope Action(TEXT("preview")); Point(0,3350,15); break; }
    case 10: { ShoenProfile::FActionScope Action(TEXT("confirm")); Controller.ConfirmPlacement(); break; }
    case 11: { ShoenProfile::FActionScope Action(TEXT("cancel")); Controller.CancelPlacement(); break; }
    case 12:
        ShoenProfile::SetSamplingEnabled(false);
        Controller.CancelPlacement(); Sim->RestoreProfilingBaseline(); Controller.RefreshInspection();
        break;
    }
    ShoenProfile::SetSamplingEnabled(true);
}
bool FInteractionReplay::Tick(float DeltaSeconds)
{
    if (!bConfigured || bFinished) return false;
    auto* Sim=Controller.GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    if (!bStarted)
    {
        if (!Sim->BeginProfilingFixture(Count))
        {
            UE_LOG(LogTemp,Error,TEXT("SHOEN_PROFILE fixture failed: %s"),*Sim->Message);
            bFinished=true; FPlatformMisc::RequestExit(false); return true;
        }
        Controller.RefreshInspection();
        bStarted=true;
    }
    if (Warmup>0)
    {
        if (--Warmup==0)
        {
            if (!bDisabled && !ShoenProfile::Start(Controller.GetWorld(),Output))
            {
                UE_LOG(LogTemp,Error,TEXT("SHOEN_PROFILE capture failed to start"));
                Finish(); FPlatformMisc::RequestExit(false); return true;
            }
            ShoenProfile::SetReplaySource(true);
            ShoenProfile::SetSceneBuildingCount(Count);
            LastFrameTime=FPlatformTime::Seconds();
        }
        return true;
    }
    const double Now=FPlatformTime::Seconds();
    FrameTimes.Add((Now-LastFrameTime)*1000.0); LastFrameTime=Now;
    if (FrameIndex>=Iterations*130)
    {
        Finish(); FPlatformMisc::RequestExit(false); return true;
    }
    if (FrameIndex%10==0)
    {
        const int32 Phase=(FrameIndex/10)%13;
        const double Begin=FPlatformTime::Seconds();
        Step(Phase);
        ActionTimes.Add((FPlatformTime::Seconds()-Begin)*1000.0);
        ActionPhases.Add(Phase);
        const auto* Record=domain::ResolveBuilding(Sim->State,Controller.InspectionSelection());
        bool Correct=true;
        if (Phase==0 || Phase==2) Correct=Record && Record->x_cm==2250 && Record->y_cm==2300;
        if (Phase==1) Correct=!Record;
        if (Phase==3 && Count>1) Correct=Record && Record->x_cm==1400 && Record->y_cm==2300;
        if (Phase==4) Correct=Controller.IsPlacing() && !Record;
        if (Phase==6) Correct=Controller.Placement().yaw_degrees==15 && Controller.PlacementStatus().ok;
        if (Phase==8) Correct=int32(Sim->State.buildings.size())==Count && !Controller.PlacementStatus().ok;
        if (Phase==10) Correct=int32(Sim->State.buildings.size())==Count+1;
        if (Phase==11) Correct=!Controller.IsPlacing();
        if (Phase==12) Correct=int32(Sim->State.buildings.size())==Count && Sim->State.speed==0;
        if (!Correct)
        {
            bValid=false;
            UE_LOG(LogTemp,Error,TEXT("SHOEN_PROFILE replay phase %d failed at iteration %d"),Phase,FrameIndex/130);
            Finish(); FPlatformMisc::RequestExit(false); return true;
        }
    }
    else if (Controller.IsPlacing())
    {
        ShoenProfile::FActionScope Action(TEXT("preview"));
        Controller.RefreshPlacement(true);
    }
    ++FrameIndex;
    return true;
}
void FInteractionReplay::Finish()
{
    if (!bConfigured || bFinished) return;
    bFinished=true;
    if (ShoenProfile::IsCapturing()) ShoenProfile::Stop();
    ShoenProfile::SetReplaySource(false);
    if (bStarted)
    {
        Controller.CancelPlacement();
        Controller.GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>()->EndProfilingFixture();
        Controller.RefreshInspection();
    }
    if (!Output.IsEmpty() && FrameTimes.Num())
    {
        auto Root=MakeShared<FJsonObject>();
        Root->SetNumberField(TEXT("schema_version"),1);
        Root->SetStringField(TEXT("source"),TEXT("replay_frame_pacing"));
        Root->SetBoolField(TEXT("instrumentation_enabled"),!bDisabled);
        Root->SetNumberField(TEXT("buildings"),Count);
        Root->SetNumberField(TEXT("iterations"),Iterations);
        Root->SetBoolField(TEXT("completed"),bValid && FrameIndex>=Iterations*130);
        TArray<TSharedPtr<FJsonValue>> Values;
        for (double Ms : FrameTimes) Values.Add(MakeShared<FJsonValueNumber>(Ms));
        Root->SetArrayField(TEXT("frame_times_ms"),Values);
        TArray<TSharedPtr<FJsonValue>> Actions;
        for (int32 I=0; I<ActionTimes.Num(); ++I)
        {
            auto Action=MakeShared<FJsonObject>();
            Action->SetNumberField(TEXT("phase"),ActionPhases[I]);
            Action->SetNumberField(TEXT("duration_ms"),ActionTimes[I]);
            Actions.Add(MakeShared<FJsonValueObject>(Action));
        }
        Root->SetArrayField(TEXT("actions"),Actions);
        FString Json; auto Writer=TJsonWriterFactory<>::Create(&Json);
        FJsonSerializer::Serialize(Root,Writer);
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(Output),true);
        if (!FFileHelper::SaveStringToFile(Json,*(Output+TEXT(".frames.json"))))
        { UE_LOG(LogTemp,Error,TEXT("SHOEN_PROFILE frame export failed")); }
    }
}
