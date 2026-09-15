#include "FoundationCursorDiagnostics.h"
#include "Mac/MacApplication.h"

FVector2D ReadFoundationMacCursor(FVector2D& Cocoa, double& BackingScale, uint32& Buttons)
{
    SCOPED_AUTORELEASE_POOL;
    const NSPoint Position = [NSEvent mouseLocation];
    Cocoa = FVector2D(Position.x, Position.y);
    BackingScale = 0;
    for (NSScreen* Screen in [NSScreen screens])
        if (NSPointInRect(Position, [Screen frame])) BackingScale = [Screen backingScaleFactor];
    Buttons = uint32([NSEvent pressedMouseButtons]);
    // Use the same documented screen-space conversion as the installed Mac backend.
    return FMacApplication::ConvertCocoaPositionToSlate(Position.x, Position.y);
}
