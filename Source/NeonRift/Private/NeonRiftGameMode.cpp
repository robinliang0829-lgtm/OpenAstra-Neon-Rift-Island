#include "NeonRiftGameMode.h"
#include "NeonRiftGameState.h"
#include "NeonRiftPlayerState.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"

ANeonRiftGameMode::ANeonRiftGameMode()
	: bRelayBound(false)
{
	GameStateClass = ANeonRiftGameState::StaticClass();
	PlayerStateClass = ANeonRiftPlayerState::StaticClass();
	PrimaryActorTick.bCanEverTick = false;
}

void ANeonRiftGameMode::BeginPlay()
{
	Super::BeginPlay();
	BindRelay();
}

void ANeonRiftGameMode::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (bRelayBound)
	{
		if (ANeonRiftGameState* State = GetGameState<ANeonRiftGameState>())
		{
			State->OnGameStateEvent.RemoveDynamic(this, &ANeonRiftGameMode::HandleGameStateEvent);
		}
		bRelayBound = false;
	}
	Super::EndPlay(EndPlayReason);
}

void ANeonRiftGameMode::PostLogin(APlayerController* NewPlayer)
{
	Super::PostLogin(NewPlayer);
	BindRelay();
	if (NewPlayer == nullptr)
	{
		return;
	}
	if (ANeonRiftPlayerState* Viewpoint = NewPlayer->GetPlayerState<ANeonRiftPlayerState>())
	{
		Viewpoint->BindToMatchRelay();
	}
}

void ANeonRiftGameMode::BindRelay()
{
	if (bRelayBound)
	{
		return;
	}
	ANeonRiftGameState* State = GetGameState<ANeonRiftGameState>();
	if (State == nullptr)
	{
		return;
	}
	State->OnGameStateEvent.AddDynamic(this, &ANeonRiftGameMode::HandleGameStateEvent);
	bRelayBound = true;
}

void ANeonRiftGameMode::HandleGameStateEvent(FName EventName, FString PayloadJson)
{
	// The name is the sim event. This relay does not decide a winner.
	OnModeRelay.Broadcast(EventName, PayloadJson);
}
