#include "NeonRiftPlayerState.h"
#include "NeonRiftEventLog.h"
#include "NeonRiftGameState.h"
#include "Engine/World.h"
#include "Net/UnrealNetwork.h"

ANeonRiftPlayerState::ANeonRiftPlayerState()
	: bBound(false)
{
	PrimaryActorTick.bCanEverTick = false;
}

void ANeonRiftPlayerState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ANeonRiftPlayerState, ViewpointClientId);
	DOREPLIFETIME(ANeonRiftPlayerState, BodyType);
	DOREPLIFETIME(ANeonRiftPlayerState, MatchFaction);
	DOREPLIFETIME(ANeonRiftPlayerState, ControllerKind);
	DOREPLIFETIME(ANeonRiftPlayerState, ViewpointEventLog);
}

void ANeonRiftPlayerState::BeginPlay()
{
	Super::BeginPlay();
	BindToMatchRelay();
}

void ANeonRiftPlayerState::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (bBound)
	{
		if (UWorld* World = GetWorld())
		{
			if (ANeonRiftGameState* State = World->GetGameState<ANeonRiftGameState>())
			{
				State->OnGameStateEvent.RemoveDynamic(this, &ANeonRiftPlayerState::HandleRelay);
			}
		}
		bBound = false;
	}
	Super::EndPlay(EndPlayReason);
}

void ANeonRiftPlayerState::SetViewpointClientId(const FString& InClientId)
{
	if (!HasAuthority())
	{
		return;
	}
	ViewpointClientId = InClientId;
}

void ANeonRiftPlayerState::SetIdentityLabels(
	const FString& InBodyType,
	const FString& InMatchFaction,
	const FString& InControllerKind)
{
	if (!HasAuthority())
	{
		return;
	}
	// Labels copied from CombatantJoined / FactionChosen. Not a second roster.
	BodyType = InBodyType;
	MatchFaction = InMatchFaction;
	ControllerKind = InControllerKind;
}

void ANeonRiftPlayerState::BindToMatchRelay()
{
	if (bBound)
	{
		return;
	}
	UWorld* World = GetWorld();
	if (World == nullptr)
	{
		return;
	}
	ANeonRiftGameState* State = World->GetGameState<ANeonRiftGameState>();
	if (State == nullptr)
	{
		return;
	}
	State->OnGameStateEvent.AddDynamic(this, &ANeonRiftPlayerState::HandleRelay);
	bBound = true;
}

void ANeonRiftPlayerState::HandleRelay(FName EventName, FString PayloadJson)
{
	if (!HasAuthority())
	{
		return;
	}
	ViewpointEventLog.Add(NeonRiftFormatEventLine(EventName.ToString(), PayloadJson));
	OnViewpointEvent.Broadcast(EventName, PayloadJson);
}

void ANeonRiftPlayerState::OnRep_ViewpointEventLog()
{
	if (ViewpointEventLog.Num() == 0)
	{
		return;
	}
	FString EventName;
	FString PayloadJson;
	if (!NeonRiftSplitEventLine(ViewpointEventLog.Last(), EventName, PayloadJson))
	{
		return;
	}
	OnViewpointEvent.Broadcast(FName(*EventName), PayloadJson);
}
