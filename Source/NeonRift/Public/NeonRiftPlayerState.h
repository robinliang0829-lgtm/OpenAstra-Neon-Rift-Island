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

	/** Body type copied from the sim. Not a faction and not a controller. */
	UPROPERTY(Replicated, BlueprintReadOnly, Category="NeonRift")
	FString BodyType;

	/** Match faction copied from the sim. Empty until FactionChosen. */
	UPROPERTY(Replicated, BlueprintReadOnly, Category="NeonRift")
	FString MatchFaction;

	/** human, digital_resident, or local_bot. Copied from the sim. */
	UPROPERTY(Replicated, BlueprintReadOnly, Category="NeonRift")
	FString ControllerKind;

	UPROPERTY(ReplicatedUsing=OnRep_ViewpointEventLog, BlueprintReadOnly, Category="NeonRift")
	TArray<FString> ViewpointEventLog;

	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void SetViewpointClientId(const FString& InClientId);

	/** Copy the three identity labels. Does not choose a side and does not score. */
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void SetIdentityLabels(const FString& InBodyType, const FString& InMatchFaction, const FString& InControllerKind);

	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void BindToMatchRelay();

	UFUNCTION()
	void HandleRelay(FName EventName, FString PayloadJson);

	UFUNCTION()
	void OnRep_ViewpointEventLog();

private:
	bool bBound;
};
