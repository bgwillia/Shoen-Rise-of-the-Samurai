#if WITH_DEV_AUTOMATION_TESTS
#include "InteractionProfiler.h"
#include "Dom/JsonObject.h"
#include "Misc/AutomationTest.h"

namespace
{
TSharedPtr<FJsonObject> ProfileEvent(const TSharedPtr<FJsonObject>& Report,int32 Index)
{
    return Report->GetArrayField(TEXT("events"))[Index]->AsObject();
}
FString VisualStatus(const TSharedPtr<FJsonObject>& Report,int32 Index)
{
    return ProfileEvent(Report,Index)->GetObjectField(TEXT("visual"))->GetStringField(TEXT("status"));
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenProfileCapacity,"Shoen.Profiling.CollectorCapacityAndScopes",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenProfileCapacity::RunTest(const FString& Parameters)
{
    using namespace ShoenProfile;
    if (!TestTrue(TEXT("isolated collector"),Testing::Begin(2,2))) return false;
    uint64 First=0;
    {
        FActionScope Outer(TEXT("select"));
        First=CurrentEvent();
        FActionScope Nested(TEXT("nested"));
        TestEqual(TEXT("nested action reuses event"),CurrentEvent(),First);
        Mark(TEXT("pick_begin"));
    }
    TestEqual(TEXT("scope restores no active event"),CurrentEvent(),uint64(0));
    {
        FUseEventScope Use(First);
        TestEqual(TEXT("deferred hook reacquires event"),CurrentEvent(),First);
        { FUseEventScope Unrelated(0); TestEqual(TEXT("zero scope suppresses inherited event"),CurrentEvent(),uint64(0)); }
        TestEqual(TEXT("zero scope restores outer event"),CurrentEvent(),First);
        Mark(TEXT("view_update"));
    }
    SetSamplingEnabled(false);
    { FActionScope Disabled(TEXT("ignored")); Mark(TEXT("ignored")); }
    TestTrue(TEXT("sampling pause retains session"),IsCapturing());
    TestEqual(TEXT("sampling pause has no current event"),CurrentEvent(),uint64(0));
    SetSamplingEnabled(true);
    { FActionScope Second(TEXT("clear")); }
    { FActionScope Overflow(TEXT("overflow")); TestEqual(TEXT("event capacity refuses new ID"),CurrentEvent(),uint64(0)); }
    Frame(.016f); Frame(.017f); Frame(.018f);
    const auto Report=Testing::Snapshot();
    TestEqual(TEXT("event storage bounded"),Report->GetArrayField(TEXT("events")).Num(),2);
    TestEqual(TEXT("frame storage bounded"),Report->GetArrayField(TEXT("frames")).Num(),2);
    TestEqual(TEXT("both capacity drops reported"),Report->GetNumberField(TEXT("overflow_count")),2.0);
    TestEqual(TEXT("no visual request is not pending"),VisualStatus(Report,0),FString(TEXT("not_requested")));
    TestEqual(TEXT("original kind retained by nested scope"),ProfileEvent(Report,0)->GetStringField(TEXT("kind")),FString(TEXT("select")));
    Testing::End();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenProfileSources,"Shoen.Profiling.InputSourceAssociation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenProfileSources::RunTest(const FString& Parameters)
{
    using namespace ShoenProfile;
    if (!TestTrue(TEXT("isolated collector"),Testing::Begin())) return false;
    Testing::SlateInput(EKeys::LeftMouseButton);
    ControllerInput(EKeys::LeftMouseButton,IE_Pressed);
    { FActionScope Matched(TEXT("select"),EKeys::LeftMouseButton); }
    { FActionScope Consumed(TEXT("clear"),EKeys::LeftMouseButton); }
    Testing::SlateInput(EKeys::B,500);
    { FActionScope Stale(TEXT("placement_enter"),EKeys::B); }
    Testing::SlateInput(EKeys::MouseX);
    { FActionScope Motion(TEXT("preview"),EKeys::MouseX); Mark(TEXT("preview_cached")); }
    SetReplaySource(true);
    Testing::SlateInput(EKeys::Enter);
    { FActionScope Replay(TEXT("placement_confirm_success"),EKeys::Enter); }
    const auto Report=Testing::Snapshot();
    TestEqual(TEXT("recent input source"),ProfileEvent(Report,0)->GetStringField(TEXT("source")),FString(TEXT("slate")));
    TestEqual(TEXT("input can only be consumed once"),ProfileEvent(Report,1)->GetStringField(TEXT("source")),FString(TEXT("frame_poll")));
    TestEqual(TEXT("stale input cannot claim physical route"),ProfileEvent(Report,2)->GetStringField(TEXT("source")),FString(TEXT("frame_poll")));
    TestEqual(TEXT("mouse motion matches preview trigger"),ProfileEvent(Report,3)->GetStringField(TEXT("source")),FString(TEXT("slate")));
    TestEqual(TEXT("cache hit retained"),ProfileEvent(Report,3)->GetStringField(TEXT("preview_cache")),FString(TEXT("hit")));
    TestEqual(TEXT("replay never masquerades as physical input"),ProfileEvent(Report,4)->GetStringField(TEXT("source")),FString(TEXT("replay")));
    Testing::End();
    if (!TestTrue(TEXT("input overflow collector"),Testing::Begin())) return false;
    for (int32 I=0;I<65;++I) Testing::SlateInput(EKeys::LeftMouseButton);
    TestEqual(TEXT("lost fresh action input is reported"),Testing::Snapshot()->GetNumberField(TEXT("dropped_input_count")),1.0);
    TestEqual(TEXT("input loss contributes to incomplete report"),Testing::Snapshot()->GetNumberField(TEXT("overflow_count")),1.0);
    Testing::End();
    if (!TestTrue(TEXT("motion coalescing collector"),Testing::Begin())) return false;
    for (int32 I=0;I<100;++I) Testing::SlateInput(EKeys::MouseX);
    { FActionScope Motion(TEXT("preview"),EKeys::MouseX); }
    { FActionScope Evaluated(TEXT("preview")); Mark(TEXT("preview_validation_begin")); }
    const auto Coalesced=Testing::Snapshot();
    TestEqual(TEXT("latest motion remains attributable"),ProfileEvent(Coalesced,0)->GetStringField(TEXT("source")),FString(TEXT("slate")));
    TestEqual(TEXT("intermediate motion is coalesced without overflow"),Coalesced->GetNumberField(TEXT("overflow_count")),0.0);
    TestTrue(TEXT("preview without a target evaluation has no cache result"),ProfileEvent(Coalesced,0)->Values.FindChecked(TEXT("preview_cache"))->IsNull());
    TestEqual(TEXT("evaluated preview is a cache miss"),ProfileEvent(Coalesced,1)->GetStringField(TEXT("preview_cache")),FString(TEXT("miss")));
    Testing::End();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenProfileFrames,"Shoen.Profiling.ExactFrameVisualCorrelation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenProfileFrames::RunTest(const FString& Parameters)
{
    using namespace ShoenProfile;
    if (!TestTrue(TEXT("isolated collector"),Testing::Begin())) return false;
    uint64 First=0,Second=0;
    {
        FActionScope Action(TEXT("select")); First=CurrentEvent();
        VisualReady(First,EVisualChannel::Selection,true,true);
        VisualReady(First,EVisualChannel::Message,false,true);
    }
    Testing::SceneSnapshot(101);
    Testing::SceneRendered(101);
    Testing::HudSnapshot(102);
    Testing::Backbuffer(101);
    TestEqual(TEXT("another frame's HUD cannot complete scene"),VisualStatus(Testing::Snapshot(),0),FString(TEXT("pending")));
    Testing::HudSnapshot(101);
    {
        FActionScope Action(TEXT("switch")); Second=CurrentEvent();
        VisualReady(Second,EVisualChannel::Selection,true,true);
        VisualReady(Second,EVisualChannel::Message,false,true);
    }
    // GT already advanced to Second; the queued frame still contains First.
    Testing::Backbuffer(101);
    auto Report=Testing::Snapshot();
    TestEqual(TEXT("older queued frame uses immutable tokens"),VisualStatus(Report,0),FString(TEXT("observed")));
    TestEqual(TEXT("newer GT state cannot steal older backbuffer"),VisualStatus(Report,1),FString(TEXT("pending")));
    TestTrue(TEXT("older completion retains newer scene request"),Testing::SceneSnapshot(103));
    TestTrue(TEXT("older completion retains newer HUD request"),Testing::HudSnapshot(103));
    Testing::Backbuffer(103);
    TestEqual(TEXT("GT scene enqueue alone is insufficient"),VisualStatus(Testing::Snapshot(),1),FString(TEXT("pending")));
    Testing::SceneRendered(103);
    Testing::Backbuffer(103);
    Report=Testing::Snapshot();
    TestEqual(TEXT("same-frame scene and HUD observed"),VisualStatus(Report,1),FString(TEXT("observed")));
    const double ObservedAt=ProfileEvent(Report,1)->GetObjectField(TEXT("visual"))->GetNumberField(TEXT("backbuffer_t_ms"));
    TestFalse(TEXT("observed request no longer schedules scene work"),Testing::SceneSnapshot(108));
    TestFalse(TEXT("observed request no longer schedules HUD work"),Testing::HudSnapshot(108));
    Testing::SceneRendered(108); Testing::Backbuffer(108);
    TestEqual(TEXT("idle frame queues no empty observation"),Testing::QueuedObservations(),0);
    Testing::Backbuffer(103);
    Report=Testing::Snapshot();
    TestEqual(TEXT("queued duplicate cannot replace first endpoint"),ProfileEvent(Report,1)->GetObjectField(TEXT("visual"))->GetNumberField(TEXT("backbuffer_t_ms")),ObservedAt);
    TestEqual(TEXT("draining observed tokens does not supersede event"),VisualStatus(Report,1),FString(TEXT("observed")));
    {
        FActionScope Action(TEXT("clear"));
        VisualReady(CurrentEvent(),EVisualChannel::Selection,true,true);
    }
    Invalidate(EVisualChannel::Selection);
    Testing::SceneSnapshot(104); Testing::SceneRendered(104); Testing::HudSnapshot(104); Testing::Backbuffer(104);
    TestEqual(TEXT("invalidated token is superseded"),VisualStatus(Testing::Snapshot(),2),FString(TEXT("superseded")));
    uint64 Revised=0;
    {
        FActionScope Action(TEXT("preview")); Revised=CurrentEvent();
        VisualReady(Revised,EVisualChannel::Preview,true,true);
    }
    Testing::SceneSnapshot(105); Testing::SceneRendered(105); Testing::HudSnapshot(105);
    VisualReady(Revised,EVisualChannel::Preview,true,true);
    Testing::Backbuffer(105);
    TestEqual(TEXT("same event newer revision cannot match old snapshot"),VisualStatus(Testing::Snapshot(),3),FString(TEXT("pending")));
    Invalidate(EVisualChannel::Preview);
    VisualReady(Revised,EVisualChannel::Preview,true,true);
    TestEqual(TEXT("re-armed same event is pending until observed"),VisualStatus(Testing::Snapshot(),3),FString(TEXT("pending")));
    SetSamplingEnabled(false);
    Invalidate(EVisualChannel::Preview);
    Testing::SceneSnapshot(106); Testing::SceneRendered(106); Testing::HudSnapshot(106); Testing::Backbuffer(106);
    TestEqual(TEXT("unmeasured setup cannot complete pending visual"),VisualStatus(Testing::Snapshot(),3),FString(TEXT("superseded")));
    SetSamplingEnabled(true);
    {
        FActionScope Rejected(TEXT("placement_confirm_rejected"));
        ExpectMessage(TEXT("Occupied"));
        VisualReady(CurrentEvent(),EVisualChannel::Message,false,true);
    }
    CaptureHud(TEXT("Replacement message"));
    Testing::HudSnapshot(107); Testing::Backbuffer(107);
    TestEqual(TEXT("replacement HUD message cannot complete rejection"),VisualStatus(Testing::Snapshot(),4),FString(TEXT("superseded")));
    {
        FActionScope HUDOnly(TEXT("enter"));
        VisualReady(CurrentEvent(),EVisualChannel::Mode,false,true);
    }
    TestFalse(TEXT("HUD-only request does not schedule scene work"),Testing::SceneSnapshot(109));
    TestTrue(TEXT("HUD-only request schedules HUD work"),Testing::HudSnapshot(109));
    Testing::Backbuffer(109);
    TestEqual(TEXT("HUD-only request still completes"),VisualStatus(Testing::Snapshot(),5),FString(TEXT("observed")));
    {
        FActionScope SceneOnly(TEXT("preview"));
        VisualReady(CurrentEvent(),EVisualChannel::Preview,true,false);
    }
    TestTrue(TEXT("scene-only request schedules scene work"),Testing::SceneSnapshot(110));
    TestFalse(TEXT("scene-only request does not schedule HUD work"),Testing::HudSnapshot(110));
    Testing::SceneRendered(110); Testing::Backbuffer(110);
    TestEqual(TEXT("scene-only request still completes"),VisualStatus(Testing::Snapshot(),6),FString(TEXT("observed")));
    Testing::End();
    return true;
}
#endif
