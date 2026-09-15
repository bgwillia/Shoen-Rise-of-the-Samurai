#include "FoundationHUD.h"
#include "FoundationGameMode.h"
#include "FoundationPlayerController.h"
#include "ShoenSimulationSubsystem.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "FoundationCursorDiagnostics.h"
#include "domain/Buildings.h"
#include "domain/Inspection.h"
#include "domain/Prototype.h"
#include "domain/Terrain.h"
#include "InteractionProfiler.h"
#include "InputCoreTypes.h"

void AFoundationHUD::Label(const FString& Text,float X,float Y,FLinearColor Color,float Scale)
{
    DrawText(Text,Color,X,Y,GEngine->GetSmallFont(),Scale,false);
}
void AFoundationHUD::Button(FName Id,const FString& Text,float X,float Y,float Width)
{
    DrawRect(FLinearColor(.13,.18,.20,.96),X,Y,Width,28);
    Label(Text,X+9,Y+5,FLinearColor(.9,.87,.74));
    AddHitBox(FVector2D(X,Y),FVector2D(Width,28),Id,true);
}
void AFoundationHUD::BuildingInspector(const domain::Building& Instance,const domain::BuildingDefinition* Definition)
{
    const FLinearColor Muted(.62,.72,.73), Cyan(.2,.95,1), Gold(.95,.74,.37);
    Label(TEXT("BUILDING INSPECTOR"),20,341,Cyan);
    Label(TEXT("INSTANCE  /  placed building"),20,362,Gold);
    Label(FString::Printf(TEXT("Building ID: %llu"),uint64(Instance.id)),20,381);
    const FString District=Instance.district_id ? FString::Printf(TEXT("%llu"),uint64(Instance.district_id)) : TEXT("Unassigned");
    Label(FString::Printf(TEXT("Settlement: %llu  |  District: %s"),uint64(Instance.settlement_id),*District),20,400);
    Label(FString::Printf(TEXT("Position (cm): %d, %d, %d"),Instance.x_cm,Instance.y_cm,Instance.z_cm),20,419);
    const TCHAR* State=Instance.state==domain::ConstructionState::Completed ? TEXT("Completed") : TEXT("Unknown");
    Label(FString::Printf(TEXT("Yaw: %d deg  |  State: %s"),Instance.yaw_degrees,State),20,438);
    Label(FString::Printf(TEXT("Placed footprint: %.1f x %.1f m"),Instance.width_cm/100.0,Instance.depth_cm/100.0),20,457,Muted);
    Label(TEXT("DEFINITION  /  configured type"),20,483,Gold);
    Label(Definition ? UTF8_TO_TCHAR(Definition->display_name.c_str()) : TEXT("Definition unavailable"),20,502);
    Label(FString::Printf(TEXT("Type: %s"),UTF8_TO_TCHAR(Instance.definition_id.c_str())),20,521);
    if (Definition)
    {
        Label(FString::Printf(TEXT("Footprint: %.1f x %.1f m  |  Version: %u"),Definition->width_cm/100.0,Definition->depth_cm/100.0,Definition->version),20,540,Muted);
        Label(FString::Printf(TEXT("Cost: %lld timber + %lld treasury"),Definition->timber_cost,Definition->treasury_cost),20,559);
    }
    else Label(TEXT("Configured footprint and cost unavailable"),20,540,Muted);
    Label(TEXT("Cyan: selected | Click empty ground to clear"),20,580,Muted);
}
void AFoundationHUD::DrawHUD()
{
    Super::DrawHUD();
    auto* Sim = GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    auto* Mode = Cast<AFoundationGameMode>(GetWorld()->GetAuthGameMode());
    auto* PC = Cast<AFoundationPlayerController>(PlayerOwner);
    if (!Sim || !Mode || !Canvas) return;
    if (Sim->Prototype.enabled) { DrawPrototypeHUD(Sim,Mode,PC); return; }
    const auto P = domain::Summarize(Sim->State);
    const FLinearColor Muted(.62,.72,.73), Gold(.95,.74,.37);
    DrawRect(FLinearColor(.025,.04,.045,.95),0,0,Canvas->SizeX,64);
    Label(Sim->IsSettlement() ? TEXT("SHOEN  /  SETTLEMENT") : TEXT("SHOEN  /  FOUNDATION LAB"),20,15,Gold,1.4f);
    Button(TEXT("settlement"),TEXT("N  New settlement fixture"),Canvas->SizeX-246,17,226);
    Label(FString::Printf(TEXT("Year %lld  |  Day %lld / 360  |  %dx"),1180+Sim->State.campaign_day/360,1+Sim->State.campaign_day%360,Sim->State.speed),440,17,FLinearColor::White,1.2f);
    Label(TEXT("Simulation calendar  |  1 day / 3 sec at 1x"),440,40,Muted);
    DrawRect(FLinearColor(.035,.055,.06,.94),0,64,410,Canvas->SizeY-64);
    Label(TEXT("CAMPAIGN CLOCK"),20,82,Gold);
    Button(TEXT("pause"),TEXT("Pause"),20,105,64);
    Button(TEXT("speed1"),TEXT("1x"),92,105,64);
    Button(TEXT("speed3"),TEXT("3x"),164,105,64);
    Button(TEXT("speed5"),TEXT("5x"),236,105,64);
    Button(TEXT("speed10"),TEXT("10x"),308,105,78);
    if (Sim->IsSettlement())
    {
        // These borrowed records are resolved afresh for this draw, never cached
        // in the Actor or retained across a save/load/world replacement.
        const auto* Inspected=PC ? domain::ResolveBuilding(Sim->State,PC->InspectionSelection()) : nullptr;
        const auto& Resources=Sim->State.settlements.begin()->second.resources;
        Label(TEXT("SETTLEMENT RESOURCES"),20,154,Gold);
        Label(FString::Printf(TEXT("Timber     %lld"),Resources.timber),20,182,FLinearColor::White,1.2f);
        Label(FString::Printf(TEXT("Treasury   %lld"),Resources.treasury),20,210,FLinearColor::White,1.2f);
        Label(FString::Printf(TEXT("Workers %lld   |   Buildings %llu"),P.available,uint64(Sim->State.buildings.size())),20,242,Muted);
        Label(TEXT("CHOOSE BUILDING"),20,278,Gold);
        if (!Sim->BuildingDefinitions().empty())
        {
            const auto& Definition=Sim->BuildingDefinitions().begin()->second;
            Button(TEXT("build"),TEXT("B  ")+FString(UTF8_TO_TCHAR(Definition.display_name.c_str())),20,301,366);
            if (!Inspected)
            {
                Label(FString::Printf(TEXT("Cost: %lld timber + %lld treasury"),Definition.timber_cost,Definition.treasury_cost),20,341);
                Label(FString::Printf(TEXT("Footprint %.1f x %.1f m | Flat ground"),Definition.width_cm/100.0,Definition.depth_cm/100.0),20,362,Muted);
            }
        }
        const bool Placing=PC && PC->IsPlacing();
        if (Inspected) BuildingInspector(*Inspected,domain::ResolveBuildingDefinition(Sim->BuildingDefinitions(),*Inspected));
        else
        {
            Label(Placing ? TEXT("PLACEMENT ACTIVE") : TEXT("Click a placed building to inspect"),20,397,Gold);
            if (Placing)
            {
                const bool Valid=PC->HasPlacementPoint() && PC->PlacementStatus().ok;
                Label(PC->HasPlacementPoint() ? UTF8_TO_TCHAR(domain::PlacementReason(PC->PlacementStatus().code)) : TEXT("Move the pointer onto the ground"),20,424,Valid ? FLinearColor(.3,1,.45) : FLinearColor(1,.4,.3));
                Label(FString::Printf(TEXT("Position %d, %d cm   |   Facing %d deg"),PC->Placement().x_cm,PC->Placement().y_cm,PC->Placement().yaw_degrees),20,447,Muted);
                Button(TEXT("rotateleft"),TEXT("[  Rotate left"),20,474);
                Button(TEXT("rotateright"),TEXT("]  Rotate right"),211,474);
                Button(TEXT("confirm"),TEXT("Enter  Confirm"),20,509);
                Button(TEXT("cancel"),TEXT("Esc  Cancel"),211,509);
            }
            if (!Sim->State.buildings.empty())
            {
                const auto& Last=Sim->State.buildings.rbegin()->second;
                Label(FString::Printf(TEXT("Last building ID %llu | Completed"),uint64(Last.id)),20,554,Gold);
            }
            Label(TEXT("Gold outline: build area | Raised strip: slope"),20,580,Muted);
        }
        Button(TEXT("save"),TEXT("F5  Save settlement"),20,606);
        Button(TEXT("load"),TEXT("F9  Load settlement"),211,606);
        Label(TEXT("WASD pan | Wheel zoom | Q/E camera rotate"),20,640,Muted);
        Label(TEXT("Middle-drag rotate | Shift-middle pan"),20,656,Muted);
        Label(Placing ? TEXT("Click / Enter build | Right click / Esc cancel") : TEXT("Click building: inspect | Esc: clear selection"),20,672,Muted);
        Label(TEXT("N new fixture | R foundation | F12 diagnostics"),20,688,Muted);
        Label(TEXT("Placeholder only. No storage or production."),20,705,Muted);
    }
    else
    {
    Label(TEXT("POPULATION / ONE SHARED LEDGER"),20,150,Gold);
    Label(FString::Printf(TEXT("Available workers       %lld"),P.available),20,178);
    Label(FString::Printf(TEXT("Away in service         %lld"),P.away),20,201);
    Label(FString::Printf(TEXT("Wounded at home         %lld"),P.recovering),20,224);
    Label(FString::Printf(TEXT("Dead (audit ledger)     %lld"),P.dead),20,247);
    Label(FString::Printf(TEXT("Living %lld   |   Accounted %lld"),P.living,P.total),20,274,Gold);
    if (!Sim->State.settlements.empty())
    {
        const auto& R = Sim->State.settlements.begin()->second.resources;
        Label(FString::Printf(TEXT("Food %lld   Treasury %lld"),R.food,R.treasury),20,301,Muted);
        Label(FString::Printf(TEXT("Timber %lld  Iron %lld  Fuel %lld  Gear %lld"),R.timber,R.iron,R.fuel,R.equipment),20,320,Muted);
    }
    Label(TEXT("SCRIPTED ACCOUNTING PROOF"),20,352,Gold);
    Button(TEXT("accounting"),TEXT("Reset: 200 workers"),20,376);
    Button(TEXT("mobilize"),TEXT("M  Mobilize 100"),211,376);
    Button(TEXT("outcome"),TEXT("O  Apply 20/15/65"),20,411);
    Button(TEXT("demobilize"),TEXT("Return survivors"),211,411);
    Label(TEXT("No battle simulation in this milestone."),20,449,Muted);
    Label(TEXT("NEW SCALE FIXTURE / 100 PER FORMATION"),20,479,Gold);
    Button(TEXT("scale1000"),TEXT("1,000 soldiers"),20,504);
    Button(TEXT("scale4000"),TEXT("4,000 soldiers"),211,504);
    Button(TEXT("scale8000"),TEXT("8,000 soldiers"),20,539);
    Button(TEXT("scale20000"),TEXT("20,000 stress only"),211,539);
    Label(FString::Printf(TEXT("Rendered: %d soldiers / %d formations"),Mode->LiveInstances(),Mode->LiveFormations()),20,579,Gold);
    Button(TEXT("save"),TEXT("F5  Save snapshot"),20,606);
    Button(TEXT("load"),TEXT("F9  Load snapshot"),211,606);
    Label(TEXT("WASD pan | Wheel zoom | Q/E rotate"),20,636,Muted);
    Label(TEXT("Middle-drag rotate | Shift-middle pan"),20,650,Muted);
    Label(TEXT("Click/box select | Shift adds | Right move"),20,664,Muted);
    Label(TEXT("Right-drag facing | Ctrl+1..9 assign group"),20,678,Muted);
    Label(TEXT("1..9 recall | Ctrl+A all | Space pause"),20,692,Muted);
    Label(TEXT("Z/X/C/V presets | R reset | F12 input debug"),20,706,Muted);
    }
    if (PC)
    {
        if (!Sim->IsSettlement()) Label(FString::Printf(TEXT("Selected: %d formations"),PC->Selected.Num()),440,78,Gold,1.1f);
        if (PC->bMouseDiagnostics)
        {
            const auto Diagnostic = ReadFoundationCursorDiagnostics(*PC);
            const float MX = Diagnostic.Viewport.X, MY = Diagnostic.Viewport.Y;
            DrawRect(FLinearColor(0,0,0,.85),420,155,Canvas->SizeX-430,80);
            for (int32 I=0; I<Diagnostic.Lines.Num(); ++I) Label(Diagnostic.Lines[I],430,160+I*18,FLinearColor::White);
            DrawLine(MX-8,MY,MX+8,MY,FLinearColor::Red,2);
            DrawLine(MX,MY-8,MX,MY+8,FLinearColor::Red,2);
            if (Diagnostic.bHasNative)
            {
                const FVector2D NativePoint = Diagnostic.NativeViewport;
                DrawLine(NativePoint.X-12,NativePoint.Y-12,NativePoint.X+12,NativePoint.Y+12,FLinearColor(0,1,1),1);
                DrawLine(NativePoint.X-12,NativePoint.Y+12,NativePoint.X+12,NativePoint.Y-12,FLinearColor(0,1,1),1);
            }
        }
        if (PC->Selected.Num()==1)
        {
            const auto Id = *PC->Selected.CreateConstIterator();
            const auto It = Sim->State.formations.find(Id);
            if (It!=Sim->State.formations.end() && !It->second.service_ids.empty())
            {
                const auto& S = Sim->State.services.at(It->second.service_ids.front());
                Label(FString::Printf(TEXT("Formation %llu | %lld attached | Group %d"),Id,domain::ActiveFormationCount(Sim->State,Id),It->second.control_group),440,102);
                Label(FString::Printf(TEXT("Origin district %llu | %s | cohort %llu"),S.origin.district_id,UTF8_TO_TCHAR(domain::OccupationName(S.origin.occupation)),S.origin.cohort_id),440,125);
            }
        }
        if (PC->bSelecting)
        {
            const FVector2D A=PC->SelectionStart, B=PC->SelectionEnd;
            DrawLine(A.X,A.Y,B.X,A.Y,Gold,1);
            DrawLine(B.X,A.Y,B.X,B.Y,Gold,1);
            DrawLine(B.X,B.Y,A.X,B.Y,Gold,1);
            DrawLine(A.X,B.Y,A.X,A.Y,Gold,1);
        }
    }
    DrawRect(FLinearColor(.025,.04,.045,.95),410,Canvas->SizeY-54,Canvas->SizeX-410,54);
    Label(Sim->Message,430,Canvas->SizeY-42,Gold);
    Label(Sim->IsSettlement() ? TEXT("Buildings are saved simulation records. N resets this test fixture.") : TEXT("Original primitive placeholders. Scale support requires measured evidence."),430,Canvas->SizeY-23,Muted);
    ShoenProfile::CaptureHud(Sim->Message);
}
void AFoundationHUD::NotifyHitBoxClick(FName Id)
{
    const FName Kind=Id==TEXT("build") ? TEXT("enter") : Id==TEXT("rotateleft") || Id==TEXT("rotateright") ? TEXT("rotate") : Id==TEXT("confirm") ? TEXT("confirm") : Id==TEXT("cancel") ? TEXT("cancel") : TEXT("hud_other");
    ShoenProfile::FActionScope Profile(Kind,EKeys::LeftMouseButton);
    ShoenProfile::Mark(TEXT("ui_hit_processed"));
    Super::NotifyHitBoxClick(Id);
    auto* Sim = GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    auto* Mode = Cast<AFoundationGameMode>(GetWorld()->GetAuthGameMode());
    if (!Sim || !Mode) return;
    auto* PC=Cast<AFoundationPlayerController>(PlayerOwner);
    if (Id==TEXT("proto_reset")) { Mode->NewPrototype(); return; }
    if (Sim->Prototype.enabled)
    {
        const int32 Ordinary=int32(Sim->Prototype.config.ordinary_formation_size),Elite=int32(Sim->Prototype.config.elite_formation_size);
        const int32 Smiths=Sim->Prototype.terrain_enabled ? Ordinary : 20;
        if (Id==TEXT("terrain_muster")) Sim->MusterTerrainArmy();
        if (Id==TEXT("terrain_bridge")) Sim->OrderTerrainCrossing(false);
        if (Id==TEXT("terrain_ford")) Sim->OrderTerrainCrossing(true);
        if (Id==TEXT("terrain_line")) Sim->DeployTerrainLine();
        if (Id==TEXT("proto_farmer")) Sim->RecruitPrototypeTroops(domain::Occupation::Agriculture,domain::TroopRole::Polearm,Ordinary);
        if (Id==TEXT("proto_labor")) Sim->RecruitPrototypeTroops(domain::Occupation::GeneralLabor,domain::TroopRole::Polearm,Ordinary);
        if (Id==TEXT("proto_smith")) Sim->RecruitPrototypeTroops(domain::Occupation::Smithing,domain::TroopRole::Polearm,Smiths);
        if (Id==TEXT("proto_bow")) Sim->RecruitPrototypeTroops(domain::Occupation::Agriculture,domain::TroopRole::Bow,Ordinary);
        if (Id==TEXT("proto_samurai")) Sim->RecruitPrototypeTroops(domain::Occupation::RetainerService,domain::TroopRole::SamuraiFoot,Elite);
        if (Id==TEXT("proto_fight")) { if (Sim->StartPrototypeBattle()) Mode->FrameCurrentScenario(); }
        if (Id==TEXT("proto_attack")) Sim->OrderPrototypeAttack();
        if (Id==TEXT("proto_return")) { if (Sim->ReturnPrototypeArmy()) Mode->FrameCurrentScenario(); }
        if (Id==TEXT("proto_days")) Sim->FastForwardPrototype(7);
        const FString Name=Id.ToString();
        if (PC && Name.StartsWith(TEXT("proto_build_"))) PC->BeginPlacementType(Name.RightChop(12));
    }
    if (Id==TEXT("settlement")) Mode->NewSettlement();
    if (PC)
    {
        if (Id==TEXT("build")) PC->BeginPlacement();
        if (Id==TEXT("rotateleft")) PC->RotatePlacement(-1);
        if (Id==TEXT("rotateright")) PC->RotatePlacement(1);
        if (Id==TEXT("confirm")) PC->ConfirmPlacement();
        if (Id==TEXT("cancel")) PC->CancelPlacement();
    }
    if (Id==TEXT("pause")) Sim->SetGameSpeed(0);
    if (Id==TEXT("speed1")) Sim->SetGameSpeed(1);
    if (Id==TEXT("speed3")) Sim->SetGameSpeed(3);
    if (Id==TEXT("speed5")) Sim->SetGameSpeed(5);
    if (Id==TEXT("speed10")) Sim->SetGameSpeed(10);
    if (Id==TEXT("accounting")) Mode->NewScenario(0);
    if (Id==TEXT("mobilize")) Sim->MobilizeProof();
    if (Id==TEXT("outcome")) Sim->ResolveProof();
    if (Id==TEXT("demobilize")) Sim->DemobilizeProof();
    if (Id==TEXT("scale1000")) Mode->NewScenario(1000);
    if (Id==TEXT("scale4000")) Mode->NewScenario(4000);
    if (Id==TEXT("scale8000")) Mode->NewScenario(8000);
    if (Id==TEXT("scale20000")) Mode->NewScenario(20000);
    if (Id==TEXT("save")) Sim->Save();
    if (Id==TEXT("load")) Sim->Load();
}

