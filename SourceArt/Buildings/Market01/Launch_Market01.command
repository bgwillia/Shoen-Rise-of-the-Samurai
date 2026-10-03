#!/bin/zsh
export SHOEN_MARKET_VIEW=1
exec '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor' '/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/game/Shoen.uproject' '-ExecCmds=py /Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/SourceArt/Buildings/Market01/Scripts/import_unreal.py' -windowed -ResX=1600 -ResY=1200 -NoVSync -nop4 -nosplash
