#include "NeonRiftBridgeWarn.h"
#include "NeonRiftEventNames.h"
#include "NeonRiftMatchSubsystem.h"

void ANeonRiftBridgeWarn::EmitBridgeOccupantNudged(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::BridgeOccupantNudged, PayloadJson);
}

void ANeonRiftBridgeWarn::EmitBridgeLightStripAdvanced(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::BridgeLightStripAdvanced, PayloadJson);
}

void ANeonRiftBridgeWarn::EmitBridgeStateChanged(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::BridgeStateChanged, PayloadJson);
}

void ANeonRiftBridgeWarn::EmitBridgeWarningCompleted(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::BridgeWarningCompleted, PayloadJson);
}

void ANeonRiftBridgeWarn::EmitBridgeWarningStarted(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::BridgeWarningStarted, PayloadJson);
}

void ANeonRiftBridgeWarn::EmitMoveCompleted(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::MoveCompleted, PayloadJson);
}

void ANeonRiftBridgeWarn::EmitMoveRejected(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::MoveRejected, PayloadJson);
}

void ANeonRiftBridgeWarn::EmitRouteRejected(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::RouteRejected, PayloadJson);
}

void ANeonRiftBridgeWarn::EmitRouteSelected(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::RouteSelected, PayloadJson);
}
