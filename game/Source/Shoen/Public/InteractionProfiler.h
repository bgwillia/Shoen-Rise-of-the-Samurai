#pragma once
#include "CoreMinimal.h"
#include "InputCoreTypes.h"
#include "Engine/EngineBaseTypes.h"

class UWorld;
class FJsonObject;

// Opt-in diagnostics only. All gameplay-facing calls are game-thread calls.
namespace ShoenProfile
{
enum class EVisualChannel : uint8 { Selection,Mode,Rotation,Preview,Buildings,Message,Count };
bool Start(UWorld* World,const FString& OutputPath);
bool Stop();
bool IsCapturing();
void SetSamplingEnabled(bool bEnabled);
void SetReplaySource(bool bReplay);
void ControllerInput(const FKey& Key,EInputEvent Event);
void SetSceneBuildingCount(int32 Count);
uint64 CurrentEvent();
void Mark(FName Stage,uint64 Event=0);
void SetKind(FName Kind,uint64 Event=0);
void SetEntity(uint64 Entity,uint64 Event=0);
void VisualReady(uint64 Event,EVisualChannel Channel,bool NeedsScene,bool NeedsHUD);
void Invalidate(EVisualChannel Channel);
void ExpectMessage(const FString& Message);
void CaptureHud(const FString& DisplayedMessage=FString());
void Frame(float DeltaSeconds);

class FActionScope
{
public:
    FActionScope(FName Kind,const FKey& Trigger=FKey());
    ~FActionScope();
    FActionScope(const FActionScope&)=delete;
    FActionScope& operator=(const FActionScope&)=delete;
private:
    uint64 Event=0;
    uint64 Session=0;
    bool bOwns=false;
};

class FUseEventScope
{
public:
    explicit FUseEventScope(uint64 Event);
    ~FUseEventScope();
    FUseEventScope(const FUseEventScope&)=delete;
    FUseEventScope& operator=(const FUseEventScope&)=delete;
private:
    uint64 Previous=0;
    uint64 Session=0;
};

#if WITH_DEV_AUTOMATION_TESTS
// Exercises the same bounded collector and frame join without a rendered window.
namespace Testing
{
bool Begin(int32 EventLimit=8,int32 FrameLimit=8);
void End();
void SlateInput(const FKey& Key,double AgeMs=0);
bool SceneSnapshot(uint64 Frame);
void SceneRendered(uint64 Frame);
bool HudSnapshot(uint64 Frame);
void Backbuffer(uint64 Frame);
int32 QueuedObservations();
TSharedPtr<FJsonObject> Snapshot();
}
#endif
}
