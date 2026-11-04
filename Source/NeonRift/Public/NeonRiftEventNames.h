#pragma once

#include "CoreMinimal.h"

/** Canonical Steel Tide event names. Must match sim/steel_tide/events.py. */
namespace NeonRiftEvents
{
	inline const TCHAR* const AbilityRejected = TEXT("AbilityRejected");
	inline const TCHAR* const AbilityUsed = TEXT("AbilityUsed");
	inline const TCHAR* const ActorDowned = TEXT("ActorDowned");
	inline const TCHAR* const ActorRespawned = TEXT("ActorRespawned");
	inline const TCHAR* const BridgeLightStripAdvanced = TEXT("BridgeLightStripAdvanced");
	inline const TCHAR* const BridgeOccupantNudged = TEXT("BridgeOccupantNudged");
	inline const TCHAR* const BridgeStateChanged = TEXT("BridgeStateChanged");
	inline const TCHAR* const BridgeWarningCompleted = TEXT("BridgeWarningCompleted");
	inline const TCHAR* const BridgeWarningStarted = TEXT("BridgeWarningStarted");
	inline const TCHAR* const BotDecision = TEXT("BotDecision");
	inline const TCHAR* const CombatantJoined = TEXT("CombatantJoined");
	inline const TCHAR* const CoreDropRejected = TEXT("CoreDropRejected");
	inline const TCHAR* const CoreDropped = TEXT("CoreDropped");
	inline const TCHAR* const CoreMarkRejected = TEXT("CoreMarkRejected");
	inline const TCHAR* const CoreMarkedUnpickable = TEXT("CoreMarkedUnpickable");
	inline const TCHAR* const CorePassRejected = TEXT("CorePassRejected");
	inline const TCHAR* const CorePassed = TEXT("CorePassed");
	inline const TCHAR* const CorePickRejected = TEXT("CorePickRejected");
	inline const TCHAR* const CorePicked = TEXT("CorePicked");
	inline const TCHAR* const CoreReset = TEXT("CoreReset");
	inline const TCHAR* const CoreReturnedToCenter = TEXT("CoreReturnedToCenter");
	inline const TCHAR* const FactionChosen = TEXT("FactionChosen");
	inline const TCHAR* const FactionRejected = TEXT("FactionRejected");
	inline const TCHAR* const FactionsLocked = TEXT("FactionsLocked");
	inline const TCHAR* const HitIgnored = TEXT("HitIgnored");
	inline const TCHAR* const HitRejected = TEXT("HitRejected");
	inline const TCHAR* const MatchClockExpired = TEXT("MatchClockExpired");
	inline const TCHAR* const MatchSettled = TEXT("MatchSettled");
	inline const TCHAR* const MatchStarted = TEXT("MatchStarted");
	inline const TCHAR* const MoveCompleted = TEXT("MoveCompleted");
	inline const TCHAR* const MoveRejected = TEXT("MoveRejected");
	inline const TCHAR* const OvertimeStarted = TEXT("OvertimeStarted");
	inline const TCHAR* const PointScored = TEXT("PointScored");
	inline const TCHAR* const ResidentDecision = TEXT("ResidentDecision");
	inline const TCHAR* const RoleChosen = TEXT("RoleChosen");
	inline const TCHAR* const RoleRejected = TEXT("RoleRejected");
	inline const TCHAR* const RolesLocked = TEXT("RolesLocked");
	inline const TCHAR* const RouteRejected = TEXT("RouteRejected");
	inline const TCHAR* const RouteSelected = TEXT("RouteSelected");
	inline const TCHAR* const ScoreChannelInterrupted = TEXT("ScoreChannelInterrupted");
	inline const TCHAR* const ScoreChannelRejected = TEXT("ScoreChannelRejected");
	inline const TCHAR* const ScoreChannelStarted = TEXT("ScoreChannelStarted");
}
