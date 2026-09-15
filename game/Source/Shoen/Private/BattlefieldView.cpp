#include "BattlefieldView.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "MeshDescription.h"
#include "StaticMeshAttributes.h"
#include "PhysicsEngine/BodySetup.h"
#include "domain/Terrain.h"

ABattlefieldView::ABattlefieldView()
{
    PrimaryActorTick.bCanEverTick=false;
    Ground=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BattlefieldGround"));
    SetRootComponent(Ground);
    const TCHAR* Names[]={TEXT("River"),TEXT("Crossings"),TEXT("WoodsFloor"),TEXT("Trunks"),TEXT("Canopy"),TEXT("Deployment")};
    for (const auto* Name : Names)
    {
        auto* Layer=CreateDefaultSubobject<UInstancedStaticMeshComponent>(Name);
        Layer->SetupAttachment(Ground); SurfaceLayers.Add(Layer);
    }
}
void ABattlefieldView::BeginPlay()
{
    Super::BeginPlay();
    auto* Cube=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto* Base=LoadObject<UMaterialInterface>(nullptr,TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    auto Passive=[&](UStaticMeshComponent* Component,FLinearColor Color)
    {
        Component->SetMobility(EComponentMobility::Movable);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCanEverAffectNavigation(false); Component->SetCastShadow(false);
        Component->SetMaterial(0,Base);
        if (auto* Material=Component->CreateDynamicMaterialInstance(0)) Material->SetVectorParameterValue(TEXT("Color"),Color);
    };
    const FLinearColor Colors[]={{.04,.23,.38},{.54,.43,.28},{.13,.25,.10},{.24,.16,.08},{.08,.20,.09},{.38,.48,.28}};
    for (int32 I=0;I<SurfaceLayers.Num();++I) { SurfaceLayers[I]->SetStaticMesh(Cube); Passive(SurfaceLayers[I],Colors[I]); }
    Passive(Ground,FLinearColor(.31,.38,.21));
    const auto& T=domain::PrototypeTerrain();
    auto Block=[&](int32 Layer,double X,double Y,double Z,double W,double D,double H)
    { SurfaceLayers[Layer]->AddInstance(FTransform(FRotator::ZeroRotator,FVector(X,Y,Z),FVector(W,D,H)/100.)); };
    auto Rect=[&](int32 Layer,const domain::TerrainRect& R,double Z,double Height)
    { Block(Layer,(R.min_x+R.max_x)*.5,(R.min_y+R.max_y)*.5,Z,R.max_x-R.min_x,R.max_y-R.min_y,Height); };
    Rect(0,T.river,4,8);
    Rect(1,T.bridge,11,6); Rect(1,T.ford,10,4);
    // Broad surface patches and sparse trees communicate movement modifiers while leaving units visible.
    Rect(2,T.forest,3,6);
    for (double X=T.forest.min_x+700;X<T.forest.max_x;X+=1800)
        for (double Y=T.forest.min_y+600;Y<T.forest.max_y;Y+=2000)
        { Block(3,X,Y,130,85,85,260); Block(4,X,Y,300,470,470,170); }
    Block(5,-11200,0,5,130,19000,10); Block(5,11200,0,5,130,19000,10);
    // Shared height samples keep the visible defensive hill on the same coordinates as movement/combat.
    FMeshDescription Description;
    FStaticMeshAttributes Attributes(Description); Attributes.Register();
    Attributes.GetVertexInstanceUVs().SetNumChannels(1);
    auto Group=Description.CreatePolygonGroup(); Attributes.GetPolygonGroupMaterialSlotNames()[Group]=TEXT("Surface");
    auto Triangle=[&](FVector3f A,FVector3f B,FVector3f C)
    {
        const FVector3f Points[]={A,B,C}; FVertexInstanceID Corners[3];
        const auto Normal=FVector3f::CrossProduct(B-A,C-A).GetSafeNormal();
        for (int32 I=0;I<3;++I)
        {
            auto Vertex=Description.CreateVertex(); Attributes.GetVertexPositions()[Vertex]=Points[I];
            Corners[I]=Description.CreateVertexInstance(Vertex);
            Attributes.GetVertexInstanceNormals()[Corners[I]]=Normal;
            Attributes.GetVertexInstanceTangents()[Corners[I]]=(B-A).GetSafeNormal();
            Attributes.GetVertexInstanceBinormalSigns()[Corners[I]]=1;
            Attributes.GetVertexInstanceColors()[Corners[I]]=FVector4f(1,1,1,1);
            Attributes.GetVertexInstanceUVs().Set(Corners[I],0,FVector2f(Points[I].X,Points[I].Y)/1600.f);
        }
        const FVertexInstanceID Render[]={Corners[0],Corners[2],Corners[1]}; Description.CreateTriangle(Group,MakeArrayView(Render));
    };
    const double Cell=800;
    auto Point=[](double X,double Y) { return FVector3f(X,Y,domain::TerrainHeight(X,Y)); };
    for (double X=T.bounds.min_x;X<T.bounds.max_x;X+=Cell)
        for (double Y=T.bounds.min_y;Y<T.bounds.max_y;Y+=Cell)
        { const auto A=Point(X,Y),B=Point(X+Cell,Y),C=Point(X+Cell,Y+Cell),D=Point(X,Y+Cell); Triangle(A,B,C); Triangle(A,C,D); }
    auto* Mesh=NewObject<UStaticMesh>(this,NAME_None,RF_Transient);
    Mesh->GetStaticMaterials().Add(FStaticMaterial(Base,TEXT("Surface"))); Mesh->bSupportRayTracing=false;
    Mesh->CreateBodySetup(); Mesh->GetBodySetup()->bNeverNeedsCookedCollisionData=true;
    UStaticMesh::FBuildMeshDescriptionsParams Params; Params.bFastBuild=true; Params.bBuildSimpleCollision=false;
    Params.bCommitMeshDescription=false; Params.bMarkPackageDirty=false;
    TArray<const FMeshDescription*> Lods={&Description};
    if (Mesh->BuildFromMeshDescriptions(Lods,Params)) Ground->SetStaticMesh(Mesh);
}
