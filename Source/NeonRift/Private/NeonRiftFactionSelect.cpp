#include "NeonRiftFactionSelect.h"
#include "NeonRiftEventNames.h"
#include "NeonRiftMatchSubsystem.h"

void UNeonRiftFactionSelect::EmitCombatantJoined(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::CombatantJoined, PayloadJson);
}

void UNeonRiftFactionSelect::EmitFactionChosen(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::FactionChosen, PayloadJson);
}

void UNeonRiftFactionSelect::EmitFactionRejected(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::FactionRejected, PayloadJson);
}

void UNeonRiftFactionSelect::EmitFactionsLocked(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::FactionsLocked, PayloadJson);
}

void UNeonRiftFactionSelect::EmitMatchStarted(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::MatchStarted, PayloadJson);
}

void UNeonRiftFactionSelect::EmitRoleChosen(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::RoleChosen, PayloadJson);
}

void UNeonRiftFactionSelect::EmitRoleRejected(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::RoleRejected, PayloadJson);
}

void UNeonRiftFactionSelect::EmitRolesLocked(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::RolesLocked, PayloadJson);
}
