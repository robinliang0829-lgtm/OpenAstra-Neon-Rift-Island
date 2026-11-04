#include "NeonRiftGameState.h"
#include "NeonRiftEventLog.h"
#include "NeonRiftEventNames.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Net/UnrealNetwork.h"

namespace
{
	bool NameIs(FName EventName, const TCHAR* Expected)
	{
		return EventName == FName(Expected);
	}
}

ANeonRiftGameState::ANeonRiftGameState()
{
	PrimaryActorTick.bCanEverTick = false;
}

void ANeonRiftGameState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ANeonRiftGameState, AuthoritativeEventLog);
	DOREPLIFETIME(ANeonRiftGameState, MirroredHolderEvent);
	DOREPLIFETIME(ANeonRiftGameState, MirroredHolderPayload);
	DOREPLIFETIME(ANeonRiftGameState, MirroredScorePayload);
	DOREPLIFETIME(ANeonRiftGameState, MirroredIdentityPayload);
}

void ANeonRiftGameState::BeginPlay()
{
	Super::BeginPlay();
	if (!HasAuthority())
	{
		return;
	}
	UWorld* World = GetWorld();
	if (World == nullptr || World->GetGameInstance() == nullptr)
	{
		return;
	}
	if (UNeonRiftMatchSubsystem* Match = World->GetGameInstance()->GetSubsystem<UNeonRiftMatchSubsystem>())
	{
		Match->OnMatchEvent.AddDynamic(this, &ANeonRiftGameState::HandleMatchEvent);
	}
}

void ANeonRiftGameState::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UWorld* World = GetWorld())
	{
		if (UGameInstance* Instance = World->GetGameInstance())
		{
			if (UNeonRiftMatchSubsystem* Match = Instance->GetSubsystem<UNeonRiftMatchSubsystem>())
			{
				Match->OnMatchEvent.RemoveDynamic(this, &ANeonRiftGameState::HandleMatchEvent);
			}
		}
	}
	Super::EndPlay(EndPlayReason);
}

void ANeonRiftGameState::HandleMatchEvent(FName EventName, FString PayloadJson)
{
	if (!HasAuthority())
	{
		return;
	}
	AuthoritativeEventLog.Add(NeonRiftFormatEventLine(EventName.ToString(), PayloadJson));
	NoteMirror(EventName, PayloadJson);
	OnGameStateEvent.Broadcast(EventName, PayloadJson);
}

void ANeonRiftGameState::NoteMirror(FName EventName, const FString& PayloadJson)
{
	// Copy the authority payload. Do not grant a holder and do not add a point.
	if (NameIs(EventName, NeonRiftEvents::CorePicked)
		|| NameIs(EventName, NeonRiftEvents::CorePassed)
		|| NameIs(EventName, NeonRiftEvents::CoreDropped)
		|| NameIs(EventName, NeonRiftEvents::CoreReset)
		|| NameIs(EventName, NeonRiftEvents::CoreReturnedToCenter))
	{
		MirroredHolderEvent = EventName.ToString();
		MirroredHolderPayload = PayloadJson;
		return;
	}
	if (NameIs(EventName, NeonRiftEvents::PointScored))
	{
		MirroredScorePayload = PayloadJson;
		return;
	}
	if (NameIs(EventName, NeonRiftEvents::FactionsLocked))
	{
		MirroredIdentityPayload = PayloadJson;
		return;
	}
	static const TCHAR* const HeardOnly[] = {
		NeonRiftEvents::AbilityRejected,
		NeonRiftEvents::AbilityUsed,
		NeonRiftEvents::ActorDowned,
		NeonRiftEvents::ActorRespawned,
		NeonRiftEvents::BridgeLightStripAdvanced,
		NeonRiftEvents::BridgeOccupantNudged,
		NeonRiftEvents::BridgeStateChanged,
		NeonRiftEvents::BridgeWarningCompleted,
		NeonRiftEvents::BridgeWarningStarted,
		NeonRiftEvents::CombatantJoined,
		NeonRiftEvents::CoreDropRejected,
		NeonRiftEvents::CoreMarkRejected,
		NeonRiftEvents::CoreMarkedUnpickable,
		NeonRiftEvents::CorePassRejected,
		NeonRiftEvents::CorePickRejected,
		NeonRiftEvents::FactionChosen,
		NeonRiftEvents::FactionRejected,
		NeonRiftEvents::HitIgnored,
		NeonRiftEvents::HitRejected,
		NeonRiftEvents::MatchClockExpired,
		NeonRiftEvents::MatchSettled,
		NeonRiftEvents::MatchStarted,
		NeonRiftEvents::MoveCompleted,
		NeonRiftEvents::MoveRejected,
		NeonRiftEvents::OvertimeStarted,
		NeonRiftEvents::RoleChosen,
		NeonRiftEvents::RoleRejected,
		NeonRiftEvents::RolesLocked,
		NeonRiftEvents::RouteRejected,
		NeonRiftEvents::RouteSelected,
		NeonRiftEvents::ScoreChannelInterrupted,
		NeonRiftEvents::ScoreChannelRejected,
		NeonRiftEvents::ScoreChannelStarted,
	};
	for (const TCHAR* Name : HeardOnly)
	{
		if (NameIs(EventName, Name))
		{
			return;
		}
	}
}
