#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameStateBase.h"
#include "Net/UnrealNetwork.h"
#include "NeonRiftMatchSubsystem.h"
#include "NeonRiftGameState.generated.h"

/**
 * Replicated copy of the match bus.
 * Holder and score strings are the last authority payloads, not a local total.
 * sim/steel_tide remains the only scorer.
 */
UCLASS()
class NEONRIFT_API ANeonRiftGameState : public AGameStateBase
{
	GENERATED_BODY()

public:
	ANeonRiftGameState();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UPROPERTY(BlueprintAssignable, Category="NeonRift")
	FNeonRiftMatchEvent OnGameStateEvent;

	UPROPERTY(Replicated, BlueprintReadOnly, Category="NeonRift")
	TArray<FString> AuthoritativeEventLog;

	/** Event name of the last holder-affecting payload. Copied, not chosen here. */
	UPROPERTY(Replicated, BlueprintReadOnly, Category="NeonRift")
	FString MirroredHolderEvent;

	UPROPERTY(Replicated, BlueprintReadOnly, Category="NeonRift")
	FString MirroredHolderPayload;

	/** Raw PointScored payload. Clients display it. They do not add to it. */
	UPROPERTY(Replicated, BlueprintReadOnly, Category="NeonRift")
	FString MirroredScorePayload;

	/** Raw FactionsLocked payload. Body, faction, and controller stay in that JSON. */
	UPROPERTY(Replicated, BlueprintReadOnly, Category="NeonRift")
	FString MirroredIdentityPayload;

	UFUNCTION()
	void HandleMatchEvent(FName EventName, FString PayloadJson);

private:
	void NoteMirror(FName EventName, const FString& PayloadJson);
};
