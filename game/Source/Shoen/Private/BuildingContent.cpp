#include "BuildingContent.h"

#include "Dom/JsonObject.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "domain/Buildings.h"

#include <cmath>
#include <limits>

namespace
{
bool Reject(FString& OutError, const FString& Context, const FString& Detail)
{
    OutError = FString::Printf(TEXT("%s: %s"), *Context, *Detail);
    return false;
}

bool ParseObject(const FString& Json, TSharedPtr<FJsonObject>& OutObject, FString& OutError, const FString& Context)
{
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Json);
    if (!FJsonSerializer::Deserialize(Reader, OutObject) || !OutObject.IsValid())
    {
        return Reject(OutError, Context, TEXT("expected a valid JSON object"));
    }
    return true;
}

bool CheckFields(
    const TSharedPtr<FJsonObject>& Object,
    std::initializer_list<const TCHAR*> Allowed,
    std::initializer_list<const TCHAR*> Required,
    FString& OutError,
    const FString& Context)
{
    TSet<FString> AllowedNames;
    for (const TCHAR* Name : Allowed)
    {
        AllowedNames.Add(Name);
    }
    for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : Object->Values)
    {
        if (!AllowedNames.Contains(Pair.Key))
        {
            return Reject(OutError, Context, FString::Printf(TEXT("unknown field '%s'"), *Pair.Key));
        }
    }
    for (const TCHAR* Name : Required)
    {
        if (!Object->Values.Contains(Name))
        {
            return Reject(OutError, Context, FString::Printf(TEXT("missing field '%s'"), Name));
        }
    }
    return true;
}

bool ReadString(
    const TSharedPtr<FJsonObject>& Object,
    const TCHAR* Name,
    int32 MaxLength,
    FString& OutValue,
    FString& OutError,
    const FString& Context)
{
    const TSharedPtr<FJsonValue>* Value = Object->Values.Find(Name);
    if (Value == nullptr || !Value->IsValid() || (*Value)->Type != EJson::String)
    {
        return Reject(OutError, Context, FString::Printf(TEXT("field '%s' must be a string"), Name));
    }
    OutValue = (*Value)->AsString();
    if (OutValue.IsEmpty() || OutValue.Len() > MaxLength)
    {
        return Reject(
            OutError,
            Context,
            FString::Printf(TEXT("field '%s' length must be between 1 and %d"), Name, MaxLength));
    }
    return true;
}

bool ReadInteger(
    const TSharedPtr<FJsonObject>& Object,
    const TCHAR* Name,
    int64 Minimum,
    int64 Maximum,
    int64& OutValue,
    FString& OutError,
    const FString& Context)
{
    const TSharedPtr<FJsonValue>* Value = Object->Values.Find(Name);
    if (Value == nullptr || !Value->IsValid() || (*Value)->Type != EJson::Number)
    {
        return Reject(OutError, Context, FString::Printf(TEXT("field '%s' must be an integer"), Name));
    }
    const double Number = (*Value)->AsNumber();
    if (!FMath::IsFinite(Number) || std::floor(Number) != Number || Number < double(Minimum) || Number > double(Maximum))
    {
        return Reject(
            OutError,
            Context,
            FString::Printf(TEXT("field '%s' must be an integer from %lld to %lld"), Name, Minimum, Maximum));
    }
    OutValue = static_cast<int64>(Number);
    return true;
}

bool ReadObject(
    const TSharedPtr<FJsonObject>& Object,
    const TCHAR* Name,
    TSharedPtr<FJsonObject>& OutValue,
    FString& OutError,
    const FString& Context)
{
    const TSharedPtr<FJsonValue>* Value = Object->Values.Find(Name);
    if (Value == nullptr || !Value->IsValid() || (*Value)->Type != EJson::Object)
    {
        return Reject(OutError, Context, FString::Printf(TEXT("field '%s' must be an object"), Name));
    }
    OutValue = (*Value)->AsObject();
    return OutValue.IsValid() || Reject(OutError, Context, FString::Printf(TEXT("field '%s' is invalid"), Name));
}

bool ReadArray(
    const TSharedPtr<FJsonObject>& Object,
    const TCHAR* Name,
    const TArray<TSharedPtr<FJsonValue>>*& OutValue,
    FString& OutError,
    const FString& Context)
{
    const TSharedPtr<FJsonValue>* Value = Object->Values.Find(Name);
    if (Value == nullptr || !Value->IsValid() || (*Value)->Type != EJson::Array)
    {
        return Reject(OutError, Context, FString::Printf(TEXT("field '%s' must be an array"), Name));
    }
    OutValue = &(*Value)->AsArray();
    return true;
}

