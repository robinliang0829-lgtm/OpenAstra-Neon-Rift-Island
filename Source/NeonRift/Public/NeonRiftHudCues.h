#pragma once

#include "CoreMinimal.h"

/**
 * NR-M2 HUD cue ids. Authority is sim/steel_tide/hud.py.
 * Names only: this header does not build a widget, does not score, and does
 * not pick a holder. Faction text is badge shape plus shoulder slot.
 * Auxiliary color is not part of an id. No widget blueprint, texture, or
 * cooked asset is committed.
 */
namespace NeonRiftHud
{
	inline const TCHAR* const Scoreboard = TEXT("hud.scoreboard");
	inline const TCHAR* const TerminalReadBar = TEXT("hud.terminal.read_bar");
	inline const TCHAR* const SpawnShield = TEXT("hud.spawn_shield");
	inline const TCHAR* const RoleLock = TEXT("hud.role_lock");
	inline const TCHAR* const SideLock = TEXT("hud.side_lock");
}
