#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "NeonRiftResidentPort.generated.h"

/**
 * Thin policy for one digital resident. Not a production resident.
 * SelectMatch accepts a legal faction for the body. Decide records an intent
 * from flags and ids. There is no coordinate argument, and nothing here scores.
 * NR-M1-bot does not construct this. GameMode, GameState, and PlayerState do not either.
 */
UCLASS()
class NEONRIFT_API UNeonRiftResidentPort : public UObject
{
	GENERATED_BODY()

public:
	UNeonRiftResidentPort();

	/** Join when Body may take OfferedFaction and OfferedRole is a real role. */
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	bool SelectMatch(const FString& CombatantId, const FString& Body, const FString& OfferedFaction, const FString& OfferedRole);

	/**
	 * Same contest, pass, interrupt, and score intents as the local bot.
	 * Caller passes ids and flags only. Do not pass post-wall coordinates.
	 */
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void Decide(
		const FString& CombatantId,
		const FString& Role,
		bool bDowned,
		bool bLive,
		bool bHoldingCore,
		bool bCorePickable,
		bool bAtCore,
		bool bPassOpen,
		bool bTeammateInRange,
		bool bAtTerminal,
		bool bChannelActive,
		bool bInterruptOpen,
		bool bReaderHere,
		bool bAtHolderTerminal,
		const FString& ScoreTerminal,
		const FString& PassTargetId,
		const FString& ReaderId,
		const FString& HolderId,
		const FString& HolderScoreTerminal);

	UPROPERTY(BlueprintReadOnly, Category="NeonRift")
	bool bJoined;

	UPROPERTY(BlueprintReadOnly, Category="NeonRift")
	FString SelectedFaction;

	UPROPERTY(BlueprintReadOnly, Category="NeonRift")
	FString SelectedRole;

	UPROPERTY(BlueprintReadOnly, Category="NeonRift")
	FString LastAction;

	UPROPERTY(BlueprintReadOnly, Category="NeonRift")
	FString LastReason;

	UPROPERTY(BlueprintReadOnly, Category="NeonRift")
	FString LastTargetId;

private:
	void EmitSelect(const FString& CombatantId) const;
	void EmitIntent(const FString& CombatantId) const;
};
