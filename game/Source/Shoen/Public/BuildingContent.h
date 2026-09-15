#pragma once

#include "CoreMinimal.h"
#include "domain/BuildingTypes.h"

SHOEN_API bool ParseBuildingCatalog(
    const FString& Json,
    domain::BuildingCatalog& OutCatalog,
    FString& OutError);

SHOEN_API bool LoadBuildingCatalog(
    domain::BuildingCatalog& OutCatalog,
    FString& OutError);

SHOEN_API bool LoadSettlementContent(
    domain::BuildingCatalog& OutCatalog,
    domain::BuildArea& OutBuildArea,
    int64& OutTimber,
    int64& OutTreasury,
    FString& OutError);
