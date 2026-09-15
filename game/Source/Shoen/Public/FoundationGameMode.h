#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "FoundationGameMode.generated.h"
class AFormationView;
class ASettlementView;
class ABattlefieldView;
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
    void NewPrototype();
    void FrameCurrentScenario();
    ASettlementView* SettlementPresentation() const { return SettlementView; }
    int32 LiveInstances() const;
    int32 LiveFormations() const { return Views.Num(); }
private:
    friend class FShoenInspectionLifecycle;
    UPROPERTY() TArray<TObjectPtr<AFormationView>> Views;
    UPROPERTY() TObjectPtr<ASettlementView> SettlementView;
    UPROPERTY() TObjectPtr<ABattlefieldView> BattlefieldView;
    UPROPERTY() TArray<TObjectPtr<AActor>> LabDecorations;
    uint64 SeenGeneration = MAX_uint64;
    void RebuildViews();
    void CreateEnvironment();
    void BenchmarkTick(float DeltaSeconds);
    void FinishBenchmark();
    void BeginCombatBenchmark();
    void CombatBenchmarkTick(float DeltaSeconds);
    void FinishCombatBenchmark();
    bool bCombatBenchmark = false;
    bool bTerrainCombatBenchmark=false;
    uint64 CombatPathRequests=0, CombatPathFailures=0, CombatCrossingCompletions=0, CombatBridgeCompletions=0, CombatFordCompletions=0, CombatFlankAttackTicks=0, CombatHillAttackTicks=0;
    uint64 CombatPeakWaiting=0, CombatPeakStuck=0, CombatPeakTerrainOverlap=0;
    int32 CombatPerSide = 0, CombatRuns = 0;
    double CombatSeconds = 0, CombatCaptureSeconds = 0, CombatLastFrameTime = 0;
    double CombatWarmupUntil = 0, CombatNextOrder = 5;
    FString CombatOutput;
    uint64 CombatContactEvents = 0, CombatRangedAttacks = 0;
    int64 CombatPlayerCasualties = 0, CombatEnemyCasualties = 0;
    int32 CombatPeakCongestion = 0, CombatOrders = 0;
    TArray<double> CombatFrameTimes, CombatSimulationTimes;
    TArray<double> CombatCommandTimes;
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
