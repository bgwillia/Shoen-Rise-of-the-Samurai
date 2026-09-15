#include "SettlementView.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "MeshDescription.h"
#include "StaticMeshAttributes.h"
#include "StaticMeshResources.h"
#include "PhysicsEngine/BodySetup.h"
#include "UObject/ConstructorHelpers.h"
#include "domain/Buildings.h"
#include <cmath>

namespace
{
constexpr double CubeSize = 100.0;
constexpr double WallFraction = 0.7;

// Only render geometry is created here. All footprint and ground decisions stay
// in DomainCore. Per-triangle normals make the authored ramp easy to distinguish.
class FSurfaceMesh
{
public:
    FSurfaceMesh() : Attributes(Description)
    {
        Attributes.Register();
        Attributes.GetVertexInstanceUVs().SetNumChannels(1);
        Group = Description.CreatePolygonGroup();
        Attributes.GetPolygonGroupMaterialSlotNames()[Group] = TEXT("Surface");
    }

    void Triangle(const FVector3f& A, const FVector3f& B, const FVector3f& C)
    {
        const FVector3f Points[] = {A,B,C};
        const FVector3f Normal = FVector3f::CrossProduct(B-A,C-A).GetSafeNormal();
        const FVector3f Tangent = (B-A).GetSafeNormal();
        FVertexInstanceID Corners[3];
        for (int32 I=0; I<3; ++I)
        {
            const FVertexID Vertex = Description.CreateVertex();
            Attributes.GetVertexPositions()[Vertex] = Points[I];
            Corners[I] = Description.CreateVertexInstance(Vertex);
            Attributes.GetVertexInstanceNormals()[Corners[I]] = Normal;
            Attributes.GetVertexInstanceTangents()[Corners[I]] = Tangent;
            Attributes.GetVertexInstanceBinormalSigns()[Corners[I]] = 1;
            Attributes.GetVertexInstanceColors()[Corners[I]] = FVector4f(1,1,1,1);
            Attributes.GetVertexInstanceUVs().Set(Corners[I],0,FVector2f(Points[I].X,Points[I].Y)/1000.0f);
        }
        // Unreal static-mesh fronts use clockwise winding; retain the core
        // triangle positions/diagonal and the outward mathematical normal.
        const FVertexInstanceID RenderCorners[] = {Corners[0],Corners[2],Corners[1]};
        Description.CreateTriangle(Group,MakeArrayView(RenderCorners));
    }

    UStaticMesh* Build(UObject* Owner, UMaterialInterface* Material)
    {
        if (Description.Triangles().Num()==0) return nullptr;
        UStaticMesh* Mesh = NewObject<UStaticMesh>(Owner,NAME_None,RF_Transient);
        Mesh->GetStaticMaterials().Add(FStaticMaterial(Material,TEXT("Surface")));
        Mesh->bSupportRayTracing = false;
        Mesh->CreateBodySetup();
        // These are presentation meshes; placement raycasts authoritative terrain.
        Mesh->GetBodySetup()->bNeverNeedsCookedCollisionData = true;
        UStaticMesh::FBuildMeshDescriptionsParams Params;
        Params.bFastBuild = true; // Runtime path also works outside editor builds.
        Params.bBuildSimpleCollision = false;
        Params.bCommitMeshDescription = false;
        Params.bMarkPackageDirty = false;
        const TArray<const FMeshDescription*> Lods = {&Description};
        if (!Mesh->BuildFromMeshDescriptions(Lods,Params))
        {
            UE_LOG(LogTemp,Error,TEXT("Settlement placeholder mesh could not be built."));
            return nullptr;
        }
        return Mesh;
    }

private:
    FMeshDescription Description;
    FStaticMeshAttributes Attributes;
    FPolygonGroupID Group;
};

void PassiveComponent(UStaticMeshComponent* Component)
{
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCanEverAffectNavigation(false);
    Component->SetCastShadow(false);
    Component->PrimaryComponentTick.bCanEverTick = false;
}

void Tint(UStaticMeshComponent* Component, const FLinearColor& Color)
{
    if (auto* Material = Component->CreateDynamicMaterialInstance(0))
        Material->SetVectorParameterValue(TEXT("Color"),Color);
}

FTransform BasePose(int32 X, int32 Y, int32 Z, int32 Yaw)
{
    return FTransform(FRotator(0,Yaw,0),FVector(X,Y,Z));
}

FTransform BodyPose(const FTransform& Base, int32 Width, int32 Depth, int32 Height)
{
    return FTransform(Base.GetRotation(),Base.GetLocation()+FVector(0,0,Height*WallFraction/2),
        FVector(Width/CubeSize,Depth/CubeSize,Height*WallFraction/CubeSize));
}

FTransform RoofPose(const FTransform& Base, int32 Width, int32 Depth, int32 Height)
{
    // Roof mesh has its eaves at z=0 and ridge at z=100.
    return FTransform(Base.GetRotation(),Base.GetLocation()+FVector(0,0,Height*WallFraction),
        FVector(Width/CubeSize,Depth/CubeSize,Height*(1-WallFraction)/CubeSize));
}

void AddBar(UInstancedStaticMeshComponent* Component, FVector A, FVector B, double Width)
{
    const FVector Direction = B-A;
    const double Length = Direction.Size();
    if (Length<UE_SMALL_NUMBER) return;
    const FQuat Rotation = FQuat::FindBetweenNormals(FVector::ForwardVector,Direction/Length);
    Component->AddInstance(FTransform(Rotation,(A+B)/2,FVector(Length/CubeSize,Width/CubeSize,Width/CubeSize)));
}
}

