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
#include <limits>

namespace
{
constexpr double CubeSize = 100.0;
constexpr double WallFraction = 0.7;
const FVector3f RoofVertices[] = {
    {-50,-50,0},{50,-50,0},{50,50,0},{-50,50,0},{-50,0,100},{50,0,100}};
constexpr int32 RoofTriangles[][3] = {
    {0,1,5},{0,5,4},{3,4,5},{3,5,2},{0,4,3},{1,2,5},{0,3,2},{0,2,1}};
constexpr double MinPickDistance = 1.e-6;

bool RayBody(const FVector& Origin, const FVector& Direction, double& Distance)
{
    double Near=-std::numeric_limits<double>::infinity();
    double Far=std::numeric_limits<double>::infinity();
    for (int32 Axis=0; Axis<3; ++Axis)
    {
        if (Direction[Axis]==0)
        {
            if (Origin[Axis]<-CubeSize/2 || Origin[Axis]>CubeSize/2) return false;
            continue;
        }
        double A=(-CubeSize/2-Origin[Axis])/Direction[Axis];
        double B=(CubeSize/2-Origin[Axis])/Direction[Axis];
        if (A>B) std::swap(A,B);
        Near=FMath::Max(Near,A);
        Far=FMath::Min(Far,B);
        if (Near>Far) return false;
    }
    Distance=Near>MinPickDistance ? Near : Far;
    return std::isfinite(Distance) && Distance>MinPickDistance;
}

bool RayRoofTriangle(const FVector& Origin, const FVector& Direction,
    const FVector& A, const FVector& B, const FVector& C, double& Distance)
{
    const FVector AB=B-A, AC=C-A;
    const FVector P=FVector::CrossProduct(Direction,AC);
    const double Determinant=FVector::DotProduct(AB,P);
    if (FMath::Abs(Determinant)<1.e-12) return false;
    const FVector Offset=Origin-A;
    const double U=FVector::DotProduct(Offset,P)/Determinant;
    if (U < -1.e-9 || U > 1+1.e-9) return false;
    const FVector Q=FVector::CrossProduct(Offset,AB);
    const double V=FVector::DotProduct(Direction,Q)/Determinant;
    if (V < -1.e-9 || U+V > 1+1.e-9) return false;
    Distance=FVector::DotProduct(AC,Q)/Determinant;
    return std::isfinite(Distance) && Distance>MinPickDistance;
}

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
    SelectedFootprint = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("BuildingSelectionFootprint"));
    UStaticMeshComponent* Components[] = {Terrain,Bodies,Roofs,Boundary,PreviewBody,PreviewRoof,PreviewFootprint,SelectedFootprint};
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
    SelectedFootprint->SetStaticMesh(Cube.Object);
    SelectedFootprint->SetVisibility(false);
    HidePreview();
}