void AFoundationHUD::DrawPrototypeHUD(UShoenSimulationSubsystem* Sim,AFoundationGameMode* Mode,AFoundationPlayerController* PC)
{
    const auto& W=Sim->State; const auto& Proto=Sim->Prototype;
    const auto Pop=domain::Summarize(W); const auto Economy=domain::ForecastPrototype(W,Proto);
    const bool Battle=Sim->IsPrototypeBattle(),Terrain=Proto.terrain_enabled;
    const int32 Ordinary=int32(Proto.config.ordinary_formation_size),Elite=int32(Proto.config.elite_formation_size),Smiths=Terrain ? Ordinary : 20;
    const FLinearColor Muted(.62,.72,.73),Gold(.95,.74,.37),Cyan(.3,.85,1);
    DrawRect(FLinearColor(.025,.04,.045,.96),0,0,Canvas->SizeX,64);
    DrawRect(FLinearColor(.035,.055,.06,.96),0,64,410,Canvas->SizeY-64);
    Label(Terrain ? TEXT("SHOEN / TERRAIN PROTOTYPE B") : TEXT("SHOEN / CORE LOOP PROTOTYPE"),20,16,Gold,1.2f);
    Label(FString::Printf(TEXT("Day %lld | %dx | %s"),W.campaign_day+1,W.speed,UTF8_TO_TCHAR(domain::BattlePhaseName(Proto.phase))),440,17,FLinearColor::White,1.2f);
    Label(Battle ? TEXT("Blue: your army | Red: enemy | Purple: elite") : TEXT("Settlement -> mobilize -> battle -> return -> recover"),440,41,Muted);
    Button(TEXT("proto_reset"),TEXT("Reset entire prototype"),Canvas->SizeX-220,17,200);
    Label(TEXT("CAMPAIGN / BATTLE CLOCK"),20,76,Gold);
    Button(TEXT("pause"),TEXT("Pause"),20,98,64); Button(TEXT("speed1"),TEXT("1x"),92,98,64);
    Button(TEXT("speed3"),TEXT("3x"),164,98,64); Button(TEXT("speed5"),TEXT("5x"),236,98,64); Button(TEXT("speed10"),TEXT("10x"),308,98,78);
    Label(FString::Printf(TEXT("Living %lld | Away %lld | Dead %lld"),Pop.living,Pop.away,Pop.dead),20,136,Gold);
    Label(FString::Printf(TEXT("Available %lld | Recovering %lld | Dependents %lld"),Pop.available,Pop.recovering,Pop.dependent),20,156,Muted);
    Label(TEXT("OCCUPATION             READY / AWAY / RECOVER"),20,180,Cyan);
    domain::Quantity Available[6]{},Away[6]{},Recovering[6]{};
    for (const auto& Pair:W.cohorts)
    {
        const auto I=static_cast<int32>(Pair.second.occupation);
        if (I>=0 && I<6) { Available[I]+=Pair.second.available; Recovering[I]+=Pair.second.recovering_home; }
    }
    for (const auto& Pair:W.services)
    {
        const auto& S=Pair.second; const auto I=static_cast<int32>(S.origin.occupation);
        if (I>=0 && I<6 && S.status!=domain::ServiceStatus::Dead && S.status!=domain::ServiceStatus::ReturnedHealthy && S.status!=domain::ServiceStatus::ReturnedWounded) ++Away[I];
    }
    domain::Quantity EliteOriginal=Available[5]+Recovering[5],EliteDead=0;
    for (const auto& Pair:W.services)
        if (Pair.second.origin.occupation==domain::Occupation::RetainerService)
        {
            if (Pair.second.status==domain::ServiceStatus::Dead) ++EliteDead;
        }
    // Returned survivors are already in their cohort; count away/dead records once.
    EliteOriginal+=Away[5]+EliteDead;
    const TCHAR* Occupations[]={TEXT("Farmers"),TEXT("Laborers"),TEXT("Smiths"),TEXT("Commerce"),TEXT("Maritime"),TEXT("Retainers")};
    for (int32 I=0;I<6;++I)
    {
        Label(Occupations[I],20,201+I*17);
        Label(FString::Printf(TEXT("%lld / %lld / %lld"),Available[I],Away[I],Recovering[I]),218,201+I*17);
    }
    if (!W.settlements.empty())
    {
        const auto& R=W.settlements.begin()->second.resources;
        Label(FString::Printf(TEXT("Food %lld / %lld | Timber %lld"),R.food,Economy.food_capacity,R.timber),20,309,Gold);
        Label(FString::Printf(TEXT("Iron %lld | Fuel %lld | Treasury %lld"),R.iron,R.fuel,R.treasury),20,329);
        Label(FString::Printf(TEXT("Basic gear %lld | Elite gear %lld"),R.equipment,Proto.elite_equipment),20,349,Cyan);
    }
    Label(FString::Printf(TEXT("Daily food %+lld (%lld grown - %lld eaten)"),Economy.food_produced-Economy.food_consumed,Economy.food_produced,Economy.food_consumed),20,374,Economy.food_produced>=Economy.food_consumed ? FLinearColor(.4,1,.5) : FLinearColor(1,.45,.3));
    Label(FString::Printf(TEXT("Smith output/day: %lld basic, %lld elite"),Economy.basic_equipment_produced,Economy.elite_equipment_produced),20,394,Muted);
    domain::Quantity Roles[5]{};
    for (const auto& Pair:W.formations)
    {
        if (Pair.second.demobilized) continue;
        const auto I=static_cast<int32>(Pair.second.role);
        const auto* Unit=domain::LookupCombatUnit(Proto,domain::CombatSide::Player,Pair.first);
        if (I>=0 && I<5) Roles[I]+=Battle && Unit ? Unit->alive : domain::ActiveFormationCount(W,Pair.first);
    }
    Label(FString::Printf(TEXT("Army: %lld spear | %lld bow | %lld elite"),Roles[0],Roles[1],Roles[2]+Roles[3]+Roles[4]),20,417,Gold);
    Button(TEXT("proto_farmer"),FString::Printf(TEXT("M  %d farmer spears"),Ordinary),20,442); Button(TEXT("proto_labor"),FString::Printf(TEXT("L  %d labor spears"),Ordinary),211,442);
    Button(TEXT("proto_smith"),FString::Printf(TEXT("J  %d smith spears"),Smiths),20,474); Button(TEXT("proto_bow"),FString::Printf(TEXT("K  %d farmer bows"),Ordinary),211,474);
    Button(TEXT("proto_samurai"),FString::Printf(TEXT("T  %d samurai"),Elite),20,506); Button(TEXT("proto_days"),TEXT("P  Advance 7 days"),211,506);
    Button(TEXT("proto_fight"),TEXT("F  Take army to battle"),20,542); Button(TEXT("proto_attack"),TEXT("G  Advance / attack"),211,542);
    Button(TEXT("proto_return"),Battle && Proto.phase==domain::BattlePhase::Fighting ? TEXT("H  Retreat to settlement") : TEXT("H  Return survivors"),20,574,366);
    Label(TEXT("WASD pan | Wheel zoom | Q/E rotate"),20,611,Muted);
    Label(TEXT("Middle-drag rotate | Shift-middle pan"),20,628,Muted);
    Label(TEXT("Click/box select | Shift adds | Right move"),20,645,Muted);
    Label(Terrain ? TEXT("[ / ] face line | Ctrl+1..9 set group") : TEXT("Right-drag facing | Ctrl+1..9 set group"),20,662,Muted);
    Label(Terrain ? TEXT("Tab all | , infantry | . bows | / elite") : TEXT("1..9 recall | Ctrl+A all | Space pause"),20,679,Muted);
    Label(Terrain ? TEXT("1..9 recall | Space pause | F12 optional") : TEXT("F6 profile / F12 diagnostics: optional"),20,696,Muted);
    if (Battle)
    {
        const auto& R=Proto.battle;
        DrawRect(FLinearColor(.035,.055,.06,.94),420,70,Canvas->SizeX-440,146);
        AddHitBox(FVector2D(420,70),FVector2D(Canvas->SizeX-440,146),TEXT("battle_status"),true,1);
        Label(FString::Printf(TEXT("YOUR ARMY: %lld standing | %lld dead | %lld wounded"),R.player_alive,R.player_dead,R.player_wounded),440,82,Cyan,1.1f);
        Label(FString::Printf(TEXT("ENEMY: %lld standing | %lld dead | %lld wounded"),R.enemy_alive,R.enemy_dead,R.enemy_wounded),440,105,FLinearColor(1,.45,.4));
        int32 Routed=0; double Fatigue=0; int32 Units=0;
        for (const auto& Pair:Proto.player_units) { Routed+=Pair.second.routed ? 1 : 0; Fatigue+=Pair.second.fatigue; ++Units; }
        Label(FString::Printf(TEXT("%.0fs battle | Routing %d formations | Average fatigue %.0f | Selected %d"),R.seconds,Routed,Units ? Fatigue/Units : 0,PC ? PC->Selected.Num() : 0),440,128,Gold);
        DrawBattleSelection(Sim,PC,(Terrain ? 266.f : 230.f)+(Proto.phase!=domain::BattlePhase::Fighting ? 24.f : 0.f));
        if (Terrain)
        {
            Button(TEXT("terrain_bridge"),TEXT("Y  Primary bridge"),440,224,240);
            Button(TEXT("terrain_ford"),TEXT("O  Flanking ford"),690,224,240);
            Button(TEXT("terrain_line"),TEXT("I  Deploy selected line"),940,224,240);
        }
        if (Proto.phase!=domain::BattlePhase::Fighting) Label(Proto.phase==domain::BattlePhase::Victory ? TEXT("VICTORY - H returns survivors") : TEXT("DEFEAT - H returns remaining survivors"),440,Terrain ? 262 : 220,Gold,1.05f);
    }
    else
    {
        const auto& R=Proto.last_outcome;
        if (R.player_started>0)
        {
            DrawRect(FLinearColor(.035,.055,.06,.94),420,70,Canvas->SizeX-440,48);
            Label(FString::Printf(TEXT("LAST BATTLE: %s | Dead %lld | Wounded %lld | Healthy %lld"),R.retreated ? TEXT("retreated") : R.victory ? TEXT("victory") : TEXT("defeat"),R.player_dead,R.player_wounded,R.player_alive),440,79,Gold);
            Label(TEXT("Dead workers stay lost. Wounded recover after 7 days; watch food and gear output."),440,100,Muted);
        }
        int32 I=0;
        for (const auto& Pair:Proto.catalog)
        {
            if (I==6) break;
            const FString Type=UTF8_TO_TCHAR(Pair.first.c_str());
            Button(FName(*(TEXT("proto_build_")+Type)),UTF8_TO_TCHAR(Pair.second.display_name.c_str()),440+(I%3)*250,128+(I/3)*32,240); ++I;
        }
        if (Terrain && (!PC || !PC->IsPlacing()))
        {
            DrawRect(FLinearColor(.035,.055,.06,.96),420,190,Canvas->SizeX-440,95);
            AddHitBox(FVector2D(420,190),FVector2D(Canvas->SizeX-440,95),TEXT("terrain_muster_status"),true,-1);
            Button(TEXT("terrain_muster"),TEXT("U  Muster remaining population"),440,198,300);
            Label(FString::Printf(TEXT("Elite ready %lld / %lld original | Last war: %lld dead, %lld wounded"),Available[5],EliteOriginal,Proto.last_outcome.player_elite_dead,Proto.last_outcome.player_elite_wounded),440,236,Gold);
            Label(TEXT("Muster uses remaining people and equipment; it never resets the settlement."),440,257,Muted);
        }
        if (PC && PC->IsPlacing())
        {
            Label(FString::Printf(TEXT("PLACE: %s | %s"),UTF8_TO_TCHAR(PC->Placement().definition_id.c_str()),PC->HasPlacementPoint() ? UTF8_TO_TCHAR(domain::PlacementReason(PC->PlacementStatus().code)) : TEXT("move pointer onto ground")),440,199,Gold);
            Label(TEXT("Click / Enter confirm | [ / ] rotate | Right click / Esc cancel"),440,220,Muted);
        }
        if (PC) for (const auto& Pair:W.buildings)
        {
            const auto& B=Pair.second; FVector2D Screen;
            if (Terrain && PC->InspectionSelection().id!=B.id) continue;
            if (PC->ProjectWorldLocationToScreen(FVector(B.x_cm,B.y_cm,B.z_cm+B.height_cm+120),Screen,false) && Screen.X>420 && Screen.Y>(Terrain ? 290 : 240) && Screen.Y<Canvas->SizeY-64)
            {
                const auto Definition=Proto.catalog.find(B.definition_id);
                const FString Name=Definition!=Proto.catalog.end() ? UTF8_TO_TCHAR(Definition->second.display_name.c_str()) : UTF8_TO_TCHAR(B.definition_id.c_str());
                FString Function;
                if (B.definition_id=="house") Function=TEXT("Housing");
                else if (B.definition_id=="farm") Function=TEXT("Food production");
                else if (B.definition_id=="granary") Function=TEXT("Food storage");
                else if (B.definition_id=="smithy") Function=TEXT("Military equipment");
                else if (B.definition_id=="manor") Function=TEXT("Estate / retainers");
                else Function=TEXT("Retainer training");
                Label(Name+TEXT(" / ")+Function,Screen.X-75,Screen.Y,Gold);
            }
        }
    }
    if (PC && PC->bSelecting)
    {
        const FVector2D A=PC->SelectionStart,B=PC->SelectionEnd;
        DrawLine(A.X,A.Y,B.X,A.Y,Gold); DrawLine(B.X,A.Y,B.X,B.Y,Gold);
        DrawLine(B.X,B.Y,A.X,B.Y,Gold); DrawLine(A.X,B.Y,A.X,A.Y,Gold);
    }
    DrawRect(FLinearColor(.025,.04,.045,.95),410,Canvas->SizeY-54,Canvas->SizeX-410,54);
    Label(Sim->Message,430,Canvas->SizeY-42,Gold);
    Label(Battle ? TEXT("Selected labels only: M morale / F fatigue / G group. Orange ring: routing.") : TEXT("Mobilizing workers lowers production. Return survivors and advance days to see the consequence."),430,Canvas->SizeY-23,Muted);
    if (PC && PC->bMouseDiagnostics)
    {
        const auto Diagnostic=ReadFoundationCursorDiagnostics(*PC);
        DrawRect(FLinearColor(0,0,0,.85),420,245,Canvas->SizeX-430,80);
        for (int32 I=0;I<Diagnostic.Lines.Num();++I) Label(Diagnostic.Lines[I],430,250+I*18);
        DrawLine(Diagnostic.Viewport.X-8,Diagnostic.Viewport.Y,Diagnostic.Viewport.X+8,Diagnostic.Viewport.Y,FLinearColor::Red,2);
        DrawLine(Diagnostic.Viewport.X,Diagnostic.Viewport.Y-8,Diagnostic.Viewport.X,Diagnostic.Viewport.Y+8,FLinearColor::Red,2);
        if (Diagnostic.bHasNative)
        {
            const auto P=Diagnostic.NativeViewport;
            DrawLine(P.X-12,P.Y-12,P.X+12,P.Y+12,FLinearColor(0,1,1),1);
            DrawLine(P.X-12,P.Y+12,P.X+12,P.Y-12,FLinearColor(0,1,1),1);
        }
    }
    ShoenProfile::CaptureHud(Sim->Message);
}

