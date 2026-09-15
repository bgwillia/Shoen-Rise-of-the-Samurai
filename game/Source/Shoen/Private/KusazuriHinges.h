#pragma once

#include "CoreMinimal.h"

// Armor-only pose channels on the unchanged Manny skeleton. All inputs/outputs
// use native Unreal component-space centimetres. These are not body bone edits.
namespace KusazuriHinges
{
struct FPanel
{
    const TCHAR* Name;
    const TCHAR* Bone;
    double Theta;
    int32 Side; // 0 = both legs, +1 = anatomical left, -1 = right.
};
inline constexpr FPanel Panels[7] = {
    {TEXT("Front_Center"), TEXT("spine_01"), 0, 0},
    {TEXT("Front_L"), TEXT("thigh_l"), .84, 1},
    {TEXT("Front_R"), TEXT("thigh_r"), -.84, -1},
    {TEXT("Side_L"), TEXT("thigh_twist_01_l"), 1.70, 1},
    {TEXT("Side_R"), TEXT("thigh_twist_01_r"), -1.70, -1},
    {TEXT("Rear_L"), TEXT("thigh_twist_02_l"), 2.64, 1},
    {TEXT("Rear_R"), TEXT("thigh_twist_02_r"), -2.64, -1},
};

inline FVector ReflectY(const FVector& Value) { return FVector(Value.X,-Value.Y,Value.Z); }

inline bool Target(int32 PanelIndex, const FTransform& ReferenceBone, const FTransform& ReferencePelvis,
    const FTransform& Pelvis, const FVector& LeftThigh, const FVector& LeftCalf,
    const FVector& RightThigh, const FVector& RightCalf, FTransform& OutTarget, double& OutAngle)
{
    if (PanelIndex < 0 || PanelIndex >= 7 || ReferenceBone.ContainsNaN() || ReferencePelvis.ContainsNaN() ||
        Pelvis.ContainsNaN() || LeftThigh.ContainsNaN() || LeftCalf.ContainsNaN() ||
        RightThigh.ContainsNaN() || RightCalf.ContainsNaN()) return false;
    const auto& Panel = Panels[PanelIndex];
    const FTransform PelvisDelta = ReferencePelvis.Inverse()*Pelvis;
    const FVector LeftDirection = ReflectY(PelvisDelta.GetRotation().UnrotateVector((LeftCalf-LeftThigh).GetSafeNormal()));
    const FVector RightDirection = ReflectY(PelvisDelta.GetRotation().UnrotateVector((RightCalf-RightThigh).GetSafeNormal()));
    if (LeftDirection.IsNearlyZero() || RightDirection.IsNearlyZero()) return false;
    const double Sine = FMath::Sin(Panel.Theta), Cosine = FMath::Cos(Panel.Theta);
    const FVector Radial(Sine,-Cosine,0);
    const FVector& SideDirection = Panel.Side > 0 ? LeftDirection : RightDirection;
    const double SagittalFlex = FMath::Atan2(FMath::Max(0.0,-SideDirection.Y),FMath::Max(.08,-SideDirection.Z));
    FVector Normal = Radial;
    if (PanelIndex == 1 || PanelIndex == 2)
    {
        // High, nearly forward knees swing along the thigh direction. The
        // azimuth guard preserves radial clearance during lateral attacks.
        auto Smooth = [](double Value)
        {
            const double T = FMath::Clamp(Value,0.0,1.0);
            return T*T*(3-2*T);
        };
        const double Azimuth = FMath::Atan2(FMath::Abs(SideDirection.X),FMath::Max(0.0,-SideDirection.Y));
        const double Blend = Smooth((SagittalFlex-FMath::DegreesToRadians(50.0))/FMath::DegreesToRadians(25.0))*
            (1-Smooth((Azimuth-FMath::DegreesToRadians(15.0))/FMath::DegreesToRadians(20.0)));
        const FVector Horizontal = FVector(SideDirection.X,SideDirection.Y,0).GetSafeNormal();
        Normal = FMath::Lerp(Radial,Horizontal,Blend).GetSafeNormal();
    }
    auto Flex = [&](const FVector& Direction)
    {
        return FMath::Atan2(FMath::Max(0.0,FVector::DotProduct(Direction,Normal)), FMath::Max(.08,-Direction.Z));
    };
    const double Flexion = Panel.Side == 0 ? FMath::Max(Flex(LeftDirection),Flex(RightDirection)) :
        Panel.Side > 0 ? Flex(LeftDirection) : Flex(RightDirection);
    OutAngle = FMath::Clamp(Flexion-.02,0.0,UE_PI*.5);
    if (PanelIndex == 3 || PanelIndex == 4)
        OutAngle = FMath::Max(OutAngle,.08*SagittalFlex);
    auto Power = [](double Value) { return FMath::Sign(Value)*FMath::Pow(FMath::Abs(Value),2.0/2.8); };
    const FVector Pivot = ReflectY(FVector(.184*Power(Sine),-.014-.148*Power(Cosine),1.006))*100;
    const FVector Axis = ReflectY(FVector(Normal.Y,-Normal.X,0));
    // Reflection changes handedness, so the native quaternion angle is negated.
    const FTransform Hinge(FQuat(Axis,-OutAngle));
    OutTarget = ReferenceBone*FTransform(-Pivot)*Hinge*FTransform(Pivot)*PelvisDelta;
    return !OutTarget.ContainsNaN() && FMath::IsFinite(OutAngle);
}
}
