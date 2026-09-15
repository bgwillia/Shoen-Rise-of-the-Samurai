#include "FoundationPlayerController.h"
#include "ShoenSimulationSubsystem.h"
#include "FoundationGameMode.h"
#include "SettlementView.h"
#include "domain/Buildings.h"
#include "Engine/GameInstance.h"
#include "InputCoreTypes.h"
#include "domain/Battle.h"
#include <algorithm>
#include "UnrealClient.h"
#include "Misc/Paths.h"
#include "GameFramework/HUD.h"
#include "FoundationCursorDiagnostics.h"

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
void AFoundationPlayerController::BeginPlacement()
{
    auto* Sim=GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    if (!Sim || !Sim->IsSettlement() || Sim->BuildingDefinitions().empty())
    {
        if (Sim) Sim->Message=TEXT("N: open the settlement fixture before choosing a building.");
        return;
    }
    CancelPlacement();
    PendingPlacement={};
    PendingPlacement.definition_id=Sim->BuildingDefinitions().begin()->first;
    PendingPlacement.settlement_id=Sim->State.build_areas.begin()->first;
    for (const auto& [Id,District] : Sim->State.districts)
        if (District.settlement_id==PendingPlacement.settlement_id) { PendingPlacement.district_id=Id; break; }
    bPlacing=true;
    SeenWorldGeneration=Sim->WorldGeneration;
    Sim->Message=TEXT("Move to ground, [ / ] rotate, click or Enter to build. Esc / right click cancel.");
}
void AFoundationPlayerController::CancelPlacement()
{
    bPlacing=false; bHasPlacementPoint=false; bSelecting=false; bOrdering=false;
    PreviewResult={}; bPreviewCached=false;
    if (auto* Mode=Cast<AFoundationGameMode>(GetWorld()->GetAuthGameMode()))
        if (auto* View=Mode->SettlementPresentation()) View->HidePreview();
}
void AFoundationPlayerController::RefreshPlacement()
{
    if (!bPlacing || !bHasPlacementPoint) return;
    auto* Sim=GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    if (!bPreviewCached || PreviewRevision!=Sim->State.revision || PreviewX!=PendingPlacement.x_cm || PreviewY!=PendingPlacement.y_cm || PreviewYaw!=PendingPlacement.yaw_degrees)
    {
        PreviewResult=Sim->PreviewBuilding(PendingPlacement);
        PreviewRevision=Sim->State.revision;
        PreviewX=PendingPlacement.x_cm; PreviewY=PendingPlacement.y_cm; PreviewYaw=PendingPlacement.yaw_degrees;
        bPreviewCached=true;
    }
    const auto It=Sim->BuildingDefinitions().find(PendingPlacement.definition_id);
    if (It==Sim->BuildingDefinitions().end()) { CancelPlacement(); return; }
    if (auto* Mode=Cast<AFoundationGameMode>(GetWorld()->GetAuthGameMode()))
        if (auto* View=Mode->SettlementPresentation())
            View->SetPreview(It->second,PendingPlacement,PreviewResult.ground_z_cm,PreviewResult.ok);
}
void AFoundationPlayerController::UpdatePlacement(bool bCanReadCursor)
{
    if (!bPlacing) return;
    if (bCanReadCursor)
    {
        auto* Sim=GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
        FVector Origin,Direction;
        if (!DeprojectMousePositionToWorld(Origin,Direction))
        {
            bHasPlacementPoint=false;
            if (auto* Mode=Cast<AFoundationGameMode>(GetWorld()->GetAuthGameMode()))
                if (auto* View=Mode->SettlementPresentation()) View->HidePreview();
            return;
        }
        domain::Point3 Hit;
        const auto Area=Sim->State.build_areas.find(PendingPlacement.settlement_id);
        bool Found=Area!=Sim->State.build_areas.end() && domain::RaycastBuildArea(Area->second,
            {Origin.X,Origin.Y,Origin.Z},{Direction.X,Direction.Y,Direction.Z},Hit);
        if (!Found)
        {
            FVector Ground;
            Found=GroundAtCursor(Ground);
            if (Found) Hit={Ground.X,Ground.Y,Ground.Z};
        }
        bHasPlacementPoint=Found;
        if (Found)
        {
            PendingPlacement.x_cm=FMath::RoundToInt(FMath::Clamp(Hit.x,-1.e9,1.e9));
            PendingPlacement.y_cm=FMath::RoundToInt(FMath::Clamp(Hit.y,-1.e9,1.e9));
        }
    }
    RefreshPlacement();
}
void AFoundationPlayerController::RotatePlacement(int32 Direction)
{
    if (!bPlacing) return;
    auto* Sim=GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    const auto It=Sim->BuildingDefinitions().find(PendingPlacement.definition_id);
    if (It==Sim->BuildingDefinitions().end()) return;
    PendingPlacement.yaw_degrees=(PendingPlacement.yaw_degrees+Direction*It->second.rotation_step_degrees+360)%360;
    RefreshPlacement();
}
void AFoundationPlayerController::ConfirmPlacement()
{
    auto* Sim=GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    if (!bPlacing || !bHasPlacementPoint || SeenWorldGeneration!=Sim->WorldGeneration || LastConfirmFrame==GFrameCounter) return;
    LastConfirmFrame=GFrameCounter;
    auto Command=PendingPlacement;
    Command.transaction_id=Sim->State.next_transaction_id;
    Sim->PlaceBuilding(Command);
    RefreshPlacement();
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
    float MouseX = 0, MouseY = 0;
    if (!GetMousePosition(MouseX,MouseY))
    {
        bSelecting = false;
        return;
    }
    auto* Sim = GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    const bool Box = FVector2D::Distance(SelectionStart, SelectionEnd) > 8;
    const FBox2D Rect(SelectionStart.ComponentMin(SelectionEnd), SelectionStart.ComponentMax(SelectionEnd));
    FVector Ground = FVector::ZeroVector;
    if (!Box && !GroundAtCursor(Ground))
    {
        bSelecting = false;
        return;
    }
    if (!IsInputKeyDown(EKeys::LeftShift) && !IsInputKeyDown(EKeys::RightShift)) Selected.Reset();
    uint64 ClosestId = 0;
    double Closest = 850 * 850;
    for (const auto& [Id, F] : Sim->State.formations)
    {
        if (domain::ActiveFormationCount(Sim->State, Id) == 0) continue;
        FVector2D Screen;
        const FVector Center(F.x,F.y,100);
        if (Box && ProjectWorldLocationToScreen(Center, Screen) && Rect.IsInside(Screen)) Selected.Add(Id);
        if (!Box)
        {
            const double Dist = FVector::DistSquared2D(Center, Ground);
            if (Dist < Closest) { Closest = Dist; ClosestId = Id; }
        }
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
    const bool bHasMousePosition = GetMousePosition(MX, MY);
    if (bMouseDiagnostics && WasInputKeyJustPressed(EKeys::LeftMouseButton)) UE_LOG(LogTemp,Display,TEXT("SHOEN_CLICK %.1f %.1f"),MX,MY);
    int32 ViewWidth=0,ViewHeight=0; GetViewportSize(ViewWidth,ViewHeight);
    const bool OverPanel = MX < 410 || MY < 66 || MY >= ViewHeight-54;
    if (SeenWorldGeneration!=Sim->WorldGeneration)
    {
        CancelPlacement(); Selected.Reset(); SeenWorldGeneration=Sim->WorldGeneration;
    }
    if (WasInputKeyJustPressed(EKeys::B)) { if (bPlacing) CancelPlacement(); else BeginPlacement(); }
    const bool bPlacementGesture=bPlacing;
    if (bPlacing)
    {
        UpdatePlacement(bHasMousePosition && !OverPanel);
        if (WasInputKeyJustPressed(EKeys::LeftBracket)) RotatePlacement(-1);
        if (WasInputKeyJustPressed(EKeys::RightBracket)) RotatePlacement(1);
        if (WasInputKeyJustPressed(EKeys::Escape) || WasInputKeyJustPressed(EKeys::RightMouseButton)) CancelPlacement();
        else if (WasInputKeyJustPressed(EKeys::Enter) || (bHasMousePosition && !OverPanel && WasInputKeyJustPressed(EKeys::LeftMouseButton))) ConfirmPlacement();
    }
    if (bHasMousePosition) SelectionEnd = FVector2D(MX,MY);
    if (!bPlacementGesture && bHasMousePosition && WasInputKeyJustPressed(EKeys::LeftMouseButton) && !OverPanel)
    { SelectionStart = SelectionEnd; bSelecting = true; }
    if (bSelecting && WasInputKeyJustReleased(EKeys::LeftMouseButton)) FinishSelection();
    if (!bPlacementGesture && bHasMousePosition && WasInputKeyJustPressed(EKeys::RightMouseButton) && !OverPanel) bOrdering = GroundAtCursor(MoveStart);
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
    if (bMouseDiagnostics && (DiagnosticLogTime -= Dt) <= 0)
    {
        DiagnosticLogTime = 1;
        for (const auto& Line : ReadFoundationCursorDiagnostics(*this).Lines)
            UE_LOG(LogTemp,Display,TEXT("SHOEN_CURSOR %s"),*Line);
    }
    if (auto* Mode = Cast<AFoundationGameMode>(GetWorld()->GetAuthGameMode()))
    {
        if (WasInputKeyJustPressed(EKeys::N)) Mode->NewSettlement();
        if (WasInputKeyJustPressed(EKeys::R)) Mode->NewScenario(0);
        if (WasInputKeyJustPressed(EKeys::Z)) Mode->NewScenario(1000);
        if (WasInputKeyJustPressed(EKeys::X)) Mode->NewScenario(4000);
        if (WasInputKeyJustPressed(EKeys::C)) Mode->NewScenario(8000);
        if (WasInputKeyJustPressed(EKeys::V)) Mode->NewScenario(20000);
    }
    if (WasInputKeyJustPressed(EKeys::F10))
        FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir() / TEXT("Screenshots/Foundation.png"),true,true);
    if (!Sim->IsSettlement())
    {
        if (WasInputKeyJustPressed(EKeys::M)) Sim->MobilizeProof();
        if (WasInputKeyJustPressed(EKeys::O)) Sim->ResolveProof();
        if (WasInputKeyJustPressed(EKeys::BackSpace)) Sim->DemobilizeProof();
    }
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
