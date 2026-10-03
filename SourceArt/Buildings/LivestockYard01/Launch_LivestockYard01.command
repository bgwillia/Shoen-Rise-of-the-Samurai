#!/bin/zsh
export SHOEN_LIVESTOCK_VIEW=1
exec '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor' '/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/game/Shoen.uproject' '-ExecCmds=py /Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/SourceArt/Buildings/LivestockYard01/Scripts/import_unreal.py' -ShoenScenario=settlement -windowed -ResX=1600 -ResY=1200 -nop4 -nosplash
