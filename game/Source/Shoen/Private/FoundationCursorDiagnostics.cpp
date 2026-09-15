#include "FoundationCursorDiagnostics.h"
#include "GameFramework/PlayerController.h"
#include "Engine/LocalPlayer.h"
#include "Engine/GameViewportClient.h"
#include "Slate/SceneViewport.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SViewport.h"
#include "Widgets/SWindow.h"

FFoundationCursorDiagnostics ReadFoundationCursorDiagnostics(const APlayerController& Controller)
{
    FFoundationCursorDiagnostics Result;
    float X = 0, Y = 0;
    const bool Valid = Controller.GetMousePosition(X,Y);
    Result.Viewport = FVector2D(X,Y);
    const ULocalPlayer* Player = Controller.GetLocalPlayer();
    FSceneViewport* Viewport = Player && Player->ViewportClient ? Player->ViewportClient->GetGameViewport() : nullptr;
    if (!Viewport || !FSlateApplication::IsInitialized()) return Result;
    auto& Slate = FSlateApplication::Get();
    const FGeometry& Geometry = Viewport->GetCachedGeometry();
    const FIntPoint Pixels = Viewport->GetSizeXY();
    const FVector2D LocalSize = Geometry.GetLocalSize();
    const FVector2D Origin = Geometry.LocalToAbsolute(FVector2D::ZeroVector);
    const FVector2D PixelScale = UE::Slate::Viewport::GetViewportLocalToPixelScale(Geometry,FVector2D(Pixels));
    const FVector2D SlatePosition = Slate.GetCursorPos();
    const FVector2D SlatePixel = Geometry.AbsoluteToLocal(SlatePosition) * PixelScale;
    Result.Lines.Add(FString::Printf(TEXT("RED viewport %.0f,%.0f valid=%d | Slate screen %.0f,%.0f -> pixel %.0f,%.0f"),X,Y,Valid,SlatePosition.X,SlatePosition.Y,SlatePixel.X,SlatePixel.Y));
#if PLATFORM_MAC
    FVector2D Cocoa;
    double BackingScale = 0;
    uint32 Buttons = 0;
    const FVector2D Native = ReadFoundationMacCursor(Cocoa,BackingScale,Buttons);
    Result.NativeViewport = Geometry.AbsoluteToLocal(Native) * PixelScale;
    Result.bHasNative = true;
    Result.Lines.Add(FString::Printf(TEXT("CYAN native %.0f,%.0f -> pixel %.0f,%.0f | Cocoa %.0f,%.0f backing=%.2f buttons=%u"),Native.X,Native.Y,Result.NativeViewport.X,Result.NativeViewport.Y,Cocoa.X,Cocoa.Y,BackingScale,Buttons));
#endif
    Result.Lines.Add(FString::Printf(TEXT("Viewport %dx%d | local %.0fx%.0f origin %.0f,%.0f | local-to-pixel %.2f,%.2f"),Pixels.X,Pixels.Y,LocalSize.X,LocalSize.Y,Origin.X,Origin.Y,PixelScale.X,PixelScale.Y));
    const auto Widget = Viewport->GetViewportWidget().Pin();
    const auto Window = Widget.IsValid() ? Slate.FindWidgetWindow(Widget.ToSharedRef()) : nullptr;
    if (Window.IsValid())
    {
        const FVector2D WindowPosition = Window->GetPositionInScreen();
        Result.Lines.Add(FString::Printf(TEXT("Window %.0f,%.0f dpi=%.2f app-scale=%.2f mode=%d | active=%d focus=%d capture=%d raw=%d"),WindowPosition.X,WindowPosition.Y,Window->GetDPIScaleFactor(),Slate.GetApplicationScale(),int32(Window->GetWindowMode()),Slate.IsActive(),Viewport->HasFocus(),Viewport->HasMouseCapture(),Slate.IsUsingHighPrecisionMouseMovment()));
    }
    return Result;
}