void AFoundationHUD::DrawBattleSelection(UShoenSimulationSubsystem* Sim,AFoundationPlayerController* PC,float WorldLabelTop)
{
    const FLinearColor Gold(.95,.74,.37),Muted(.62,.72,.73);
    TArray<const domain::Formation*> Formations;
    domain::Quantity Strength=0,Starting=0;
    int32 RoleCount[5]{},Routed=0;
    double Morale=0,Fatigue=0;
    TArray<uint8> Groups;
    if (PC) for (const uint64 Id:PC->Selected)
    {
        const auto Found=Sim->State.formations.find(Id);
        if (Found==Sim->State.formations.end() || Found->second.demobilized) continue;
        const auto* Unit=domain::LookupCombatUnit(Sim->Prototype,domain::CombatSide::Player,Id);
        if (!Unit) continue;
        Formations.Add(&Found->second); Strength+=Unit->alive; Starting+=Unit->starting;
        Morale+=Unit->morale*Unit->alive; Fatigue+=Unit->fatigue*Unit->alive;
        Routed+=Unit->routed ? 1 : 0;
        const int32 Role=int32(Found->second.role); if (Role>=0 && Role<5) ++RoleCount[Role];
        Groups.AddUnique(Found->second.control_group);
    }
    Groups.Sort(); FString GroupText;
    for (const uint8 Group:Groups)
    {
        if (!GroupText.IsEmpty()) GroupText+=TEXT(",");
        GroupText+=Group ? FString::FromInt(Group) : TEXT("none");
    }
    if (GroupText.IsEmpty()) GroupText=TEXT("none");
    const auto RoleName=[](domain::TroopRole Role)->const TCHAR*
    {
        switch (Role)
        {
        case domain::TroopRole::Bow: return TEXT("BOW");
        case domain::TroopRole::RetainerInfantry: return TEXT("RETAINER");
        case domain::TroopRole::SamuraiFoot: return TEXT("SAMURAI");
        case domain::TroopRole::MountedSamurai: return TEXT("CAVALRY");
        default: return TEXT("POLEARM");
        }
    };
    Label(FString::Printf(TEXT("SELECTED %d formations | Strength %lld / %lld | Groups: %s"),Formations.Num(),Strength,Starting,*GroupText),440,151,Gold);
    if (Formations.Num()==1)
    {
        const auto& F=*Formations[0]; const auto* Unit=domain::LookupCombatUnit(Sim->Prototype,domain::CombatSide::Player,F.id);
        Label(FString::Printf(TEXT("%s #%llu | Morale %.0f | Fatigue %.0f | %s"),RoleName(F.role),uint64(F.id),Unit->morale,Unit->fatigue,Unit->routed ? TEXT("ROUTING") : Unit->engaged ? TEXT("ENGAGED") : TEXT("READY")),440,173);
        Label(FString::Printf(TEXT("Dead %lld | Wounded %lld | Group %s | Right-drag facing"),Unit->dead,Unit->wounded,*GroupText),440,195,Muted);
    }
    else
    {
        Label(FString::Printf(TEXT("Polearm %d | Bows %d | Elite %d | Routing %d"),RoleCount[0],RoleCount[1],RoleCount[2]+RoleCount[3]+RoleCount[4],Routed),440,173);
        Label(FString::Printf(TEXT("Weighted morale %.0f | Fatigue %.0f | Click one for detailed status"),Strength ? Morale/Strength : 0,Strength ? Fatigue/Strength : 0),440,195,Muted);
    }
    // Labels belong to HUD coordinates so they cannot spill over the sidebar,
    // command strip or footer. At army scale the aggregate header carries detail.
    TArray<FBox2D> Occupied;
    for (const auto* F:Formations)
    {
        if (Occupied.Num()==12) break;
        const auto* Unit=domain::LookupCombatUnit(Sim->Prototype,domain::CombatSide::Player,F->id);
        if (!Unit || Unit->alive==0) continue;
        FVector2D Screen;
        const double Z=Sim->Prototype.terrain_enabled ? domain::TerrainHeight(F->x,F->y) : 0;
        if (!PC->ProjectWorldLocationToScreen(FVector(F->x,F->y,Z+340),Screen,false)) continue;
        const FString Text=FString::Printf(TEXT("%s %lld | M%.0f F%.0f G%d%s"),RoleName(F->role),Unit->alive,Unit->morale,Unit->fatigue,F->control_group,Unit->routed ? TEXT(" ROUT") : TEXT(""));
        float Width=0,Height=0; GetTextSize(Text,Width,Height,GEngine->GetSmallFont(),1.f);
        const FVector2D Min(Screen.X-Width*.5-5,Screen.Y-3),Max(Min.X+Width+10,Min.Y+Height+6);
        if (Min.X<420 || Max.X>Canvas->SizeX-10 || Min.Y<WorldLabelTop || Max.Y>Canvas->SizeY-64) continue;
        bool Overlaps=false;
        for (const auto& Bounds:Occupied)
            if (Min.X<Bounds.Max.X && Max.X>Bounds.Min.X && Min.Y<Bounds.Max.Y && Max.Y>Bounds.Min.Y) { Overlaps=true; break; }
        if (Overlaps) continue;
        Occupied.Add(FBox2D(Min,Max));
        DrawRect(FLinearColor(.02,.025,.03,.9),Min.X,Min.Y,Width+10,Height+6);
        Label(Text,Min.X+5,Min.Y+3,Unit->routed ? FLinearColor(1,.5,.1) : Gold);
    }
    if (PC && Sim->Prototype.terrain_enabled)
    {
        const auto& Geometry=domain::PrototypeTerrain();
        const TCHAR* Names[]={TEXT("BRIDGE"),TEXT("LONG FORD"),TEXT("WOODS"),TEXT("HILL")};
        const domain::TerrainRect Rects[]={Geometry.bridge,Geometry.ford,Geometry.forest,Geometry.hill};
        for (int32 I=0;I<4;++I)
        {
            const double X=(Rects[I].min_x+Rects[I].max_x)*.5,Y=(Rects[I].min_y+Rects[I].max_y)*.5;
            FVector2D Screen;
            if (!PC->ProjectWorldLocationToScreen(FVector(X,Y,domain::TerrainHeight(X,Y)+60),Screen,false)) continue;
            float Width=0,Height=0; GetTextSize(Names[I],Width,Height,GEngine->GetSmallFont(),1.f);
            const FVector2D Min(Screen.X-Width*.5-5,Screen.Y-3),Max(Min.X+Width+10,Min.Y+Height+6);
            if (Min.X<420 || Max.X>Canvas->SizeX-10 || Min.Y<WorldLabelTop || Max.Y>Canvas->SizeY-64) continue;
            bool Overlaps=false;
            for (const auto& Bounds:Occupied)
                if (Min.X<Bounds.Max.X && Max.X>Bounds.Min.X && Min.Y<Bounds.Max.Y && Max.Y>Bounds.Min.Y) { Overlaps=true; break; }
            if (Overlaps) continue;
            Occupied.Add(FBox2D(Min,Max));
            DrawRect(FLinearColor(.02,.025,.03,.8),Min.X,Min.Y,Width+10,Height+6);
            Label(Names[I],Min.X+5,Min.Y+3,FLinearColor(.65,.82,.7));
        }
    }

}
