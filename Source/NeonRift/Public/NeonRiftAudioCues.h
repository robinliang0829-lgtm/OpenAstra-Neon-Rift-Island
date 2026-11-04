#pragma once

#include "CoreMinimal.h"

/**
 * NR-M2 audio cue ids. Authority is sim/steel_tide/audio.py.
 * Names only: this header does not play sound, does not score, and does not
 * pick a holder. Team ids are badge shape plus shoulder-lamp mouth.
 * Auxiliary color is not part of an id. No sound asset is committed.
 */
namespace NeonRiftAudio
{
	inline const TCHAR* const TeamA = TEXT("sfx.team.A.open_chevron.mouth.shoulder_left");
	inline const TCHAR* const TeamB = TEXT("sfx.team.B.closed_ring.mouth.shoulder_right");
	inline const TCHAR* const BridgeWarn = TEXT("sfx.bridge.warn");
	inline const TCHAR* const BridgeLightStrip = TEXT("sfx.bridge.light_strip");
	inline const TCHAR* const BridgeConnect = TEXT("sfx.bridge.connect");
	inline const TCHAR* const BridgeDisconnect = TEXT("sfx.bridge.disconnect");
	inline const TCHAR* const CorePickup = TEXT("sfx.core.pickup");
	inline const TCHAR* const CorePass = TEXT("sfx.core.pass");
	inline const TCHAR* const CoreDrop = TEXT("sfx.core.drop");
	inline const TCHAR* const CoreChannelStart = TEXT("sfx.core.channel_start");
	inline const TCHAR* const CoreInterrupt = TEXT("sfx.core.interrupt");
	inline const TCHAR* const CoreScore = TEXT("sfx.core.score");
	inline const TCHAR* const CoreReturnToCenter = TEXT("sfx.core.return_to_center");
	inline const TCHAR* const CoreReset = TEXT("sfx.core.reset");
}
