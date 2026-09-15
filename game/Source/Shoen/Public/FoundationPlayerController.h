#pragma once
#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "domain/BuildingTypes.h"
#include "FoundationPlayerController.generated.h"

UCLASS()
class SHOEN_API AFoundationPlayerController : public APlayerController
{
    GENERATED_BODY()
public:
    AFoundationPlayerController();
    virtual void BeginPlay() override;
    virtual void PlayerTick(float DeltaTime) override;
    virtual bool InputKey(const FInputKeyEventArgs& Params) override;
    TSet<uint64> Selected;
    bool bMouseDiagnostics = false;
    bool GroundAtCursor(FVector& Point) const;
    bool bSelecting = false;
    FVector2D SelectionStart;
    FVector2D SelectionEnd;
    void SelectAll();
    void BeginPlacement();
    void CancelPlacement();
    void RotatePlacement(int32 Direction);
    void ConfirmPlacement();
    bool IsPlacing() const { return bPlacing; }
    bool HasPlacementPoint() const { return bHasPlacementPoint; }
    const domain::PlacementCommand& Placement() const { return PendingPlacement; }
    const domain::PlacementResult& PlacementStatus() const { return PreviewResult; }
private:
    friend class FShoenPlacementInput;
    bool bPlacing = false;
    bool bHasPlacementPoint = false;
    uint64 SeenWorldGeneration = MAX_uint64;
    uint64 LastConfirmFrame = MAX_uint64;
    domain::PlacementCommand PendingPlacement;
    domain::PlacementResult PreviewResult;
    bool bPreviewCached = false;
    uint64 PreviewRevision = 0;
    int32 PreviewX = 0, PreviewY = 0, PreviewYaw = 0;
    void UpdatePlacement(bool bCanReadCursor);
    void RefreshPlacement();
private:
    friend class FShoenSelectionProjectionFailure;
    float DiagnosticLogTime = 0;
    FVector MoveStart = FVector::ZeroVector;
    bool bOrdering = false;
    void FinishSelection();
};