FString DomainError(const std::string& Error)
{
    return FString(UTF8_TO_TCHAR(Error.c_str()));
}

bool ParseSettlementFixture(
    const FString& Json,
    domain::BuildArea& OutBuildArea,
    int64& OutTimber,
    int64& OutTreasury,
    FString& OutError)
{
    const FString RootContext = TEXT("settlement_fixture.json");
    TSharedPtr<FJsonObject> Root;
    if (!ParseObject(Json, Root, OutError, RootContext)
        || !CheckFields(
            Root,
            {TEXT("schema_version"), TEXT("settlement_id"), TEXT("timber"), TEXT("treasury"), TEXT("build_area")},
            {TEXT("schema_version"), TEXT("settlement_id"), TEXT("timber"), TEXT("treasury"), TEXT("build_area")},
            OutError,
            RootContext))
    {
        return false;
    }

    int64 SchemaVersion = 0;
    int64 SettlementId = 0;
    int64 Timber = 0;
    int64 Treasury = 0;
    if (!ReadInteger(Root, TEXT("schema_version"), 1, 1, SchemaVersion, OutError, RootContext)
        || !ReadInteger(Root, TEXT("settlement_id"), 1, 9'007'199'254'740'991LL, SettlementId, OutError, RootContext)
        || !ReadInteger(Root, TEXT("timber"), 0, 1'000'000'000'000LL, Timber, OutError, RootContext)
        || !ReadInteger(Root, TEXT("treasury"), 0, 1'000'000'000'000LL, Treasury, OutError, RootContext))
    {
        return false;
    }

    TSharedPtr<FJsonObject> AreaObject;
    const FString AreaContext = TEXT("settlement_fixture.json.build_area");
    if (!ReadObject(Root, TEXT("build_area"), AreaObject, OutError, RootContext)
        || !CheckFields(
            AreaObject,
            {TEXT("origin_x_cm"), TEXT("origin_y_cm"), TEXT("cell_size_cm"), TEXT("columns"), TEXT("rows"), TEXT("heights_cm")},
            {TEXT("origin_x_cm"), TEXT("origin_y_cm"), TEXT("cell_size_cm"), TEXT("columns"), TEXT("rows"), TEXT("heights_cm")},
            OutError,
            AreaContext))
    {
        return false;
    }

    int64 OriginX = 0;
    int64 OriginY = 0;
    int64 CellSize = 0;
    int64 Columns = 0;
    int64 Rows = 0;
    if (!ReadInteger(AreaObject, TEXT("origin_x_cm"), MIN_int32, MAX_int32, OriginX, OutError, AreaContext)
        || !ReadInteger(AreaObject, TEXT("origin_y_cm"), MIN_int32, MAX_int32, OriginY, OutError, AreaContext)
        || !ReadInteger(AreaObject, TEXT("cell_size_cm"), 1, MAX_int32, CellSize, OutError, AreaContext)
        || !ReadInteger(AreaObject, TEXT("columns"), 2, int64(domain::MaxTerrainVertices), Columns, OutError, AreaContext)
        || !ReadInteger(AreaObject, TEXT("rows"), 2, int64(domain::MaxTerrainVertices), Rows, OutError, AreaContext)
        || uint64(Columns) > uint64(domain::MaxTerrainVertices) / uint64(Rows))
    {
        if (OutError.IsEmpty())
        {
            Reject(OutError, AreaContext, TEXT("columns times rows exceeds the terrain vertex limit"));
        }
        return false;
    }

    const TArray<TSharedPtr<FJsonValue>>* Heights = nullptr;
    if (!ReadArray(AreaObject, TEXT("heights_cm"), Heights, OutError, AreaContext))
    {
        return false;
    }
    const int64 ExpectedHeights = Columns * Rows;
    if (Heights->Num() != ExpectedHeights)
    {
        return Reject(
            OutError,
            AreaContext,
            FString::Printf(TEXT("heights_cm must contain exactly %lld values"), ExpectedHeights));
    }

    domain::BuildArea Candidate;
    Candidate.settlement_id = static_cast<uint64>(SettlementId);
    Candidate.origin_x_cm = static_cast<int32>(OriginX);
    Candidate.origin_y_cm = static_cast<int32>(OriginY);
    Candidate.cell_size_cm = static_cast<int32>(CellSize);
    Candidate.columns = static_cast<uint32>(Columns);
    Candidate.rows = static_cast<uint32>(Rows);
    Candidate.heights_cm.reserve(static_cast<size_t>(ExpectedHeights));
    for (int32 Index = 0; Index < Heights->Num(); ++Index)
    {
        const TSharedPtr<FJsonValue>& Value = (*Heights)[Index];
        if (!Value.IsValid() || Value->Type != EJson::Number)
        {
            return Reject(
                OutError,
                AreaContext,
                FString::Printf(TEXT("heights_cm[%d] must be an integer"), Index));
        }
        const double Number = Value->AsNumber();
        if (!FMath::IsFinite(Number) || std::floor(Number) != Number || Number < MIN_int32 || Number > MAX_int32)
        {
            return Reject(
                OutError,
                AreaContext,
                FString::Printf(TEXT("heights_cm[%d] is outside the int32 range"), Index));
        }
        Candidate.heights_cm.push_back(static_cast<int32>(Number));
    }

    domain::World ValidationWorld = domain::MakeFoundationWorld();
    const auto Settlement = ValidationWorld.settlements.find(Candidate.settlement_id);
    if (Settlement == ValidationWorld.settlements.end())
    {
        return Reject(OutError, RootContext, TEXT("settlement_id does not reference the foundation settlement"));
    }
    Settlement->second.resources.timber = Timber;
    Settlement->second.resources.treasury = Treasury;
    ValidationWorld.build_areas.emplace(Candidate.settlement_id, Candidate);
    const domain::Result Validation = domain::ValidateBuildingState(ValidationWorld);
    if (!Validation.ok)
    {
        return Reject(OutError, RootContext, DomainError(Validation.error));
    }

    OutBuildArea = std::move(Candidate);
    OutTimber = Timber;
    OutTreasury = Treasury;
    OutError.Reset();
    return true;
}
}

