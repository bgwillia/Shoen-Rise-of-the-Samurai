#pragma once
#include "CoreMinimal.h"

class AFoundationPlayerController;

// Explicit development command-line driver. It calls gameplay paths without
// synthesizing operating-system input; all samples are labelled replay.
class FInteractionReplay
{
public:
    explicit FInteractionReplay(AFoundationPlayerController& InController);
    bool Tick(float DeltaSeconds);
    void Finish();
private:
    AFoundationPlayerController& Controller;
    int32 Count = 0, Iterations = 30, Warmup = 120, FrameIndex = 0;
    bool bConfigured = false, bStarted = false, bFinished = false, bDisabled = false;
    FString Output;
    TArray<double> FrameTimes;
    TArray<double> ActionTimes;
    TArray<int32> ActionPhases;
    bool bValid = true;
    double LastFrameTime = 0;
    void Step(int32 Phase);
    void Pick(double X, double Y);
    void Point(int32 X, int32 Y, int32 Yaw);
};