ASettlementView::ASettlementView()
{
    PrimaryActorTick.bCanEverTick = false;
    SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("SettlementRoot")));
    Terrain = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SettlementTerrain"));
    Bodies = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("BuildingBodies"));
    Roofs = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("BuildingRoofs"));
    Boundary = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("BuildAreaBoundary"));
    PreviewBody = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlacementBody"));
    PreviewRoof = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlacementRoof"));
    PreviewFootprint = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("PlacementFootprint"));
    UStaticMeshComponent* Components[] = {Terrain,Bodies,Roofs,Boundary,PreviewBody,PreviewRoof,PreviewFootprint};
    for (auto* Component : Components)
    {
        Component->SetupAttachment(GetRootComponent());
        PassiveComponent(Component);
    }
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> Material(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    BaseMaterial = Material.Object;
    for (auto* Component : Components) Component->SetMaterial(0,BaseMaterial);
    Bodies->SetStaticMesh(Cube.Object);
    Boundary->SetStaticMesh(Cube.Object);
    PreviewBody->SetStaticMesh(Cube.Object);
    PreviewFootprint->SetStaticMesh(Cube.Object);
    HidePreview();
}

void ASettlementView::PrepareMeshesAndMaterials()
{
    if (!RoofMesh)
    {
        FSurfaceMesh Mesh;
        const FVector3f A(-50,-50,0), B(50,-50,0), C(50,50,0), D(-50,50,0);
        const FVector3f E(-50,0,100), F(50,0,100);
        Mesh.Triangle(A,B,F); Mesh.Triangle(A,F,E);
        Mesh.Triangle(D,E,F); Mesh.Triangle(D,F,C);
        Mesh.Triangle(A,E,D); Mesh.Triangle(B,C,F);
        Mesh.Triangle(A,D,C); Mesh.Triangle(A,C,B);
        RoofMesh = Mesh.Build(this,BaseMaterial);
        Roofs->SetStaticMesh(RoofMesh);
        PreviewRoof->SetStaticMesh(RoofMesh);
        Tint(Bodies,FLinearColor(.55,.39,.22));
        Tint(Roofs,FLinearColor(.22,.26,.28));
        Tint(Terrain,FLinearColor(.29,.38,.22));
        Tint(Boundary,FLinearColor(.95,.69,.16));
    }
    if (!PreviewMaterial)
    {
        PreviewMaterial = UMaterialInstanceDynamic::Create(BaseMaterial,this);
        PreviewBody->SetMaterial(0,PreviewMaterial);
        PreviewRoof->SetMaterial(0,PreviewMaterial);
        PreviewFootprint->SetMaterial(0,PreviewMaterial);
    }
}

void ASettlementView::Rebuild(const domain::World& State)
{
    SetActorTransform(FTransform::Identity);
    PrepareMeshesAndMaterials();
    HidePreview();
    Bodies->ClearInstances();
    Roofs->ClearInstances();
    BuildingTransforms.Reset();
    TArray<FTransform> BodyTransforms, RoofTransforms;
    BodyTransforms.Reserve(int32(State.buildings.size()));
    RoofTransforms.Reserve(int32(State.buildings.size()));
    for (const auto& [Id,Building] : State.buildings)
    {
        const FTransform Base = BasePose(Building.x_cm,Building.y_cm,Building.z_cm,Building.yaw_degrees);
        BuildingTransforms.Add(Id,Base);
        BodyTransforms.Add(BodyPose(Base,Building.width_cm,Building.depth_cm,Building.height_cm));
        RoofTransforms.Add(RoofPose(Base,Building.width_cm,Building.depth_cm,Building.height_cm));
    }
    Bodies->AddInstances(BodyTransforms,false,false,false);
    Roofs->AddInstances(RoofTransforms,false,false,false);
    // Placing another building does not rebuild the unchanged terrain mesh.
    if (!bHasBuiltTerrain || PresentedAreas!=State.build_areas) RebuildTerrain(State);
}