bool ParseBuildingCatalog(
    const FString& Json,
    domain::BuildingCatalog& OutCatalog,
    FString& OutError)
{
    const FString RootContext = TEXT("buildings.json");
    TSharedPtr<FJsonObject> Root;
    if (!ParseObject(Json, Root, OutError, RootContext)
        || !CheckFields(
            Root,
            {TEXT("schema_version"), TEXT("buildings")},
            {TEXT("schema_version"), TEXT("buildings")},
            OutError,
            RootContext))
    {
        return false;
    }

    int64 SchemaVersion = 0;
    if (!ReadInteger(Root, TEXT("schema_version"), 1, 1, SchemaVersion, OutError, RootContext))
    {
        return false;
    }
    const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
    if (!ReadArray(Root, TEXT("buildings"), Values, OutError, RootContext)
        || Values->IsEmpty()
        || Values->Num() > int32(domain::MaxBuildings))
    {
        if (OutError.IsEmpty())
        {
            Reject(
                OutError,
                RootContext,
                FString::Printf(TEXT("buildings must contain between 1 and %zu definitions"), domain::MaxBuildings));
        }
        return false;
    }

    domain::BuildingCatalog Candidate;
    for (int32 Index = 0; Index < Values->Num(); ++Index)
    {
        const TSharedPtr<FJsonValue>& JsonValue = (*Values)[Index];
        const FString Context = FString::Printf(TEXT("buildings.json.buildings[%d]"), Index);
        if (!JsonValue.IsValid() || JsonValue->Type != EJson::Object)
        {
            return Reject(OutError, Context, TEXT("definition must be an object"));
        }
        const TSharedPtr<FJsonObject> Object = JsonValue->AsObject();
        if (!CheckFields(
            Object,
            {
                TEXT("id"), TEXT("display_name"), TEXT("version"), TEXT("width_cm"), TEXT("depth_cm"),
                TEXT("height_cm"), TEXT("rotation_step_degrees"), TEXT("max_height_variation_cm"),
                TEXT("max_slope_permille"), TEXT("timber_cost"), TEXT("treasury_cost")
            },
            {
                TEXT("id"), TEXT("display_name"), TEXT("version"), TEXT("width_cm"), TEXT("depth_cm"),
                TEXT("height_cm"), TEXT("rotation_step_degrees"), TEXT("max_height_variation_cm"),
                TEXT("max_slope_permille"), TEXT("timber_cost"), TEXT("treasury_cost")
            },
            OutError,
            Context))
        {
            return false;
        }

        FString Id;
        FString DisplayName;
        int64 Version = 0;
        int64 Width = 0;
        int64 Depth = 0;
        int64 Height = 0;
        int64 RotationStep = 0;
        int64 MaxHeightVariation = 0;
        int64 MaxSlope = 0;
        int64 TimberCost = 0;
        int64 TreasuryCost = 0;
        if (!ReadString(Object, TEXT("id"), 128, Id, OutError, Context)
            || !ReadString(Object, TEXT("display_name"), 128, DisplayName, OutError, Context)
            || !ReadInteger(Object, TEXT("version"), 1, MAX_uint32, Version, OutError, Context)
            || !ReadInteger(Object, TEXT("width_cm"), 1, MAX_int32, Width, OutError, Context)
            || !ReadInteger(Object, TEXT("depth_cm"), 1, MAX_int32, Depth, OutError, Context)
            || !ReadInteger(Object, TEXT("height_cm"), 1, MAX_int32, Height, OutError, Context)
            || !ReadInteger(Object, TEXT("rotation_step_degrees"), 1, 360, RotationStep, OutError, Context)
            || !ReadInteger(Object, TEXT("max_height_variation_cm"), 0, MAX_int32, MaxHeightVariation, OutError, Context)
            || !ReadInteger(Object, TEXT("max_slope_permille"), 0, MAX_int32, MaxSlope, OutError, Context)
            || !ReadInteger(Object, TEXT("timber_cost"), 0, 1'000'000'000'000LL, TimberCost, OutError, Context)
            || !ReadInteger(Object, TEXT("treasury_cost"), 0, 1'000'000'000'000LL, TreasuryCost, OutError, Context))
        {
            return false;
        }

        domain::BuildingDefinition Definition;
        Definition.id = TCHAR_TO_UTF8(*Id);
        Definition.display_name = TCHAR_TO_UTF8(*DisplayName);
        Definition.version = static_cast<uint32>(Version);
        Definition.width_cm = static_cast<int32>(Width);
        Definition.depth_cm = static_cast<int32>(Depth);
        Definition.height_cm = static_cast<int32>(Height);
        Definition.rotation_step_degrees = static_cast<int32>(RotationStep);
        Definition.max_height_variation_cm = static_cast<int32>(MaxHeightVariation);
        Definition.max_slope_permille = static_cast<int32>(MaxSlope);
        Definition.timber_cost = TimberCost;
        Definition.treasury_cost = TreasuryCost;
        if (!Candidate.emplace(Definition.id, std::move(Definition)).second)
        {
            return Reject(OutError, Context, FString::Printf(TEXT("duplicate building id '%s'"), *Id));
        }
    }

    const domain::Result Validation = domain::ValidateBuildingCatalog(Candidate);
    if (!Validation.ok)
    {
        return Reject(OutError, RootContext, DomainError(Validation.error));
    }
    OutCatalog = std::move(Candidate);
    OutError.Reset();
    return true;
}

