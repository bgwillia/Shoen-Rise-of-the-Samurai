#include "FormationView.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"
#include "DrawDebugHelpers.h"
#include "domain/Battle.h"
#include "domain/Terrain.h"

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
    bCombatPresentation=false;
    SelectionExtent=FVector(560,560,10);
    CachedAlive=CachedDead=CachedWounded=-1;
    BaseTint=FLinearColor(.28,.45,.55);
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
    SetActorLocationAndRotation(FVector(Formation.x, Formation.y, bTerrain ? domain::TerrainHeight(Formation.x,Formation.y) : 0), FRotator(0, FMath::RadiansToDegrees(Formation.facing), 0));
    if (Material && Selected != bWasSelected)
        Material->SetVectorParameterValue(TEXT("Color"), Selected ? FLinearColor(0.95, 0.65, 0.14) : BaseTint);
    bWasSelected = Selected;
    if (Selected && (!bCombatPresentation || Instances->GetInstanceCount()>0))
    {
        DrawDebugBox(GetWorld(), GetActorLocation() + FVector(0,0,20), SelectionExtent+FVector(30,30,0), GetActorQuat(), FColor(45,30,5), false, -1, 0, 12);
        DrawDebugBox(GetWorld(), GetActorLocation() + FVector(0,0,20), SelectionExtent, GetActorQuat(), FColor(255,220,70), false, -1, 0, 7);
        DrawDebugDirectionalArrow(GetWorld(), GetActorLocation() + FVector(0,0,210), GetActorLocation() + GetActorForwardVector() * 850 + FVector(0,0,210), 120, FColor::Yellow, false, -1, 0, 9);
        if (Formation.moving) DrawDebugCircle(GetWorld(), FVector(Formation.target_x, Formation.target_y, 20+(bTerrain ? domain::TerrainHeight(Formation.target_x,Formation.target_y) : 0)), 230, 20, FColor::Yellow, false, -1, 0, 7, FVector(1,0,0), FVector(0,1,0), false);
    }
}
int32 AFormationView::InstanceCount() const { return Instances->GetInstanceCount(); }

void AFormationView::SetEnemy(bool Enemy)
{
    bEnemy=Enemy;
    BaseTint=Enemy ? FLinearColor(.85,.17,.12) : FLinearColor(.12,.42,.95);
    if (Material) Material->SetVectorParameterValue(TEXT("Color"),bWasSelected ? FLinearColor(.95,.65,.14) : BaseTint);
}
void AFormationView::UpdateCombat(const domain::World& State,const domain::Formation& Formation,const domain::CombatUnit& Unit,bool Selected)
{
    FormationId=Formation.id;
    const bool Elite=Formation.role==domain::TroopRole::SamuraiFoot || Formation.role==domain::TroopRole::RetainerInfantry || Formation.role==domain::TroopRole::MountedSamurai;
    const bool Bow=Formation.role==domain::TroopRole::Bow;
    const bool Mounted=Formation.role==domain::TroopRole::MountedSamurai;
    if (!bCombatPresentation || CachedAlive!=Unit.alive || CachedDead!=Unit.dead || CachedWounded!=Unit.wounded || CachedRole!=Formation.role)
    {
        int32 Standing=0;
        for (const auto Status:Unit.service_states) if (Status==domain::ServiceStatus::Active) ++Standing;
        Standing=FMath::Min(Standing,int32(Formation.service_ids.size()));
        const int32 Existing=Instances->GetInstanceCount();
        if (Existing>Standing)
        {
            TArray<int32> Removed;
            for (int32 I=Existing-1;I>=Standing;--I) Removed.Add(I);
            Instances->RemoveInstances(Removed,true);
        }
        TArray<FTransform> Transforms;
        Transforms.Reserve(Standing);
        const int32 Columns=FMath::Min(10,Standing), Rows=Columns ? (Standing+Columns-1)/Columns : 0;
        SelectionExtent=FVector(FMath::Max(65.,(Columns-1)*55.+65.),FMath::Max(65.,(Rows-1)*55.+65.),10);
        const FVector Scale=Mounted ? FVector(.9,.45,2.0) : Elite ? FVector(.5,.5,2.2) : Bow ? FVector(.24,.5,1.55) : FVector(.35,.35,1.8);
        for (int32 I=0;I<Standing;++I)
            Transforms.Add(FTransform(FRotator::ZeroRotator,FVector((I%Columns-(Columns-1)*.5)*110,(I/Columns-(Rows-1)*.5)*110,Scale.Z*50),Scale));
        const int32 Retained=Instances->GetInstanceCount();
        if (Retained) Instances->BatchUpdateInstancesTransforms(0,TArrayView<const FTransform>(Transforms.GetData(),Retained),false,true,true);
        if (Standing>Retained)
        {
            TArray<FTransform> Added;
            for (int32 I=Retained;I<Standing;++I) Added.Add(Transforms[I]);
            Instances->AddInstances(Added,false,false,false);
        }
        CachedAlive=Unit.alive; CachedDead=Unit.dead; CachedWounded=Unit.wounded; CachedRole=Formation.role;
        bCombatPresentation=true;
    }
    const bool FirstMaterial=!Material;
    if (!Material) Material=Instances->CreateDynamicMaterialInstance(0);
    const FLinearColor Tint=bEnemy ? (Elite ? FLinearColor(.75,.12,.48) : Bow ? FLinearColor(1,.38,.18) : FLinearColor(.85,.17,.12)) : (Elite ? FLinearColor(.42,.28,1) : Bow ? FLinearColor(.08,.75,.9) : FLinearColor(.12,.42,.95));
    if (BaseTint!=Tint || FirstMaterial)
    {
        BaseTint=Tint;
        if (Material) Material->SetVectorParameterValue(TEXT("Color"),Selected ? FLinearColor(.95,.65,.14) : BaseTint);
    }
    UpdatePose(Formation,Selected);
    if (Unit.routed && Instances->GetInstanceCount()>0)
        DrawDebugCircle(GetWorld(),GetActorLocation()+FVector(0,0,35),SelectionExtent.Size2D()+50,12,FColor::Orange,false,-1,0,5,FVector(1,0,0),FVector(0,1,0),false);
}
