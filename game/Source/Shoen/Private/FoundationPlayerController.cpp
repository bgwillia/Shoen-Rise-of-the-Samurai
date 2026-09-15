#include "FoundationPlayerController.h"
#include "ShoenSimulationSubsystem.h"
#include "FoundationGameMode.h"
#include "Engine/GameInstance.h"
#include "InputCoreTypes.h"
#include "domain/Battle.h"
#include <algorithm>
#include "UnrealClient.h"
#include "Misc/Paths.h"
#include "GameFramework/HUD.h"

AFoundationPlayerController::AFoundationPlayerController()
{
    bShowMouseCursor = true;
    bEnableClickEvents = true;
}
void AFoundationPlayerController::BeginPlay()
{
    Super::BeginPlay();
    FInputModeGameAndUI Mode;
    Mode.SetHideCursorDuringCapture(false);
    Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    SetInputMode(Mode);
}
bool AFoundationPlayerController::InputKey(const FInputKeyEventArgs& Params)
{
    if (bMouseDiagnostics && Params.Key == EKeys::LeftMouseButton)
    {
        float X=0,Y=0; GetMousePosition(X,Y);
        UE_LOG(LogTemp,Display,TEXT("SHOEN_INPUT event=%d mouse=%.1f,%.1f click=%d hud=%d hit=%d"),int32(Params.Event),X,Y,bEnableClickEvents,GetHUD()!=nullptr,GetHUD() && GetHUD()->GetHitBoxAtCoordinates(FVector2D(X,Y),true)!=nullptr);
    }
    return Super::InputKey(Params);
}
bool AFoundationPlayerController::GroundAtCursor(FVector& Point) const
{
    FVector Origin, Direction;
    if (!DeprojectMousePositionToWorld(Origin, Direction) || FMath::Abs(Direction.Z) < 0.0001) return false;
    const double T = -Origin.Z / Direction.Z;
    if (T < 0) return false;
    Point = Origin + Direction * T;
    return true;
}
void AFoundationPlayerController::SelectAll()
{
    auto* Sim = GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    Selected.Reset();
    for (const auto& [Id, F] : Sim->State.formations)
        if (domain::ActiveFormationCount(Sim->State, Id) > 0) Selected.Add(Id);
}
void AFoundationPlayerController::FinishSelection()
{
    auto* Sim = GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    if (!IsInputKeyDown(EKeys::LeftShift) && !IsInputKeyDown(EKeys::RightShift)) Selected.Reset();
    const bool Box = FVector2D::Distance(SelectionStart, SelectionEnd) > 8;
    const FBox2D Rect(SelectionStart.ComponentMin(SelectionEnd), SelectionStart.ComponentMax(SelectionEnd));
    FVector Ground;
    GroundAtCursor(Ground);
    uint64 ClosestId = 0;
    double Closest = 850 * 850;
    for (const auto& [Id, F] : Sim->State.formations)
    {
        if (domain::ActiveFormationCount(Sim->State, Id) == 0) continue;
        FVector2D Screen;
        const FVector Center(F.x,F.y,100);
        if (Box && ProjectWorldLocationToScreen(Center, Screen) && Rect.IsInside(Screen)) Selected.Add(Id);
        const double Dist = FVector::DistSquared2D(Center, Ground);
        if (!Box && Dist < Closest) { Closest = Dist; ClosestId = Id; }
    }
    if (ClosestId) Selected.Add(ClosestId);
    bSelecting = false;
}
void AFoundationPlayerController::PlayerTick(float Dt)
{
    Super::PlayerTick(Dt);
    auto* Sim = GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    if (!Sim) return;
    float MX = 0, MY = 0;
    GetMousePosition(MX, MY);
    if (bMouseDiagnostics && WasInputKeyJustPressed(EKeys::LeftMouseButton)) UE_LOG(LogTemp,Display,TEXT("SHOEN_CLICK %.1f %.1f"),MX,MY);
    const bool OverPanel = MX < 410 || MY < 66;
    SelectionEnd = FVector2D(MX,MY);
    if (WasInputKeyJustPressed(EKeys::LeftMouseButton) && !OverPanel)
    { SelectionStart = SelectionEnd; bSelecting = true; }
    if (bSelecting && WasInputKeyJustReleased(EKeys::LeftMouseButton)) FinishSelection();
    if (WasInputKeyJustPressed(EKeys::RightMouseButton) && !OverPanel) bOrdering = GroundAtCursor(MoveStart);
    if (bOrdering && WasInputKeyJustReleased(EKeys::RightMouseButton))
    {
        FVector End;
        if (GroundAtCursor(End) && Selected.Num() > 0)
        {
            std::vector<domain::EntityId> Ids;
            for (auto Id : Selected) Ids.push_back(Id);
            std::sort(Ids.begin(), Ids.end());
            const FVector Direction = End - MoveStart;
            const double Facing = Direction.Size2D() > 180 ? FMath::Atan2(Direction.Y,Direction.X) : Sim->State.formations.at(Ids.front()).facing;
            const auto Result = domain::IssueMove(Sim->State, Ids, MoveStart.X, MoveStart.Y, Facing);
            Sim->Message = Result.ok ? TEXT("Move order issued. Drag from a destination toward the desired facing.") : UTF8_TO_TCHAR(Result.error.c_str());
        }
        bOrdering = false;
    }
    if (WasInputKeyJustPressed(EKeys::SpaceBar)) Sim->SetGameSpeed(Sim->State.speed == 0 ? 1 : 0);
    if (WasInputKeyJustPressed(EKeys::F1)) Sim->SetGameSpeed(1);
    if (WasInputKeyJustPressed(EKeys::F2)) Sim->SetGameSpeed(3);
    if (WasInputKeyJustPressed(EKeys::F3)) Sim->SetGameSpeed(5);
    if (WasInputKeyJustPressed(EKeys::F4)) Sim->SetGameSpeed(10);
    if (WasInputKeyJustPressed(EKeys::F5)) Sim->Save();
    if (WasInputKeyJustPressed(EKeys::F9)) Sim->Load();
    if (WasInputKeyJustPressed(EKeys::F12)) bMouseDiagnostics = !bMouseDiagnostics;
    if (auto* Mode = Cast<AFoundationGameMode>(GetWorld()->GetAuthGameMode()))
    {
        if (WasInputKeyJustPressed(EKeys::R)) Mode->NewScenario(0);
        if (WasInputKeyJustPressed(EKeys::Z)) Mode->NewScenario(1000);
        if (WasInputKeyJustPressed(EKeys::X)) Mode->NewScenario(4000);
        if (WasInputKeyJustPressed(EKeys::C)) Mode->NewScenario(8000);
        if (WasInputKeyJustPressed(EKeys::V)) Mode->NewScenario(20000);
    }
    if (WasInputKeyJustPressed(EKeys::F10))
        FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir() / TEXT("Screenshots/Foundation.png"),true,true);
    if (WasInputKeyJustPressed(EKeys::M)) Sim->MobilizeProof();
    if (WasInputKeyJustPressed(EKeys::O)) Sim->ResolveProof();
    if (WasInputKeyJustPressed(EKeys::BackSpace)) Sim->DemobilizeProof();
    if (WasInputKeyJustPressed(EKeys::Escape)) { Selected.Reset(); bSelecting = false; bOrdering = false; }
    if (IsInputKeyDown(EKeys::LeftControl) && WasInputKeyJustPressed(EKeys::A)) SelectAll();
    const FKey Keys[] = { EKeys::One,EKeys::Two,EKeys::Three,EKeys::Four,EKeys::Five,EKeys::Six,EKeys::Seven,EKeys::Eight,EKeys::Nine };
    for (int32 Index=0; Index<9; ++Index)
    {
        if (!WasInputKeyJustPressed(Keys[Index])) continue;
        if (IsInputKeyDown(EKeys::LeftControl) || IsInputKeyDown(EKeys::RightControl))
        {
            std::vector<domain::EntityId> Ids;
            for (auto Id : Selected) Ids.push_back(Id);
            const auto R = domain::AssignGroup(Sim->State, Ids, uint8(Index+1));
            Sim->Message = R.ok ? FString::Printf(TEXT("Assigned %d formations to group %d."),Selected.Num(),Index+1) : UTF8_TO_TCHAR(R.error.c_str());
        }
        else
        {
            Selected.Reset();
            for (const auto& [Id,F] : Sim->State.formations)
                if (F.control_group == Index+1 && domain::ActiveFormationCount(Sim->State,Id)>0) Selected.Add(Id);
        }
    }
}
