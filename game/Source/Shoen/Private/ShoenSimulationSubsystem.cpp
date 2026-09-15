#include "ShoenSimulationSubsystem.h"
#include "domain/SaveCodec.h"
#include "domain/Battle.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"

void UShoenSimulationSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    ResetScenario(0);
}
void UShoenSimulationSubsystem::ResetScenario(int32 Soldiers)
{
    State = Soldiers > 0 ? domain::MakeScaleWorld(Soldiers) : domain::MakeFoundationWorld();
    Message = Soldiers > 0 ? FString::Printf(TEXT("New scale fixture: %d people mobilized from its source population."), Soldiers)
        : TEXT("Accounting fixture: 200 agricultural workers. Press M to mobilize 100.");
    ++ViewGeneration;
}
void UShoenSimulationSubsystem::PrepareForLevel(int32 RequestedSoldiers)
{
    if (!bHasPresentedLevel && RequestedSoldiers > 0) ResetScenario(RequestedSoldiers);
    bHasPresentedLevel = true;
}
void UShoenSimulationSubsystem::Advance(float Seconds)
{
    if (!FMath::IsFinite(Seconds) || Seconds < 0) return;
    const int64 Micros = FMath::RoundToInt64(double(Seconds) * 1000000.0);
    const auto Clock = domain::AdvanceRealTime(State, Micros);
    if (!Clock.ok) Message = UTF8_TO_TCHAR(Clock.error.c_str());
    const auto Movement = domain::StepFormations(State, State.speed == 0 ? 0 : Micros);
    if (!Movement.ok) Message = UTF8_TO_TCHAR(Movement.error.c_str());
}
bool UShoenSimulationSubsystem::Report(const domain::Result& Result, const FString& Success)
{
    Message = Result.ok ? Success : UTF8_TO_TCHAR(Result.error.c_str());
    return Result.ok;
}
void UShoenSimulationSubsystem::SetGameSpeed(int32 Speed)
{
    Report(domain::SetSpeed(State, Speed), Speed == 0 ? TEXT("Campaign paused.") : FString::Printf(TEXT("Campaign speed %dx; fixed one-day steps."), Speed));
}
bool UShoenSimulationSubsystem::MobilizeProof()
{
    if (State.initial_population != 200) { Message = TEXT("Use the Accounting fixture for this proof."); return false; }
    if (!State.formations.empty()) { Message = TEXT("Reset the accounting fixture before mobilizing again."); return false; }
    const bool Okay = Report(domain::Mobilize(State, 3, 100), TEXT("100 mobilized; only 100 workers remain available. Press O for scripted outcome."));
    if (Okay) ++ViewGeneration;
    return Okay;
}
bool UShoenSimulationSubsystem::ResolveProof()
{
    if (State.initial_population != 200 || State.formations.size() != 1) { Message = TEXT("Mobilize the accounting fixture first."); return false; }
    const auto& Formation = State.formations.begin()->second;
    domain::Outcome Outcome;
    // This named transaction stays stable across retry and reload; it is a laboratory fixture, not combat.
    Outcome.transaction_id = 1;
    Outcome.formation_id = Formation.id;
    Outcome.expected_revision = State.revision;
    int32 Index = 0;
    for (auto Id : Formation.service_ids)
    {
        Outcome.dispositions.push_back({Id, Index < 20 ? domain::ServiceStatus::Dead : Index < 35 ? domain::ServiceStatus::WoundedAway : domain::ServiceStatus::Active});
        ++Index;
    }
    const bool Okay = Report(domain::ApplyOutcome(State, Outcome), TEXT("Scripted proof: 20 dead, 15 wounded, 65 healthy. Use Return survivors or Backspace."));
    if (Okay) ++ViewGeneration;
    return Okay;
}
bool UShoenSimulationSubsystem::DemobilizeProof()
{
    if (State.initial_population != 200 || State.formations.size() != 1) { Message = TEXT("Mobilize the accounting fixture first."); return false; }
    const bool Okay = Report(domain::Demobilize(State, State.formations.begin()->first), TEXT("Survivors returned to their origin cohort. Wounded remain unavailable."));
    if (Okay) ++ViewGeneration;
    return Okay;
}
bool UShoenSimulationSubsystem::SaveToPath(const FString& Path)
{
    const auto Bytes = domain::EncodeSnapshot(State);
    if (Bytes.empty()) { Message = TEXT("Save rejected: invalid simulation state."); return false; }
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path), true);
    const FString Temp = Path + TEXT(".tmp");
    if (!FFileHelper::SaveArrayToFile(TArrayView<const uint8>(Bytes.data(), int32(Bytes.size())), *Temp))
    { Message = TEXT("Could not write temporary save."); return false; }
    if (IFileManager::Get().FileExists(*Path) && IFileManager::Get().Copy(*(Path + TEXT(".bak")), *Path, true, true) != COPY_OK)
    { Message = TEXT("Could not preserve save backup; original kept."); return false; }
    if (!IFileManager::Get().Move(*Path, *Temp, true, true))
    { Message = TEXT("Could not replace save; backup is available."); return false; }
    Message = TEXT("Saved the full simulation, origins, clock and formation orders.");
    return true;
}
bool UShoenSimulationSubsystem::LoadFromPath(const FString& Path)
{
    const int64 Size = IFileManager::Get().FileSize(*Path);
    if (Size <= 0 || Size > int64(domain::MaxSnapshotBytes))
    { Message = TEXT("Save missing or exceeds the size limit. Current state kept."); return false; }
    TArray<uint8> Bytes;
    if (!FFileHelper::LoadFileToArray(Bytes, *Path)) { Message = TEXT("Could not read save. Current state kept."); return false; }
    const bool Okay = Report(domain::LoadSnapshot(State, std::span<const uint8>(Bytes.GetData(), Bytes.Num())), TEXT("Loaded saved date, population, resources and formations."));
    if (Okay) ++ViewGeneration;
    return Okay;
}
bool UShoenSimulationSubsystem::Save() { return SaveToPath(FPaths::ProjectSavedDir() / TEXT("SaveGames/Foundation.sav")); }
bool UShoenSimulationSubsystem::Load() { return LoadFromPath(FPaths::ProjectSavedDir() / TEXT("SaveGames/Foundation.sav")); }
