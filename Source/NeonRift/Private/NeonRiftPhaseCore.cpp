#include "NeonRiftPhaseCore.h"
#include "NeonRiftEventNames.h"
#include "NeonRiftMatchSubsystem.h"

void ANeonRiftPhaseCore::EmitCoreDropRejected(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::CoreDropRejected, PayloadJson);
}

void ANeonRiftPhaseCore::EmitCoreDropped(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::CoreDropped, PayloadJson);
}

void ANeonRiftPhaseCore::EmitCoreMarkRejected(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::CoreMarkRejected, PayloadJson);
}

void ANeonRiftPhaseCore::EmitCoreMarkedUnpickable(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::CoreMarkedUnpickable, PayloadJson);
}

void ANeonRiftPhaseCore::EmitCorePassRejected(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::CorePassRejected, PayloadJson);
}

void ANeonRiftPhaseCore::EmitCorePassed(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::CorePassed, PayloadJson);
}

void ANeonRiftPhaseCore::EmitCorePickRejected(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::CorePickRejected, PayloadJson);
}

void ANeonRiftPhaseCore::EmitCorePicked(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::CorePicked, PayloadJson);
}

void ANeonRiftPhaseCore::EmitCoreReset(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::CoreReset, PayloadJson);
}

void ANeonRiftPhaseCore::EmitCoreReturnedToCenter(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::CoreReturnedToCenter, PayloadJson);
}