void ASettlementView::PrepareMeshesAndMaterials()
{
    if (!RoofMesh)
    {
        FSurfaceMesh Mesh;
        for (const auto& Triangle : RoofTriangles)
            Mesh.Triangle(RoofVertices[Triangle[0]],RoofVertices[Triangle[1]],RoofVertices[Triangle[2]]);
        RoofMesh = Mesh.Build(this,BaseMaterial);
        Roofs->SetStaticMesh(RoofMesh);
        PreviewRoof->SetStaticMesh(RoofMesh);
        Tint(Bodies,FLinearColor(.55,.39,.22));
        Tint(Roofs,FLinearColor(.22,.26,.28));
        Tint(Terrain,FLinearColor(.29,.38,.22));
        Tint(Boundary,FLinearColor(.95,.69,.16));
        Tint(SelectedFootprint,FLinearColor(.1,.85,1));
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
    InstanceBuildingIds.Reset();
    InstanceBuildingIds.Reserve(int32(State.buildings.size()));
    TArray<FTransform> BodyTransforms, RoofTransforms;
    BodyTransforms.Reserve(int32(State.buildings.size()));
    RoofTransforms.Reserve(int32(State.buildings.size()));
    for (const auto& [Id,Building] : State.buildings)
    {
        const FTransform Base = BasePose(Building.x_cm,Building.y_cm,Building.z_cm,Building.yaw_degrees);
        BuildingTransforms.Add(Id,Base);
        InstanceBuildingIds.Add(Id);
        BodyTransforms.Add(BodyPose(Base,Building.width_cm,Building.depth_cm,Building.height_cm));
        RoofTransforms.Add(RoofPose(Base,Building.width_cm,Building.depth_cm,Building.height_cm));
    }
    Bodies->AddInstances(BodyTransforms,false,false,false);
    Roofs->AddInstances(RoofTransforms,false,false,false);
    // Placing another building does not rebuild the unchanged terrain mesh.
    if (!bHasBuiltTerrain || PresentedAreas!=State.build_areas) RebuildTerrain(State);
    SetSelectedBuilding(SelectedId,State);
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

bool ASettlementView::PickBuilding(const FVector& Origin, const FVector& Direction, uint64& OutId) const
{
    OutId=0;
    if (Origin.ContainsNaN() || Direction.ContainsNaN()) return false;
    const double Largest=FMath::Max3(FMath::Abs(Direction.X),FMath::Abs(Direction.Y),FMath::Abs(Direction.Z));
    if (Largest==0) return false;
    // Scale first so finite very large/small input directions cannot overflow or
    // underflow during normalization. Local ray parameters remain world distance.
    const FVector ScaledDirection(Direction.X/Largest,Direction.Y/Largest,Direction.Z/Largest);
    const FVector RayDirection=ScaledDirection.GetSafeNormal();
    double Nearest=std::numeric_limits<double>::infinity();
    for (int32 Index=0; Index<InstanceBuildingIds.Num(); ++Index)
    {
        FTransform Body,Roof;
        if (!Bodies->GetInstanceTransform(Index,Body,true) || !Roofs->GetInstanceTransform(Index,Roof,true)) continue;
        double Distance=0;
        if (RayBody(Body.InverseTransformPosition(Origin),Body.InverseTransformVector(RayDirection),Distance) && Distance<Nearest)
        {
            Nearest=Distance;
            OutId=InstanceBuildingIds[Index];
        }
        const FVector RoofOrigin=Roof.InverseTransformPosition(Origin);
        const FVector RoofDirection=Roof.InverseTransformVector(RayDirection);
        for (const auto& Triangle : RoofTriangles)
        {
            if (RayRoofTriangle(RoofOrigin,RoofDirection,FVector(RoofVertices[Triangle[0]]),
                FVector(RoofVertices[Triangle[1]]),FVector(RoofVertices[Triangle[2]]),Distance) && Distance<Nearest)
            {
                Nearest=Distance;
                OutId=InstanceBuildingIds[Index];
            }
        }
    }
    if (OutId==0) return false;
    // A nearer saved terrain triangle hides buildings behind a ridge. This is
    // the same collision-free grid used for the rendered terrain and placement.
    for (const auto& [Id,Area] : PresentedAreas)
    {
        domain::Point3 Hit;
        if (domain::RaycastBuildArea(Area,{Origin.X,Origin.Y,Origin.Z},
            {RayDirection.X,RayDirection.Y,RayDirection.Z},Hit))
        {
            const double Distance=FVector::DotProduct(FVector(Hit.x,Hit.y,Hit.z)-Origin,RayDirection);
            if (Distance>MinPickDistance && Distance<Nearest-MinPickDistance)
            {
                OutId=0;
                return false;
            }
        }
    }
    return true;
}

void ASettlementView::SetSelectedBuilding(uint64 Id, const domain::World& State)
{
    SelectedId=0;
    SelectedFootprint->ClearInstances();
    SelectedFootprint->SetVisibility(false);
    const auto Found=State.buildings.find(Id);
    if (Id==0 || Found==State.buildings.end() || Found->second.id!=Id || !BuildingTransforms.Contains(Id)) return;
    const auto& Building=Found->second;
    RebuildFootprint(SelectedFootprint,Building.x_cm,Building.y_cm,Building.yaw_degrees,
        Building.width_cm,Building.depth_cm,Building.z_cm,18);
    SelectedId=Id;
    SelectedFootprint->SetVisibility(true);
}

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
    RebuildFootprint(PreviewFootprint,Command.x_cm,Command.y_cm,Command.yaw_degrees,
        Definition.width_cm,Definition.depth_cm,GroundZ,14);
    PreviewBody->SetVisibility(true);
    PreviewRoof->SetVisibility(true);
    PreviewFootprint->SetVisibility(true);
}

void ASettlementView::RebuildFootprint(UInstancedStaticMeshComponent* Component, int32 X, int32 Y,
    int32 Yaw, int32 Width, int32 Depth, int32 GroundZ, double LineWidth)
{
    Component->ClearInstances();
    const auto Corners = domain::FootprintCorners(X,Y,Width,Depth,Yaw);
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
            AddBar(Component,Point(Segment),Point(Segment+1),LineWidth);
    }
}

void ASettlementView::HidePreview()
{
    PreviewBody->SetVisibility(false);
    PreviewRoof->SetVisibility(false);
    PreviewFootprint->SetVisibility(false);
}
