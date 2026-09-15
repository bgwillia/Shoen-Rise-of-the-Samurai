#include "InteractionProfiler.h"
#include "Dom/JsonObject.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "UnrealClient.h"
#include "Misc/EngineVersion.h"
#include "Misc/App.h"
#include "HAL/PlatformProperties.h"
#include "HAL/PlatformMisc.h"
#include "Framework/Application/IInputProcessor.h"
#include "Framework/Application/SlateApplication.h"
#include "HAL/FileManager.h"
#include "Misc/DateTime.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Rendering/SlateRenderer.h"
#include "RenderingThread.h"
#include "SceneView.h"
#include "SceneViewExtension.h"
#include "Serialization/JsonSerializer.h"
#include "Containers/Queue.h"
#include <atomic>

namespace ShoenProfile
{
namespace
{
constexpr int32 ChannelCount=static_cast<int32>(EVisualChannel::Count);
constexpr int32 StageLimit=32, InputLimit=64, RenderHistory=64, ObservationLimit=256;
struct FTokens { uint64 Id[ChannelCount]{}; uint64 Revision[ChannelCount]{}; };
struct FStage { FName Name; uint64 Cycles=0,Frame=0; };
struct FInput
{
    FKey Key; EInputEvent Type=IE_Pressed;
    uint64 Constructed=0,Receipt=0,InputFrame=0,Controller=0,ControllerFrame=0;
    bool Consumed=false;
};
struct FEvent
{
    uint64 Id=0,Entity=0;
    FName Kind;
    FString Source=TEXT("frame_poll"),Path=TEXT("frame_poll"),ExpectedMessage;
    bool HasExpectedMessage=false;
    FInput Input;
    int32 Buildings=0;
    TArray<FStage,TInlineAllocator<StageLimit>> Stages;
    uint8 Needs[ChannelCount]{};
    uint64 Revision[ChannelCount]{};
    uint64 Ready=0,ReadyFrame=0,Backbuffer=0,RenderFrame=0,SceneRenderCycles=0;
    bool Superseded=false,CacheHit=false,CacheEvaluated=false;
};
struct FFrameTime { int32 Buildings; uint64 Frame; float Milliseconds; };
struct FRenderFrame
{
    uint64 Frame=MAX_uint64,SceneRenderCycles=0;
    FTokens Scene,HUD;
    bool HasScene=false,SceneRendered=false,HasHUD=false;
};
struct FObservation { FRenderFrame Snapshot; uint64 Cycles=0; };
struct FSession
{
    uint64 Serial=0,Start=0,FirstId=0,Current=0,NextRevision=0;
    FString Path,Id,Utc;
    bool Sampling=true,Replay=false,Testing=false;
    int32 Buildings=0,EventLimit=8192,FrameLimit=65536,Width=1,Height=1;
    uint64 DroppedEvents=0,DroppedStages=0,DroppedFrames=0,DroppedInputs=0;
    TArray<FEvent> Events;
    TArray<FFrameTime> Frames;
    TArray<FInput,TInlineAllocator<InputLimit>> Inputs;
    FTokens Tokens,PendingHUD;
    uint64 PendingHUDFrame=MAX_uint64;
    TWeakObjectPtr<UGameViewportClient> Viewport;
    const FRenderTarget* Target=nullptr;
    const SWindow* Window=nullptr; // Identity only; never dereferenced on RT.
    TSharedPtr<IInputProcessor> InputObserver;
    TSharedPtr<ISceneViewExtension,ESPMode::ThreadSafe> Extension;
    FSlateRenderer* Renderer=nullptr;
    FDelegateHandle DrawnHandle,BackbufferHandle;
    // These fields are RT-only; observations cross back through a bounded queue.
    FRenderFrame RenderFrames[RenderHistory];
    TQueue<FObservation,EQueueMode::Mpsc> Observations;
    std::atomic<int32> Queued{0};
    std::atomic<uint64> DroppedRender{0};
    std::atomic<bool> Observing{true};
};
using FSessionPtr=TSharedPtr<FSession,ESPMode::ThreadSafe>;
using FSessionWeak=TWeakPtr<FSession,ESPMode::ThreadSafe>;
FSessionPtr Active;
uint64 NextSerial=0,NextId=0;
bool Capturing=false;
uint64 Now() { return FPlatformTime::Cycles64(); }
bool Sampling() { return Capturing && Active.IsValid() && Active->Sampling; }
FEvent* Find(FSession& S,uint64 Id)
{
    if (!Id || Id<S.FirstId) return nullptr;
    const uint64 Index=Id-S.FirstId;
    return Index<static_cast<uint64>(S.Events.Num()) && S.Events[Index].Id==Id ? &S.Events[Index] : nullptr;
}
bool HasTokens(const FTokens& Tokens)
{
    for (uint64 Id:Tokens.Id) if (Id) return true;
    return false;
}
bool NeedsPass(FSession& S,uint8 Pass)
{
    for (int32 I=0;I<ChannelCount;++I)
        if (const auto* E=Find(S,S.Tokens.Id[I]))
            if (!E->Backbuffer && (E->Needs[I]&Pass) && E->Revision[I]==S.Tokens.Revision[I]) return true;
    return false;
}
void Supersede(FSession& S,uint64 Id) { if (auto* E=Find(S,Id)) E->Superseded=true; }
void Stage(FSession& S,FEvent& E,FName Name)
{
    for (const auto& Existing:E.Stages) if (Existing.Name==Name) return;
    if (E.Stages.Num()==StageLimit) { ++S.DroppedStages; return; }
    E.Stages.Add({Name,Now(),GFrameCounter});
    if (Name==TEXT("preview_cached")) E.CacheHit=true;
    if (Name==TEXT("preview_validation_begin")) E.CacheEvaluated=true;
    if (Name==TEXT("hud_hitbox") || Name==TEXT("ui_hit_processed")) E.Path=TEXT("hud_hitbox");
}
FRenderFrame& RenderSlot(FSession& S,uint64 Frame)
{
    auto& Slot=S.RenderFrames[Frame%RenderHistory];
    if (Slot.Frame!=Frame) { Slot=FRenderFrame{}; Slot.Frame=Frame; }
    return Slot;
}
void StoreScene(FSession& S,uint64 Frame,const FTokens& Tokens)
{
    auto& Slot=RenderSlot(S,Frame); Slot.Scene=Tokens; Slot.HasScene=true;
}
void StoreHUD(FSession& S,uint64 Frame,const FTokens& Tokens)
{
    auto& Slot=RenderSlot(S,Frame); Slot.HUD=Tokens; Slot.HasHUD=true;
}
void Rendered(FSession& S,uint64 Frame)
{
    auto& Slot=S.RenderFrames[Frame%RenderHistory];
    if (Slot.Frame==Frame && Slot.HasScene) { Slot.SceneRendered=true; Slot.SceneRenderCycles=Now(); }
}
void Backbuffer(FSession& S,uint64 Frame)
{
    const auto& Slot=S.RenderFrames[Frame%RenderHistory];
    if (Slot.Frame!=Frame || !S.Observing.load() || (!HasTokens(Slot.Scene) && !HasTokens(Slot.HUD))) return;
    if (S.Queued.fetch_add(1)>=ObservationLimit)
    { S.Queued.fetch_sub(1); S.DroppedRender.fetch_add(1); return; }
    S.Observations.Enqueue({Slot,Now()});
}
void Drain(FSession& S)
{
    FObservation O;
    while (S.Observations.Dequeue(O))
    {
        S.Queued.fetch_sub(1);
        uint64 Candidates[ChannelCount*2]{};
        for (int32 I=0;I<ChannelCount;++I) { Candidates[I]=O.Snapshot.Scene.Id[I]; Candidates[I+ChannelCount]=O.Snapshot.HUD.Id[I]; }
        for (uint64 Id:Candidates)
        {
            auto* E=Find(S,Id);
            if (!E || E->Backbuffer || !E->Ready) continue;
            bool Matches=true;
            for (int32 I=0;I<ChannelCount;++I)
            {
                if ((E->Needs[I]&1) && (!O.Snapshot.HasScene || !O.Snapshot.SceneRendered || O.Snapshot.Scene.Id[I]!=Id || O.Snapshot.Scene.Revision[I]!=E->Revision[I])) Matches=false;
                if ((E->Needs[I]&2) && (!O.Snapshot.HasHUD || O.Snapshot.HUD.Id[I]!=Id || O.Snapshot.HUD.Revision[I]!=E->Revision[I])) Matches=false;
            }
            if (Matches && O.Cycles>=E->Ready)
            {
                E->Backbuffer=O.Cycles; E->RenderFrame=O.Snapshot.Frame; E->SceneRenderCycles=O.Snapshot.SceneRenderCycles;
                // Retire only this observed revision. Newer GT requests and queued
                // immutable snapshots remain independent of this idle-work gate.
                for (int32 I=0;I<ChannelCount;++I)
                    if (S.Tokens.Id[I]==Id && S.Tokens.Revision[I]==E->Revision[I])
                    { S.Tokens.Id[I]=0; S.Tokens.Revision[I]=0; }
            }
        }
    }
}
bool Fresh(const FInput& Input,uint64 Time)
{
    return !Input.Consumed && Input.Receipt && Time>=Input.Receipt &&
        FPlatformTime::ToSeconds64(Time-Input.Receipt)<=.250 &&
        GFrameCounter>=Input.InputFrame && GFrameCounter-Input.InputFrame<=3;
}
void RecordInput(FSession& S,const FKey& Key,EInputEvent Type,uint64 Constructed,uint64 Receipt)
{
    FInput I; I.Key=Key; I.Type=Type; I.Constructed=Constructed; I.Receipt=Receipt; I.InputFrame=GFrameCounter;
    // Preview uses the latest pointer position; intermediate motion is not a lost action.
    if (Key==EKeys::MouseX)
        for (int32 Index=S.Inputs.Num()-1;Index>=0;--Index)
            if (S.Inputs[Index].Key==EKeys::MouseX) { S.Inputs[Index]=I; return; }
    if (S.Inputs.Num()==InputLimit)
    {
        if (S.Inputs[0].Key!=EKeys::MouseX && Fresh(S.Inputs[0],Receipt)) ++S.DroppedInputs;
        S.Inputs.RemoveAt(0,1,EAllowShrinking::No);
    }
    S.Inputs.Add(I);
}
class FPassiveInput final:public IInputProcessor
{
    FSessionWeak Session;
    void Record(FSlateApplication& App,const FInputEvent& Input,const FKey& Key,EInputEvent Type)
    {
        const auto S=Session.Pin();
        if (!S || !S->Sampling || !Capturing || App.GetActiveTopLevelWindow().Get()!=S->Window) return;
        RecordInput(*S,Key,Type,Input.GetEventTimestamp(),Now());
    }
public:
    explicit FPassiveInput(FSessionWeak In):Session(In) {}
    virtual void Tick(float,FSlateApplication&,TSharedRef<ICursor>) override {}
    virtual bool HandleKeyDownEvent(FSlateApplication& A,const FKeyEvent& E) override { Record(A,E,E.GetKey(),IE_Pressed); return false; }
    virtual bool HandleMouseButtonDownEvent(FSlateApplication& A,const FPointerEvent& E) override { Record(A,E,E.GetEffectingButton(),IE_Pressed); return false; }
    virtual bool HandleMouseButtonDoubleClickEvent(FSlateApplication& A,const FPointerEvent& E) override { Record(A,E,E.GetEffectingButton(),IE_DoubleClick); return false; }
    virtual bool HandleMouseMoveEvent(FSlateApplication& A,const FPointerEvent& E) override { Record(A,E,EKeys::MouseX,IE_Axis); return false; }
    virtual const TCHAR* GetDebugName() const override { return TEXT("ShoenInteractionProfiler"); }
};
class FViewObserver final:public FWorldSceneViewExtension
{
    FSessionWeak Session;
    const FRenderTarget* Target;
public:
    FViewObserver(const FAutoRegister& Auto,UWorld* World,FSessionWeak In,const FRenderTarget* InTarget)
        :FWorldSceneViewExtension(Auto,World),Session(In),Target(InTarget) {}
    virtual void BeginRenderViewFamily(FSceneViewFamily& Family) override
    {
        const auto S=Session.Pin();
        if (!S || !Capturing || Family.RenderTarget!=Target || !NeedsPass(*S,1)) return;
        const auto Tokens=S->Tokens; const uint64 Frame=Family.FrameCounter;
        ENQUEUE_RENDER_COMMAND(ShoenProfileScene)([S,Tokens,Frame](FRHICommandListImmediate&) { StoreScene(*S,Frame,Tokens); });
    }
    virtual void PreRenderViewFamily_RenderThread(FRDGBuilder&,FSceneViewFamily& Family) override
    {
        const auto S=Session.Pin();
        if (S && Family.RenderTarget==Target) Rendered(*S,Family.FrameCounter);
    }
};
FSessionPtr NewSession(int32 Events,int32 Frames)
{
    auto S=MakeShared<FSession,ESPMode::ThreadSafe>();
    S->Serial=++NextSerial; S->Start=Now(); S->FirstId=NextId+1;
    S->Id=FGuid::NewGuid().ToString(EGuidFormats::DigitsWithHyphens);
    S->Utc=FDateTime::UtcNow().ToIso8601();
    S->EventLimit=FMath::Max(1,Events); S->FrameLimit=FMath::Max(1,Frames);
    S->Events.Reserve(S->EventLimit); S->Frames.Reserve(S->FrameLimit);
    return S;
}
void NumberOrNull(const TSharedPtr<FJsonObject>& O,const TCHAR* Key,uint64 Value,const FSession& S,bool Time)
{
    if (!Value || (Time && Value<S.Start)) O->SetField(Key,MakeShared<FJsonValueNull>());
    else O->SetNumberField(Key,Time ? FPlatformTime::ToSeconds64(Value-S.Start)*1000.0 : static_cast<double>(Value));
}
TSharedPtr<FJsonObject> Report(FSession& S)
{
    Drain(S);
    auto Root=MakeShared<FJsonObject>();
    Root->SetNumberField(TEXT("schema_version"),1);
    Root->SetStringField(TEXT("endpoint"),TEXT("backbuffer_ready_rt"));
    Root->SetStringField(TEXT("clock"),TEXT("FPlatformTime::Cycles64"));
    Root->SetNumberField(TEXT("seconds_per_cycle"),FPlatformTime::GetSecondsPerCycle64());
    Root->SetStringField(TEXT("captured_at_utc"),S.Utc);
    auto Session=MakeShared<FJsonObject>();
    Session->SetStringField(TEXT("id"),S.Id);
    Session->SetStringField(TEXT("engine_version"),FEngineVersion::Current().ToString());
    Session->SetStringField(TEXT("platform"),ANSI_TO_TCHAR(FPlatformProperties::IniPlatformName()));
    Session->SetStringField(TEXT("cpu"),FPlatformMisc::GetCPUBrand());
    Session->SetStringField(TEXT("build_configuration"),LexToString(FApp::GetBuildConfiguration()));
    Session->SetNumberField(TEXT("viewport_width"),S.Width); Session->SetNumberField(TEXT("viewport_height"),S.Height);
    Root->SetObjectField(TEXT("session"),Session);
    Root->SetNumberField(TEXT("event_count"),S.Events.Num());
    Root->SetNumberField(TEXT("dropped_event_count"),S.DroppedEvents);
    Root->SetNumberField(TEXT("dropped_stage_count"),S.DroppedStages);
    Root->SetNumberField(TEXT("dropped_frame_count"),S.DroppedFrames);
    Root->SetNumberField(TEXT("dropped_render_count"),S.DroppedRender.load());
    Root->SetNumberField(TEXT("dropped_input_count"),S.DroppedInputs);
    Root->SetNumberField(TEXT("overflow_count"),S.DroppedEvents+S.DroppedStages+S.DroppedFrames+S.DroppedInputs+S.DroppedRender.load());
    TArray<TSharedPtr<FJsonValue>> Events,Frames;
    for (const auto& F:S.Frames)
    {
        auto O=MakeShared<FJsonObject>(); O->SetNumberField(TEXT("scene_buildings"),F.Buildings);
        O->SetNumberField(TEXT("game_frame"),F.Frame); O->SetNumberField(TEXT("frame_ms"),F.Milliseconds);
        Frames.Add(MakeShared<FJsonValueObject>(O));
    }
    static const TCHAR* Names[]={TEXT("Selection"),TEXT("Mode"),TEXT("Rotation"),TEXT("Preview"),TEXT("Buildings"),TEXT("Message")};
    for (const auto& E:S.Events)
    {
        auto O=MakeShared<FJsonObject>();
        O->SetStringField(TEXT("id"),LexToString(E.Id)); O->SetStringField(TEXT("kind"),E.Kind.ToString());
        O->SetStringField(TEXT("source"),E.Source); O->SetStringField(TEXT("input_path"),E.Path);
        O->SetNumberField(TEXT("scene_buildings"),E.Buildings); O->SetNumberField(TEXT("entity_id"),E.Entity);
        if (E.Kind==TEXT("preview"))
        {
            if (E.CacheHit || E.CacheEvaluated) O->SetStringField(TEXT("preview_cache"),E.CacheHit ? TEXT("hit") : TEXT("miss"));
            else O->SetField(TEXT("preview_cache"),MakeShared<FJsonValueNull>());
        }
        NumberOrNull(O,TEXT("slate_constructed_t_ms"),E.Input.Constructed,S,true);
        NumberOrNull(O,TEXT("input_receipt_t_ms"),E.Input.Receipt,S,true);
        if (E.Input.Receipt) O->SetNumberField(TEXT("input_frame"),E.Input.InputFrame); else O->SetField(TEXT("input_frame"),MakeShared<FJsonValueNull>());
        NumberOrNull(O,TEXT("controller_t_ms"),E.Input.Controller,S,true);
        if (E.Input.Controller) O->SetNumberField(TEXT("controller_frame"),E.Input.ControllerFrame); else O->SetField(TEXT("controller_frame"),MakeShared<FJsonValueNull>());
        TArray<TSharedPtr<FJsonValue>> Stages,Channels;
        for (const auto& T:E.Stages)
        {
            auto V=MakeShared<FJsonObject>(); V->SetStringField(TEXT("name"),T.Name.ToString());
            V->SetNumberField(TEXT("t_ms"),FPlatformTime::ToSeconds64(T.Cycles-S.Start)*1000.0);
            V->SetNumberField(TEXT("game_frame"),T.Frame); Stages.Add(MakeShared<FJsonValueObject>(V));
        }
        O->SetArrayField(TEXT("stages"),Stages);
        bool Scene=false,HUD=false;
        for (int32 I=0;I<ChannelCount;++I) { Scene|=(E.Needs[I]&1)!=0; HUD|=(E.Needs[I]&2)!=0; if (E.Needs[I]) Channels.Add(MakeShared<FJsonValueString>(Names[I])); }
        auto V=MakeShared<FJsonObject>(); V->SetBoolField(TEXT("needs_scene"),Scene); V->SetBoolField(TEXT("needs_hud"),HUD);
        V->SetStringField(TEXT("channel"),Scene ? (HUD ? TEXT("scene+hud") : TEXT("scene")) : (HUD ? TEXT("hud") : TEXT("none")));
        V->SetArrayField(TEXT("channels"),Channels);
        V->SetStringField(TEXT("status"),!E.Ready ? TEXT("not_requested") : E.Backbuffer ? TEXT("observed") : E.Superseded ? TEXT("superseded") : TEXT("pending"));
        NumberOrNull(V,TEXT("ready_t_ms"),E.Ready,S,true);
        if (E.Ready) V->SetNumberField(TEXT("ready_frame"),E.ReadyFrame); else V->SetField(TEXT("ready_frame"),MakeShared<FJsonValueNull>());
        NumberOrNull(V,TEXT("backbuffer_t_ms"),E.Backbuffer,S,true);
        NumberOrNull(V,TEXT("scene_rt_t_ms"),Scene ? E.SceneRenderCycles : 0,S,true);
        if (E.Backbuffer) V->SetNumberField(TEXT("render_frame"),E.RenderFrame); else V->SetField(TEXT("render_frame"),MakeShared<FJsonValueNull>());
        O->SetObjectField(TEXT("visual"),V); Events.Add(MakeShared<FJsonValueObject>(O));
    }
    Root->SetArrayField(TEXT("events"),Events); Root->SetArrayField(TEXT("frames"),Frames);
    return Root;
}
}

bool Start(UWorld* World,const FString& OutputPath)
{
#if UE_BUILD_SHIPPING
    return false;
#else
    if (Capturing || !World || OutputPath.IsEmpty() || !FSlateApplication::IsInitialized()) return false;
    auto* Viewport=World->GetGameViewport();
    if (!Viewport || !Viewport->Viewport || !Viewport->GetWindow().IsValid()) return false;
    Active=NewSession(8192,65536); auto S=Active;
    S->Path=OutputPath; S->Viewport=Viewport; S->Target=Viewport->Viewport; S->Window=Viewport->GetWindow().Get();
    const auto Size=Viewport->Viewport->GetSizeXY(); S->Width=Size.X; S->Height=Size.Y;
    S->Renderer=FSlateApplication::Get().GetRenderer();
    Capturing=true;
    S->InputObserver=MakeShared<FPassiveInput>(FSessionWeak(S));
    FSlateApplication::Get().RegisterInputPreProcessor(S->InputObserver,0);
    S->Extension=FSceneViewExtensions::NewExtension<FViewObserver>(World,FSessionWeak(S),S->Target);
    S->DrawnHandle=Viewport->OnDrawn().AddLambda([Weak=FSessionWeak(S)]()
    {
        const auto P=Weak.Pin();
        if (!P || !Capturing || P->PendingHUDFrame!=GFrameCounter || !HasTokens(P->PendingHUD)) return;
        const auto Tokens=P->PendingHUD; const uint64 Frame=P->PendingHUDFrame;
        ENQUEUE_RENDER_COMMAND(ShoenProfileHUD)([P,Tokens,Frame](FRHICommandListImmediate&) { StoreHUD(*P,Frame,Tokens); });
    });
    S->BackbufferHandle=S->Renderer->OnBackBufferReadyToPresent().AddLambda([Weak=FSessionWeak(S)](SWindow& Window,ISlateViewportProvider&)
    {
        const auto P=Weak.Pin();
        if (P && P->Window==&Window) Backbuffer(*P,GFrameCounterRenderThread);
    });
    return true;
#endif
}
bool Stop()
{
    if (!Capturing || !Active) return false;
    auto S=Active; Capturing=false; S->Sampling=false; S->Current=0;
    if (FSlateApplication::IsInitialized() && S->InputObserver) FSlateApplication::Get().UnregisterInputPreProcessor(S->InputObserver);
    if (auto* V=S->Viewport.Get()) V->OnDrawn().Remove(S->DrawnHandle);
    S->Extension.Reset(); S->InputObserver.Reset();
    // One session-end drain, never a wait in the measured interaction path.
    if (!S->Testing) FlushRenderingCommands();
    S->Observing.store(false);
    if (S->Renderer && FSlateApplication::IsInitialized()) S->Renderer->OnBackBufferReadyToPresent().Remove(S->BackbufferHandle);
    const auto Json=Report(*S); FString Text;
    const auto Writer=TJsonWriterFactory<>::Create(&Text);
    const bool Serialized=FJsonSerializer::Serialize(Json.ToSharedRef(),Writer);
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(S->Path),true);
    const bool Saved=Serialized && FFileHelper::SaveStringToFile(Text,*S->Path);
    Active.Reset(); return Saved;
}
bool IsCapturing() { return Capturing; }
void SetSamplingEnabled(bool Enabled)
{
    if (!Capturing) return;
    Active->Sampling=Enabled; Active->Current=0; Active->Inputs.Reset();
    if (!Enabled) for (int32 I=0;I<ChannelCount;++I) { Supersede(*Active,Active->Tokens.Id[I]); Active->Tokens.Id[I]=0; }
}
void SetReplaySource(bool Replay) { if (Capturing) Active->Replay=Replay; }
void SetSceneBuildingCount(int32 Count) { if (Capturing) Active->Buildings=FMath::Max(0,Count); }
uint64 CurrentEvent() { return Sampling() ? Active->Current : 0; }
void ControllerInput(const FKey& Key,EInputEvent Type)
{
    if (!Sampling() || (Type!=IE_Pressed && Type!=IE_DoubleClick && Type!=IE_Axis)) return;
    const uint64 Time=Now();
    for (int32 I=Active->Inputs.Num()-1;I>=0;--I)
    {
        auto& Input=Active->Inputs[I];
        if (Input.Key==Key && Input.Type==Type && Fresh(Input,Time))
        { Input.Controller=Time; Input.ControllerFrame=GFrameCounter; return; }
    }
}
FActionScope::FActionScope(FName Kind,const FKey& Trigger)
{
    if (!Sampling() || Active->Current) return;
    auto& S=*Active;
    if (S.Events.Num()==S.EventLimit) { ++S.DroppedEvents; return; }
    auto& E=S.Events.AddDefaulted_GetRef(); E.Id=++NextId; E.Kind=Kind; E.Buildings=S.Buildings;
    if (S.Replay) { E.Source=TEXT("replay"); E.Path=TEXT("replay"); E.Input.Controller=Now(); E.Input.ControllerFrame=GFrameCounter; }
    else if (Trigger.IsValid())
    {
        const uint64 Time=Now();
        for (int32 I=S.Inputs.Num()-1;I>=0;--I)
        {
            auto& Input=S.Inputs[I];
            if (Input.Key!=Trigger || !Fresh(Input,Time)) continue;
            Input.Consumed=true; E.Input=Input; E.Source=TEXT("slate");
            E.Path=Trigger==EKeys::MouseX ? TEXT("cursor_motion") : Trigger.IsMouseButton() ? TEXT("mouse_button") : TEXT("keyboard");
            break;
        }
    }
    Event=E.Id; Session=S.Serial; bOwns=true; S.Current=Event; Stage(S,E,TEXT("logic_begin"));
}
FActionScope::~FActionScope()
{
    if (!bOwns || !Capturing || !Active || Active->Serial!=Session) return;
    if (auto* E=Find(*Active,Event)) Stage(*Active,*E,TEXT("logic_end"));
    Active->Current=0;
}
FUseEventScope::FUseEventScope(uint64 Id)
{
    if (!Sampling()) return;
    Session=Active->Serial; Previous=Active->Current;
    Active->Current=Find(*Active,Id) ? Id : 0;
}
FUseEventScope::~FUseEventScope() { if (Sampling() && Active->Serial==Session) Active->Current=Previous; }
void Mark(FName Name,uint64 Id) { if (Sampling()) if (auto* E=Find(*Active,Id ? Id : Active->Current)) Stage(*Active,*E,Name); }
void SetKind(FName Kind,uint64 Id) { if (Sampling()) if (auto* E=Find(*Active,Id ? Id : Active->Current)) E->Kind=Kind; }
void SetEntity(uint64 Entity,uint64 Id) { if (Sampling()) if (auto* E=Find(*Active,Id ? Id : Active->Current)) E->Entity=Entity; }
void VisualReady(uint64 Id,EVisualChannel Channel,bool Scene,bool HUD)
{
    if (!Sampling() || !Id) return;
    auto* E=Find(*Active,Id); const int32 I=static_cast<int32>(Channel);
    if (!E || I<0 || I>=ChannelCount || (!Scene && !HUD)) return;
    if (Active->Tokens.Id[I]!=Id) Supersede(*Active,Active->Tokens.Id[I]);
    Active->Tokens.Id[I]=Id;
    E->Revision[I]=++Active->NextRevision; Active->Tokens.Revision[I]=E->Revision[I];
    E->Needs[I]=(Scene ? 1 : 0)|(HUD ? 2 : 0);
    E->Ready=Now(); E->ReadyFrame=GFrameCounter;
    E->Backbuffer=0; E->RenderFrame=0; E->SceneRenderCycles=0;
    E->Superseded=false;
    for (int32 Required=0;Required<ChannelCount;++Required)
        if (E->Needs[Required] && (Active->Tokens.Id[Required]!=Id || Active->Tokens.Revision[Required]!=E->Revision[Required])) E->Superseded=true;
}
void Invalidate(EVisualChannel Channel)
{
    if (!Capturing) return;
    const int32 I=static_cast<int32>(Channel); if (I<0 || I>=ChannelCount) return;
    Supersede(*Active,Active->Tokens.Id[I]); Active->Tokens.Id[I]=0;
}
void ExpectMessage(const FString& Message)
{
    if (Sampling()) if (auto* E=Find(*Active,Active->Current)) { E->ExpectedMessage=Message; E->HasExpectedMessage=true; }
}
void CaptureHud(const FString& DisplayedMessage)
{
    if (!Capturing) return;
    const int32 Channel=static_cast<int32>(EVisualChannel::Message);
    if (const auto* E=Find(*Active,Active->Tokens.Id[Channel]))
        if (E->HasExpectedMessage && E->ExpectedMessage!=DisplayedMessage) Invalidate(EVisualChannel::Message);
    Active->PendingHUD=FTokens{}; Active->PendingHUDFrame=MAX_uint64;
    if (NeedsPass(*Active,2)) { Active->PendingHUD=Active->Tokens; Active->PendingHUDFrame=GFrameCounter; }
}
void Frame(float DeltaSeconds)
{
    if (!Capturing) return;
    Drain(*Active);
    if (!Sampling() || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds<=0) return;
    if (Active->Frames.Num()==Active->FrameLimit) { ++Active->DroppedFrames; return; }
    Active->Frames.Add({Active->Buildings,GFrameCounter,DeltaSeconds*1000.f});
}
#if WITH_DEV_AUTOMATION_TESTS
namespace Testing
{
bool Begin(int32 Events,int32 Frames)
{
    if (Capturing) return false;
    Active=NewSession(Events,Frames); Active->Testing=true; Capturing=true; return true;
}
void End() { Capturing=false; Active.Reset(); }
void SlateInput(const FKey& Key,double AgeMs)
{
    if (!Sampling()) return;
    const uint64 Time=Now()-static_cast<uint64>(FMath::Max(0.0,AgeMs)/1000.0/FPlatformTime::GetSecondsPerCycle64());
    RecordInput(*Active,Key,Key==EKeys::MouseX ? IE_Axis : IE_Pressed,Time,Time);
}
bool SceneSnapshot(uint64 Frame)
{
    if (!NeedsPass(*Active,1)) return false;
    StoreScene(*Active,Frame,Active->Tokens); return true;
}
void SceneRendered(uint64 Frame) { Rendered(*Active,Frame); }
bool HudSnapshot(uint64 Frame)
{
    if (!NeedsPass(*Active,2)) return false;
    StoreHUD(*Active,Frame,Active->Tokens); return true;
}
void Backbuffer(uint64 Frame) { ShoenProfile::Backbuffer(*Active,Frame); }
int32 QueuedObservations() { return Active->Queued.load(); }
TSharedPtr<FJsonObject> Snapshot() { return Report(*Active); }
}
#endif
}
