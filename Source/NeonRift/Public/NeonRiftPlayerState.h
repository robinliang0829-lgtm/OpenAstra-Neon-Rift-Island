#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerState.h"
#include "Net/UnrealNetwork.h"
#include "NeonRiftMatchSubsystem.h"
#include "NeonRiftPlayerState.generated.h"

/**
 * One client viewpoint. Subscribes to the game-state relay and rebroadcasts
 * the same lines. ViewpointClientId is a label for the log header, not a faction.
 */
UCLASS()
class NEONRIFT_API ANeonRiftPlayerState : public APlayerState
{
	GENERATED_BODY()

public:
	ANeonRiftPlayerState();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UPROPERTY(BlueprintAssignable, Category="NeonRift")
	FNeonRiftMatchEvent OnViewpointEvent;

	UPROPERTY(Replicated, BlueprintReadOnly, Category="NeonRift")
	FString ViewpointClientId;

	UPROPERTY(ReplicatedUsing=OnRep_ViewpointEventLog, BlueprintReadOnly, Category="NeonRift")
	TArray<FString> ViewpointEventLog;

	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void SetViewpointClientId(const FString& InClientId);

	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void BindToMatchRelay();

	UFUNCTION()
	void HandleRelay(FName EventName, FString PayloadJson);

	UFUNCTION()
	void OnRep_ViewpointEventLog();

private:
	bool bBound;
};