bool LoadSettlementContent(
    domain::BuildingCatalog& OutCatalog,
    domain::BuildArea& OutBuildArea,
    int64& OutTimber,
    int64& OutTreasury,
    FString& OutError)
{
    domain::BuildingCatalog CandidateCatalog;
    if (!LoadBuildingCatalog(CandidateCatalog, OutError))
    {
        return false;
    }
    if (!CandidateCatalog.contains("small_storehouse"))
    {
        return Reject(OutError, TEXT("settlement content"), TEXT("missing required building 'small_storehouse'"));
    }

    const FString DataDirectory = FPaths::ProjectContentDir() / TEXT("Domain/Data");
    FString FixtureJson;
    const FString FixturePath = DataDirectory / TEXT("settlement_fixture.json");
    if (!FFileHelper::LoadFileToString(FixtureJson, *FixturePath))
    {
        return Reject(OutError, TEXT("settlement content"), FString::Printf(TEXT("could not read %s"), *FixturePath));
    }
    domain::BuildArea CandidateArea;
    int64 CandidateTimber = 0;
    int64 CandidateTreasury = 0;
    if (!ParseSettlementFixture(FixtureJson, CandidateArea, CandidateTimber, CandidateTreasury, OutError))
    {
        return false;
    }

    OutCatalog = std::move(CandidateCatalog);
    OutBuildArea = std::move(CandidateArea);
    OutTimber = CandidateTimber;
    OutTreasury = CandidateTreasury;
    OutError.Reset();
    return true;
}

bool LoadBuildingCatalog(
    domain::BuildingCatalog& OutCatalog,
    FString& OutError)
{
    const FString CatalogPath = FPaths::ProjectContentDir() / TEXT("Domain/Data/buildings.json");
    FString CatalogJson;
    if (!FFileHelper::LoadFileToString(CatalogJson, *CatalogPath))
    {
        return Reject(OutError, TEXT("building content"), FString::Printf(TEXT("could not read %s"), *CatalogPath));
    }
    return ParseBuildingCatalog(CatalogJson, OutCatalog, OutError);
}
