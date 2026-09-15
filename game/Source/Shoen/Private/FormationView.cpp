#include "FormationView.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"
#include "DrawDebugHelpers.h"
#include "domain/Battle.h"

AFormationView::AFormationView()
{
    PrimaryActorTick.bCanEverTick = false;
    Instances = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("SoldierInstances"));
    SetRootComponent(Instances);
    Instances->SetMobility(EComponentMobility::Movable);
    Instances->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Instances->SetCanEverAffectNavigation(false);
    Instances->SetCastShadow(false);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Mesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
    Instances->SetStaticMesh(Mesh.Object);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> BaseMaterial(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    Instances->SetMaterial(0,BaseMaterial.Object);
}
void AFormationView::Rebuild(const domain::World& State, const domain::Formation& Formation)
{
    FormationId = Formation.id;
    Instances->ClearInstances();
    TArray<FTransform> Transforms;
    const auto Slots = domain::FormationSlots(State, Formation.id);
    int32 SlotIndex = 0;
    for (auto ServiceId : Formation.service_ids)
    {
        const auto& Service = State.services.at(ServiceId);
        if (Service.status != domain::ServiceStatus::Active && Service.status != domain::ServiceStatus::WoundedAway) continue;
        const auto& Slot = Slots.at(SlotIndex++);
        const bool Wounded = Service.status == domain::ServiceStatus::WoundedAway;
        Transforms.Add(FTransform(FRotator::ZeroRotator, FVector(Slot.x, Slot.y, Wounded ? 30 : 90), FVector(0.35, 0.35, Wounded ? 0.6 : 1.8)));
    }
    Instances->AddInstances(Transforms, false, false, false);
    if (!Material) Material = Instances->CreateDynamicMaterialInstance(0);
    if (Material) Material->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.28, 0.45, 0.55));
    bWasSelected = false;
    UpdatePose(Formation, false);
}
void AFormationView::UpdatePose(const domain::Formation& Formation, bool Selected)
{
    SetActorLocationAndRotation(FVector(Formation.x, Formation.y, 0), FRotator(0, FMath::RadiansToDegrees(Formation.facing), 0));
    if (Material && Selected != bWasSelected)
        Material->SetVectorParameterValue(TEXT("Color"), Selected ? FLinearColor(0.95, 0.65, 0.14) : FLinearColor(0.28, 0.45, 0.55));
    bWasSelected = Selected;
    if (Selected)
    {
        DrawDebugBox(GetWorld(), GetActorLocation() + FVector(0,0,20), FVector(560,560,10), GetActorQuat(), FColor(255,206,82), false, -1, 0, 6);
        DrawDebugDirectionalArrow(GetWorld(), GetActorLocation() + FVector(0,0,210), GetActorLocation() + GetActorForwardVector() * 850 + FVector(0,0,210), 120, FColor::Yellow, false, -1, 0, 9);
        if (Formation.moving) DrawDebugCircle(GetWorld(), FVector(Formation.target_x, Formation.target_y, 20), 230, 20, FColor::Yellow, false, -1, 0, 7, FVector(1,0,0), FVector(0,1,0), false);
    }
}
int32 AFormationView::InstanceCount() const { return Instances->GetInstanceCount(); }
