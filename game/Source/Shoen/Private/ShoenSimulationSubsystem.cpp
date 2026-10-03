#include "ShoenSimulationSubsystem.h"
#include "BuildingContent.h"
#include "domain/Buildings.h"
#include "domain/SaveCodec.h"
#include "domain/Battle.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "InteractionProfiler.h"
#include "domain/ProfilingFixture.h"
#include "TerrainSuitability.h"

void UShoenSimulationSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    ResetScenario(0);
}
void UShoenSimulationSubsystem::ResetScenario(int32 Soldiers)
{
    if (IsProfilingFixture()) { Message=TEXT("End the profiling fixture before resetting the scenario."); return; }
    State = Soldiers > 0 ? domain::MakeScaleWorld(Soldiers) : domain::MakeFoundationWorld();
    Prototype = {};
    BuildingCatalog.clear();
    Message = Soldiers > 0 ? FString::Printf(TEXT("New scale fixture: %d people mobilized from its source population."), Soldiers)
        : TEXT("Accounting fixture: 200 agricultural workers. Press M to mobilize 100.");
    ++ViewGeneration;
    ++WorldGeneration;
}
bool UShoenSimulationSubsystem::ResetSettlement()
{
    if (IsProfilingFixture()) { Message=TEXT("End the profiling fixture before resetting the settlement."); return false; }
    domain::BuildingCatalog CandidateCatalog;
    domain::BuildArea CandidateArea;
    int64 Timber = 0;
    int64 Treasury = 0;
    FString Error;
    if (!LoadSettlementContent(CandidateCatalog, CandidateArea, Timber, Treasury, Error))
    {
        Message = FString::Printf(TEXT("Settlement content rejected: %s Current state kept."), *Error);
        return false;
    }

    domain::World Candidate = domain::MakeFoundationWorld();
    const auto Settlement = Candidate.settlements.find(CandidateArea.settlement_id);
    if (Settlement == Candidate.settlements.end())
    {
        Message = TEXT("Settlement content rejected: build area references an unknown settlement. Current state kept.");
        return false;
    }
    Settlement->second.resources.timber = Timber;
    Settlement->second.resources.treasury = Treasury;
    if (auto* Suitability=ATerrainSuitability::Find(GetWorld()))
    {
        Suitability->InitializeSources();
        CandidateArea=Suitability->MakeBuildArea(CandidateArea.settlement_id);
    }
    Candidate.build_areas.emplace(CandidateArea.settlement_id, std::move(CandidateArea));
    const domain::Result WorldValidation = domain::ValidateWorld(Candidate);
    const domain::Result BuildingValidation = domain::ValidateBuildingState(Candidate);
    if (!WorldValidation.ok || !BuildingValidation.ok)
    {
        const std::string& DomainMessage = !WorldValidation.ok ? WorldValidation.error : BuildingValidation.error;
        Message = FString::Printf(
            TEXT("Settlement content rejected: %s Current state kept."),
            UTF8_TO_TCHAR(DomainMessage.c_str()));
        return false;
    }

    State = std::move(Candidate);
    Prototype = {};
    BuildingCatalog = std::move(CandidateCatalog);
    const domain::BuildingDefinition& Storehouse = BuildingCatalog.at("small_storehouse");
    Message = FString::Printf(
        TEXT("Settlement fixture: %s costs %lld timber and %lld treasury. Press B to place."),
        UTF8_TO_TCHAR(Storehouse.display_name.c_str()),
        Storehouse.timber_cost,
        Storehouse.treasury_cost);
    if (ATerrainSuitability::Find(GetWorld())) Message=TEXT("TerrainBase_01: B places a building using terrain rules. F8 cycles suitability; Home frames the village.");
    ++ViewGeneration;
    ++WorldGeneration;
    return true;
}
void UShoenSimulationSubsystem::PrepareForLevel(int32 RequestedSoldiers)
{
    if (!bHasPresentedLevel && RequestedSoldiers > 0) ResetScenario(RequestedSoldiers);
    bHasPresentedLevel = true;
}
bool UShoenSimulationSubsystem::PrepareSettlementForLevel()
{
    if (!bHasPresentedLevel && !IsSettlement() && !ResetSettlement())
    {
        return false;
    }
    bHasPresentedLevel = true;
    if (!IsSettlement())
    {
        Message = TEXT("Settlement fixture was not prepared; current simulation state kept.");
        return false;
    }
    return true;
}
domain::PlacementResult UShoenSimulationSubsystem::PreviewBuilding(const domain::PlacementCommand& Command) const
{
    auto Result=domain::EvaluatePlacement(State, BuildingCatalog, Command);
    // Early overlap/bounds failures still need the native ground height so the
    // existing red preview remains visible at the attempted location.
    if (const auto* Suitability=ATerrainSuitability::Find(GetWorld()))
    {
        const auto Sample=Suitability->Query(FVector(Command.x_cm,Command.y_cm,0));
        if (Sample.bInside) Result.ground_z_cm=FMath::RoundToInt(Sample.Position.Z);
    }
    return Result;
}
domain::PlacementResult UShoenSimulationSubsystem::PlaceBuilding(const domain::PlacementCommand& Command)
{
    domain::PlacementObserver Observer;
    if (ShoenProfile::IsCapturing()) Observer.on_stage=[](domain::PlacementTraceStage Stage,void*)
    {
        const TCHAR* Name=TEXT("unknown");
        switch (Stage)
        {
        case domain::PlacementTraceStage::InitialValidationBegin: Name=TEXT("initial_validation_begin"); break;
        case domain::PlacementTraceStage::InitialValidationEnd: Name=TEXT("initial_validation_end"); break;
        case domain::PlacementTraceStage::PlacementValidationBegin: Name=TEXT("validation_begin"); break;
        case domain::PlacementTraceStage::PlacementValidationEnd: Name=TEXT("validation_end"); break;
        case domain::PlacementTraceStage::CandidateCopyBegin: Name=TEXT("candidate_copy_begin"); break;
        case domain::PlacementTraceStage::CandidateCopyEnd: Name=TEXT("candidate_copy_end"); break;
        case domain::PlacementTraceStage::CandidateValidationBegin: Name=TEXT("candidate_validation_begin"); break;
        case domain::PlacementTraceStage::CandidateValidationEnd: Name=TEXT("candidate_validation_end"); break;
        case domain::PlacementTraceStage::Committed: Name=TEXT("transaction_committed"); break;
        }
        ShoenProfile::Mark(Name);
        if (Stage==domain::PlacementTraceStage::Committed) ShoenProfile::Mark(TEXT("resources_updated"));
    };
    const domain::PlacementResult Result = domain::PlaceBuilding(State, BuildingCatalog, Command,Observer);
    Message = UTF8_TO_TCHAR(domain::PlacementReason(Result.code));
    ShoenProfile::SetKind(Result.ok ? TEXT("place_success") : TEXT("place_reject"));
    ShoenProfile::SetEntity(Result.building_id);
    if (Result.ok && Result.code == domain::PlacementCode::Valid)
    {
        ++ViewGeneration;
        PendingPlacementProfile=ShoenProfile::CurrentEvent();
        ShoenProfile::Mark(TEXT("presentation_rebuild_requested"));
    }
    else
    {
        ShoenProfile::ExpectMessage(Message);
        ShoenProfile::VisualReady(ShoenProfile::CurrentEvent(),ShoenProfile::EVisualChannel::Message,false,true);
    }
    return Result;
}
void UShoenSimulationSubsystem::Advance(float Seconds)
{
    if (!FMath::IsFinite(Seconds) || Seconds < 0) return;
    const int64 Micros = FMath::RoundToInt64(double(Seconds) * 1000000.0);
    if (Prototype.enabled)
    {
        const auto PreviousPhase = Prototype.phase;
        const auto Result = domain::AdvancePrototype(State, Prototype, Micros);
        if (!Result.ok) Message = UTF8_TO_TCHAR(Result.error.c_str());
        else if (PreviousPhase != Prototype.phase)
            Message = FString::Printf(TEXT("%s. H: return survivors and apply casualties to their home occupations."), UTF8_TO_TCHAR(domain::BattlePhaseName(Prototype.phase)));
        return;
    }
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
    if (IsPrototypeBattle())
    {
        Report(domain::SetSpeed(State, Speed == 0 ? 0 : 1), Speed == 0 ? TEXT("Battle paused. Campaign time stays frozen.") : TEXT("Battle running at 1x. Campaign time stays frozen."));
        return;
    }
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
    if (ATerrainSuitability::Find(GetWorld())) { Message=TEXT("Terrain suitability is session-only. Existing save slots are preserved."); return false; }
    if (Prototype.enabled) { Message=TEXT("Core-loop prototype is session-only. Existing foundation/settlement saves are separate."); return false; }
    if (IsProfilingFixture()) { Message=TEXT("Profiling fixture is transient; saving is disabled until it ends."); return false; }
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
    Message = TEXT("Saved the full simulation, origins, clock, formation orders and buildings.");
    return true;
}
bool UShoenSimulationSubsystem::LoadFromPath(const FString& Path)
{
    if (ATerrainSuitability::Find(GetWorld())) { Message=TEXT("Terrain suitability is session-only. N starts a fresh settlement on this landscape."); return false; }
    if (Prototype.enabled) { Message=TEXT("Prototype persistence is deferred. N starts a fresh core-loop session."); return false; }
    if (IsProfilingFixture()) { Message=TEXT("End the transient profiling fixture before loading."); return false; }
    const int64 Size = IFileManager::Get().FileSize(*Path);
    if (Size <= 0 || Size > int64(domain::MaxSnapshotBytes))
    { Message = TEXT("Save missing or exceeds the size limit. Current state kept."); return false; }
    TArray<uint8> Bytes;
    if (!FFileHelper::LoadFileToArray(Bytes, *Path)) { Message = TEXT("Could not read save. Current state kept."); return false; }
    domain::DecodeResult Decoded = domain::DecodeSnapshot(std::span<const uint8>(Bytes.GetData(), Bytes.Num()));
    if (!Decoded.ok)
    {
        Message = UTF8_TO_TCHAR(Decoded.error.c_str());
        return false;
    }

    domain::BuildingCatalog CandidateCatalog;
    if (!Decoded.world.build_areas.empty() || !Decoded.world.buildings.empty())
    {
        FString Error;
        if (!LoadBuildingCatalog(CandidateCatalog, Error))
        {
            Message = FString::Printf(TEXT("Saved settlement content unavailable: %s Current state kept."), *Error);
            return false;
        }
        for (const auto& [BuildingId, Building] : Decoded.world.buildings)
        {
            const auto Definition = CandidateCatalog.find(Building.definition_id);
            if (Definition == CandidateCatalog.end() || Definition->second.version < Building.definition_version)
            {
                Message = FString::Printf(
                    TEXT("Save references unavailable building definition '%s' version %u. Current state kept."),
                    UTF8_TO_TCHAR(Building.definition_id.c_str()),
                    Building.definition_version);
                return false;
            }
        }
        const domain::Result Validation = domain::ValidateBuildingState(Decoded.world);
        if (!Validation.ok)
        {
            Message = FString::Printf(
                TEXT("Saved settlement rejected: %s Current state kept."),
                UTF8_TO_TCHAR(Validation.error.c_str()));
            return false;
        }
    }

    State = std::move(Decoded.world);
    BuildingCatalog = std::move(CandidateCatalog);
    Message = TEXT("Loaded saved date, population, resources, formations and buildings.");
    ++ViewGeneration;
    ++WorldGeneration;
    return true;
}
bool UShoenSimulationSubsystem::Save()
{
    return SaveToPath(FPaths::ProjectSavedDir() / (IsSettlement() ? TEXT("SaveGames/Settlement.sav") : TEXT("SaveGames/Foundation.sav")));
}
bool UShoenSimulationSubsystem::Load()
{
    return LoadFromPath(FPaths::ProjectSavedDir() / (IsSettlement() ? TEXT("SaveGames/Settlement.sav") : TEXT("SaveGames/Foundation.sav")));
}
bool UShoenSimulationSubsystem::BeginProfilingFixture(int32 BuildingCount)
{
#if UE_BUILD_SHIPPING
    return false;
#else
    if (IsProfilingFixture() || Prototype.enabled) return false;
    domain::World Candidate;
    const auto Result=domain::MakeProfilingFixture(BuildingCatalog,BuildingCount,Candidate);
    if (!Result.ok) return false;
    ProfilingOriginal=MakeUnique<domain::World>(State);
    ProfilingOriginalCatalog=BuildingCatalog;
    ProfilingOriginalMessage=Message;
    ProfilingBaseline=MakeUnique<domain::World>(std::move(Candidate));
    return RestoreProfilingBaseline();
#endif
}
bool UShoenSimulationSubsystem::RestoreProfilingBaseline()
{
    if (!IsProfilingFixture() || !ProfilingBaseline) return false;
    State=*ProfilingBaseline;
    Message=TEXT("Transient latency fixture. Normal saves are protected.");
    PendingPlacementProfile=0;
    ++WorldGeneration; ++ViewGeneration;
    return true;
}
void UShoenSimulationSubsystem::EndProfilingFixture()
{
    if (!IsProfilingFixture()) return;
    State=std::move(*ProfilingOriginal);
    BuildingCatalog=std::move(ProfilingOriginalCatalog);
    Message=ProfilingOriginalMessage;
    ProfilingOriginal.Reset(); ProfilingBaseline.Reset(); ProfilingOriginalMessage.Reset();
    PendingPlacementProfile=0;
    ++WorldGeneration; ++ViewGeneration;
}
