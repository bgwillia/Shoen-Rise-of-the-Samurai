#include "FoundationHUD.h"
#include "FoundationGameMode.h"
#include "FoundationPlayerController.h"
#include "ShoenSimulationSubsystem.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "FoundationCursorDiagnostics.h"

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
void AFoundationHUD::DrawHUD()
{
    Super::DrawHUD();
    auto* Sim = GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    auto* Mode = Cast<AFoundationGameMode>(GetWorld()->GetAuthGameMode());
    auto* PC = Cast<AFoundationPlayerController>(PlayerOwner);
    if (!Sim || !Mode || !Canvas) return;
    const auto P = domain::Summarize(Sim->State);
    const FLinearColor Muted(.62,.72,.73), Gold(.95,.74,.37);
    DrawRect(FLinearColor(.025,.04,.045,.95),0,0,Canvas->SizeX,64);
    Label(TEXT("SHOEN  /  FOUNDATION LAB"),20,15,Gold,1.4f);
    Label(FString::Printf(TEXT("Year %lld  |  Day %lld / 360  |  %dx"),1180+Sim->State.campaign_day/360,1+Sim->State.campaign_day%360,Sim->State.speed),440,17,FLinearColor::White,1.2f);
    Label(TEXT("Simulation calendar  |  1 day / 3 sec at 1x"),440,40,Muted);
    DrawRect(FLinearColor(.035,.055,.06,.94),0,64,410,Canvas->SizeY-64);
    Label(TEXT("CAMPAIGN CLOCK"),20,82,Gold);
    Button(TEXT("pause"),TEXT("Pause"),20,105,64);
    Button(TEXT("speed1"),TEXT("1x"),92,105,64);
    Button(TEXT("speed3"),TEXT("3x"),164,105,64);
    Button(TEXT("speed5"),TEXT("5x"),236,105,64);
    Button(TEXT("speed10"),TEXT("10x"),308,105,78);
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
    if (PC)
    {
        Label(FString::Printf(TEXT("Selected: %d formations"),PC->Selected.Num()),440,78,Gold,1.1f);
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
    Label(TEXT("Original primitive placeholders. Scale support requires measured evidence."),430,Canvas->SizeY-23,Muted);
}
void AFoundationHUD::NotifyHitBoxClick(FName Id)
{
    Super::NotifyHitBoxClick(Id);
    auto* Sim = GetGameInstance()->GetSubsystem<UShoenSimulationSubsystem>();
    auto* Mode = Cast<AFoundationGameMode>(GetWorld()->GetAuthGameMode());
    if (!Sim || !Mode) return;
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