void ASettlementView::RebuildTerrain(const domain::World& State)
{
    FSurfaceMesh Mesh;
    Boundary->ClearInstances();
    BuiltTerrainTriangles = 0;
    for (const auto& [SettlementId,Area] : State.build_areas)
    {
        if (Area.columns<2 || Area.rows<2 || Area.cell_size_cm<=0 ||
            uint64(Area.columns)*Area.rows!=Area.heights_cm.size())
        {
            UE_LOG(LogTemp,Error,TEXT("Settlement %llu has invalid terrain grid dimensions."),SettlementId);
            continue;
        }
        const auto Vertex = [&](uint32 X,uint32 Y)
        {
            return FVector3f(double(Area.origin_x_cm)+double(X)*Area.cell_size_cm,
                double(Area.origin_y_cm)+double(Y)*Area.cell_size_cm,
                Area.heights_cm[std::size_t(Y)*Area.columns+X]);
        };
        for (uint32 Y=0; Y+1<Area.rows; ++Y)
        {
            for (uint32 X=0; X+1<Area.columns; ++X)
            {
                const FVector3f P00=Vertex(X,Y), P10=Vertex(X+1,Y), P11=Vertex(X+1,Y+1), P01=Vertex(X,Y+1);
                // Exactly the DomainCore height-field diagonal, including ramps.
                Mesh.Triangle(P00,P10,P11);
                Mesh.Triangle(P00,P11,P01);
            }
        }
        const auto BoundarySegment = [&](uint32 AX,uint32 AY,uint32 BX,uint32 BY)
        {
            const FVector Lift(0,0,8);
            AddBar(Boundary,FVector(Vertex(AX,AY))+Lift,FVector(Vertex(BX,BY))+Lift,12);
        };
        for (uint32 X=0; X+1<Area.columns; ++X)
        {
            BoundarySegment(X,0,X+1,0);
            BoundarySegment(X,Area.rows-1,X+1,Area.rows-1);
        }
        for (uint32 Y=0; Y+1<Area.rows; ++Y)
        {
            BoundarySegment(0,Y,0,Y+1);
            BoundarySegment(Area.columns-1,Y,Area.columns-1,Y+1);
        }
    }
    TerrainMesh = Mesh.Build(this,BaseMaterial);
    Terrain->SetStaticMesh(TerrainMesh);
    if (TerrainMesh && TerrainMesh->GetRenderData() && !TerrainMesh->GetRenderData()->LODResources.IsEmpty())
        BuiltTerrainTriangles = TerrainMesh->GetRenderData()->LODResources[0].GetNumTriangles();
    PresentedAreas = State.build_areas;
    bHasBuiltTerrain = true;
}

int32 ASettlementView::BuildingCount() const { return Bodies->GetInstanceCount(); }

bool ASettlementView::GetBuildingTransform(uint64 Id, FTransform& Out) const
{
    const FTransform* Transform = BuildingTransforms.Find(Id);
    if (!Transform) return false;
    Out = *Transform;
    return true;
}

double ASettlementView::PreviewHeight(double X, double Y, int32 GroundZ) const
{
    for (const auto& [Id,Area] : PresentedAreas)
    {
        const double Height = domain::TerrainHeightAt(Area,X,Y);
        if (std::isfinite(Height)) return Height;
    }
    return GroundZ;
}

void ASettlementView::SetPreview(const domain::BuildingDefinition& Definition,
    const domain::PlacementCommand& Command, int32 GroundZ, bool bValid)
{
    PrepareMeshesAndMaterials();
    const FTransform Base = BasePose(Command.x_cm,Command.y_cm,GroundZ,Command.yaw_degrees);
    PreviewBody->SetWorldTransform(BodyPose(Base,Definition.width_cm,Definition.depth_cm,Definition.height_cm));
    PreviewRoof->SetWorldTransform(RoofPose(Base,Definition.width_cm,Definition.depth_cm,Definition.height_cm));
    PreviewMaterial->SetVectorParameterValue(TEXT("Color"),bValid ? FLinearColor(.15,.85,.28) : FLinearColor(.95,.12,.08));
    PreviewFootprint->ClearInstances();
    const auto Corners = domain::FootprintCorners(Command.x_cm,Command.y_cm,Definition.width_cm,Definition.depth_cm,Command.yaw_degrees);
    for (std::size_t I=0; I<Corners.size(); ++I)
    {
        const auto& A=Corners[I]; const auto& B=Corners[(I+1)%Corners.size()];
        const double Length=std::hypot(B.x-A.x,B.y-A.y);
        const int32 Segments=FMath::Clamp(FMath::CeilToInt(Length/100),1,64);
        const auto Point = [&](int32 Index)
        {
            const double T=double(Index)/Segments;
            const double X=A.x+(B.x-A.x)*T, Y=A.y+(B.y-A.y)*T;
            return FVector(X,Y,PreviewHeight(X,Y,GroundZ)+10);
        };
        for (int32 Segment=0; Segment<Segments; ++Segment)
            AddBar(PreviewFootprint,Point(Segment),Point(Segment+1),14);
    }
    PreviewBody->SetVisibility(true);
    PreviewRoof->SetVisibility(true);
    PreviewFootprint->SetVisibility(true);
}

void ASettlementView::HidePreview()
{
    PreviewBody->SetVisibility(false);
    PreviewRoof->SetVisibility(false);
    PreviewFootprint->SetVisibility(false);
}
