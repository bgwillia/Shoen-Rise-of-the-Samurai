#pragma once
#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
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
private:
    friend class FShoenSelectionProjectionFailure;
    float DiagnosticLogTime = 0;
    FVector MoveStart = FVector::ZeroVector;
    bool bOrdering = false;
    void FinishSelection();
};
