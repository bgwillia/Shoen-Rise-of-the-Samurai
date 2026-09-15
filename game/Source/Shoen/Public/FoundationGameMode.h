#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "FoundationGameMode.generated.h"
class AFormationView;
class ASettlementView;
UCLASS()
class SHOEN_API AFoundationGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AFoundationGameMode();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    void NewScenario(int32 Soldiers);
    void NewSettlement();
    ASettlementView* SettlementPresentation() const { return SettlementView; }
    int32 LiveInstances() const;
    int32 LiveFormations() const { return Views.Num(); }
private:
    UPROPERTY() TArray<TObjectPtr<AFormationView>> Views;
    UPROPERTY() TObjectPtr<ASettlementView> SettlementView;
    UPROPERTY() TArray<TObjectPtr<AActor>> LabDecorations;
    uint64 SeenGeneration = MAX_uint64;
    void RebuildViews();
    void CreateEnvironment();
    void BenchmarkTick(float DeltaSeconds);
    void FinishBenchmark();
    bool bBenchmark = false;
    int32 RequestedSoldiers = 0;
    double BenchmarkSeconds = 0;
    double BenchmarkStart = 0;
    int32 LastOrder = -1;
    FString BenchmarkOutput;
    TArray<double> FrameTimes;
    TArray<double> SimulationTimes;
    double LastFrameWallTime = 0;
    double LastSimulationMs = 0;
    uint64 PeakMemoryBytes = 0;
};
