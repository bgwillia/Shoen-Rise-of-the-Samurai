#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Engine/World.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "SettlementView.h"
#include <limits>

namespace
{
void AddInspectionBuilding(domain::World& State, uint64 Id, int32 X, int32 Y, int32 Yaw,
    int32 Width=800, int32 Depth=600)
{
    domain::Building Building;
    Building.id=Id; Building.settlement_id=1; Building.district_id=2;
    Building.definition_id="small_storehouse"; Building.definition_version=1;
    Building.width_cm=Width; Building.depth_cm=Depth; Building.height_cm=450;
    Building.x_cm=X; Building.y_cm=Y; Building.yaw_degrees=Yaw;
    Building.placement_transaction_id=State.next_transaction_id++;
    State.applied_transaction_ids.insert(Building.placement_transaction_id);
    State.buildings.emplace(Id,Building);
    if (State.next_id<=Id) State.next_id=Id+1;
}

UInstancedStaticMeshComponent* SelectionOutline(ASettlementView* View)
{
    TArray<UInstancedStaticMeshComponent*> Components;
    View->GetComponents(Components);
    for (auto* Component : Components)
        if (Component->GetFName()==TEXT("BuildingSelectionFootprint")) return Component;
    return nullptr;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenInspectionPicking, "Shoen.Inspection.ViewPicking",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenInspectionPicking::RunTest(const FString& Parameters)
{
    FTestWorldWrapper Fixture;
    if (!TestTrue(TEXT("test world"),Fixture.CreateTestWorld(EWorldType::Game))) return false;
    auto State=domain::MakeFoundationWorld();
    // Stable IDs intentionally disagree with distance from the left-hand ray.
    AddInspectionBuilding(State,31,-1600,0,0);
    AddInspectionBuilding(State,11,0,0,45);
    AddInspectionBuilding(State,47,1600,0,90);
    const auto Before=State;
    auto* View=Fixture.GetTestWorld()->SpawnActor<ASettlementView>();
    View->Rebuild(State);
    for (const auto& [Id,Building] : State.buildings)
    {
        uint64 Hit=999;
        TestTrue(TEXT("each roof resolves under a vertical ray"),View->PickBuilding(
            FVector(Building.x_cm,Building.y_cm,2000),FVector(0,0,-3),Hit));
        TestEqual(TEXT("each hit uses its own stable ID"),Hit,uint64(Id));
    }
    uint64 Hit=999;
    TestTrue(TEXT("nearest body hit wins over earlier instance index"),View->PickBuilding(FVector(-4000,0,150),FVector(2,0,0),Hit));
    TestEqual(TEXT("nearest building ID"),Hit,uint64(31));
    for (double Magnitude : {1.e-310,1.e300})
    {
        TestTrue(TEXT("finite direction scale does not change picking"),
            View->PickBuilding(FVector(0,0,2000),FVector(0,0,-Magnitude),Hit));
        TestEqual(TEXT("scaled direction preserves ID"),Hit,uint64(11));
    }

    const FTransform Rotated(FRotator(0,45,0),FVector::ZeroVector);
    // This ray intersects the visible roof, but reaches z=0 at local y=-328.125,
    // outside the 600 cm footprint. Ground-only picking would miss it.
    TestTrue(TEXT("oblique rotated roof remains selectable beyond ground footprint"),View->PickBuilding(
        Rotated.TransformPosition(FVector(0,1150,1182.5)),Rotated.TransformVector(FVector(0,-1000,-800)),Hit));
    TestEqual(TEXT("oblique roof identifies rotated building"),Hit,uint64(11));
    TestTrue(TEXT("ray from inside body finds a positive exit"),View->PickBuilding(FVector(-1600,0,150),FVector(0,1,0),Hit));
    TestEqual(TEXT("inside hit identity"),Hit,uint64(31));

    const double NaN=std::numeric_limits<double>::quiet_NaN();
    const double Infinity=std::numeric_limits<double>::infinity();
    const TArray<TPair<FVector,FVector>> Misses={
        {FVector(0,4000,1000),FVector(0,0,-1)},
        {FVector(-4000,0,150),FVector(-1,0,0)},
        {FVector(0,0,2000),FVector::ZeroVector},
        {FVector(NaN,0,2000),FVector(0,0,-1)},
        {FVector(0,0,2000),FVector(Infinity,0,-1)}};
    for (const auto& Ray : Misses)
    {
        Hit=999;
        TestFalse(TEXT("miss invalid or behind ray rejected"),View->PickBuilding(Ray.Key,Ray.Value,Hit));
        TestEqual(TEXT("miss clears output ID"),Hit,uint64(0));
    }

    auto Single=domain::MakeFoundationWorld();
    AddInspectionBuilding(Single,31,0,0,0);
    View->Rebuild(Single);
    Hit=999;
    TestFalse(TEXT("empty space inside full bounding box above sloped roof is not a hit"),
        View->PickBuilding(FVector(-1000,250,440),FVector(1,0,0),Hit));
    TestEqual(TEXT("roof bounding-box false positive clears ID"),Hit,uint64(0));
    TestTrue(TEXT("actual gable triangle is a hit"),View->PickBuilding(FVector(-1000,0,440),FVector(1,0,0),Hit));
    TestEqual(TEXT("gable hit identity"),Hit,uint64(31));

    auto Ridge=domain::MakeFoundationWorld();
    AddInspectionBuilding(Ridge,31,2000,0,0);
    domain::BuildArea Area;
    Area.settlement_id=1; Area.origin_x_cm=-3000; Area.origin_y_cm=-1000;
    Area.cell_size_cm=1000; Area.columns=7; Area.rows=3;
    for (int32 Row=0; Row<3; ++Row)
        for (int32 Column=0; Column<7; ++Column) Area.heights_cm.push_back(Column==3 ? 1000 : 0);
    Ridge.build_areas.emplace(1,Area);
    View->Rebuild(Ridge);
    TestFalse(TEXT("nearer authoritative ridge occludes otherwise hittable roof"),
        View->PickBuilding(FVector(-3000,0,400),FVector(1,0,0),Hit));
    TestEqual(TEXT("terrain occlusion clears ID"),Hit,uint64(0));
    TestTrue(TEXT("same roof is selectable from beyond the ridge"),
        View->PickBuilding(FVector(1000,0,400),FVector(1,0,0),Hit));
    TestEqual(TEXT("unoccluded roof identity"),Hit,uint64(31));
    TestTrue(TEXT("picking never mutates simulation"),State==Before);
    Fixture.DestroyTestWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShoenInspectionHighlight, "Shoen.Inspection.ViewIdentityAndHighlight",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FShoenInspectionHighlight::RunTest(const FString& Parameters)
{
    FTestWorldWrapper Fixture;
    if (!TestTrue(TEXT("test world"),Fixture.CreateTestWorld(EWorldType::Game))) return false;
    auto State=domain::MakeFoundationWorld();
    AddInspectionBuilding(State,11,-1800,0,0);
    AddInspectionBuilding(State,31,0,0,37,1234,678);
    AddInspectionBuilding(State,47,1800,0,90);
    const auto Before=State;
    auto* View=Fixture.GetTestWorld()->SpawnActor<ASettlementView>();
    View->Rebuild(State);
    View->SetSelectedBuilding(31,State);
    TestEqual(TEXT("selection stores requested stable ID"),View->SelectedBuildingId(),uint64(31));
    auto* Outline=SelectionOutline(View);
    if (TestNotNull(TEXT("separate highlight component"),Outline))
    {
        TestFalse(TEXT("highlight has no component tick"),Outline->PrimaryComponentTick.bCanEverTick);
        TestTrue(TEXT("highlight is render only"),Outline->GetCollisionEnabled()==ECollisionEnabled::NoCollision);
        TestTrue(TEXT("selected footprint visible"),Outline->IsVisible());
        TestTrue(TEXT("selected footprint has geometry"),Outline->GetInstanceCount()>0);
        const FTransform Base(FRotator(0,37,0),FVector::ZeroVector);
        for (int32 Index=0; Index<Outline->GetInstanceCount(); ++Index)
        {
            FTransform Segment;
            TestTrue(TEXT("highlight segment transform"),Outline->GetInstanceTransform(Index,Segment,true));
            const FVector Local=Base.InverseTransformPosition(Segment.GetLocation());
            TestTrue(TEXT("outline uses frozen dimensions and yaw"),
                FMath::IsNearlyEqual(FMath::Abs(Local.X),617.0,0.1) || FMath::IsNearlyEqual(FMath::Abs(Local.Y),339.0,0.1));
        }
    }
    View->Rebuild(State);
    TestEqual(TEXT("same-world rebuild reacquires same selection"),View->SelectedBuildingId(),uint64(31));
    TestTrue(TEXT("highlight/rebuild leave authoritative state unchanged"),State==Before);

    // Removing an earlier map entry shifts instance slots; identity must not shift.
    State.buildings.erase(11);
    View->Rebuild(State);
    uint64 Hit=0;
    TestTrue(TEXT("ray still hits after instance slot shift"),View->PickBuilding(FVector(0,0,2000),FVector(0,0,-1),Hit));
    TestEqual(TEXT("shifted slot still resolves selected ID"),Hit,uint64(31));
    TestEqual(TEXT("slot shift preserves selected ID"),View->SelectedBuildingId(),uint64(31));
    View->Destroy();
    View=Fixture.GetTestWorld()->SpawnActor<ASettlementView>();
    View->Rebuild(State);
    TestEqual(TEXT("recreated view starts with no pointer identity"),View->SelectedBuildingId(),uint64(0));
    View->SetSelectedBuilding(31,State);
    TestTrue(TEXT("recreated view picking resolves stable record"),View->PickBuilding(FVector(1800,0,2000),FVector(0,0,-1),Hit));
    TestEqual(TEXT("another building never aliases selected one"),Hit,uint64(47));
    TestEqual(TEXT("external stable ID reapplies highlight"),View->SelectedBuildingId(),uint64(31));
    const auto Recreated=State;
    View->SetSelectedBuilding(999,State);
    TestEqual(TEXT("missing ID safely clears selection"),View->SelectedBuildingId(),uint64(0));
    View->SetSelectedBuilding(31,State);
    TestTrue(TEXT("selection and missing lookup do not mutate recreated world"),State==Recreated);
    State.buildings.erase(31);
    View->Rebuild(State);
    TestEqual(TEXT("removing selected record clears selection"),View->SelectedBuildingId(),uint64(0));
    Outline=SelectionOutline(View);
    if (TestNotNull(TEXT("outline component persists without selected record"),Outline))
    {
        TestEqual(TEXT("no stale highlight instances"),Outline->GetInstanceCount(),0);
        TestFalse(TEXT("missing selection outline hidden"),Outline->IsVisible());
    }
    const auto Final=State;
    View->SetSelectedBuilding(0,State);
    View->Rebuild(State);
    TestTrue(TEXT("clear and final rebuild remain read only"),State==Final);
    auto Mismatched=Recreated;
    Mismatched.buildings.at(31).id=999;
    View->Rebuild(Mismatched);
    View->SetSelectedBuilding(31,Mismatched);
    TestEqual(TEXT("mismatched map key and record ID cannot acquire highlight"),View->SelectedBuildingId(),uint64(0));
    Fixture.DestroyTestWorld(false);
    return true;
}
#endif
