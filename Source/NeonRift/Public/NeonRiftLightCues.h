#pragma once

#include "CoreMinimal.h"

/**
 * NR-M2 light cue ids. Authority is sim/steel_tide/light.py.
 * Names only: this header does not light a level, does not score, and does
 * not pick a holder. Shoulder ids are badge shape plus lamp slot.
 * Auxiliary color is not part of an id. Day-port and night-port intensities
 * stay in config/steel_tide_greybox.json. No texture asset is committed.
 */
namespace NeonRiftLight
{
	inline const TCHAR* const ShoulderA = TEXT("light.shoulder.A.open_chevron.shoulder_left");
	inline const TCHAR* const ShoulderB = TEXT("light.shoulder.B.closed_ring.shoulder_right");
	inline const TCHAR* const BridgeRamp = TEXT("light.bridge.ramp");
	inline const TCHAR* const BridgeConnect = TEXT("light.bridge.connect");
	inline const TCHAR* const BridgeDisconnect = TEXT("light.bridge.disconnect");
	inline const TCHAR* const TerminalReadBar = TEXT("light.terminal.read_bar");
	inline const TCHAR* const Score = TEXT("light.score");
	inline const TCHAR* const SpawnProtection = TEXT("light.spawn_protection");
}
