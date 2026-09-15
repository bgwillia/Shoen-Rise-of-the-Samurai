#pragma once
#include "CoreMinimal.h"

class APlayerController;

// Read-only, opt-in evidence. Never feeds coordinates back into the input system.
struct FFoundationCursorDiagnostics
{
    FVector2D Viewport = FVector2D::ZeroVector;
    FVector2D NativeViewport = FVector2D::ZeroVector;
    bool bHasNative = false;
    TArray<FString> Lines;
};

FFoundationCursorDiagnostics ReadFoundationCursorDiagnostics(const APlayerController& Controller);
#if PLATFORM_MAC
FVector2D ReadFoundationMacCursor(FVector2D& Cocoa, double& BackingScale, uint32& Buttons);
#endif
