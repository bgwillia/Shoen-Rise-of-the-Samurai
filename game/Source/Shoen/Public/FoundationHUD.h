#pragma once
#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "FoundationHUD.generated.h"
namespace domain { struct Building; struct BuildingDefinition; }
UCLASS()
class SHOEN_API AFoundationHUD : public AHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
    virtual void NotifyHitBoxClick(FName Name) override;
private:
    void Label(const FString& Text, float X, float Y, FLinearColor Color = FLinearColor::White, float Scale = 1.0f);
    void Button(FName Id, const FString& Text, float X, float Y, float Width = 175);
    void BuildingInspector(const domain::Building& Instance, const domain::BuildingDefinition* Definition);
};
