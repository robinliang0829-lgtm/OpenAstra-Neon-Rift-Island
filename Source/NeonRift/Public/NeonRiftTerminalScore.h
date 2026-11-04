#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NeonRiftTerminalScore.generated.h"

/** Terminal channel wire. Completing a score is the sim's job, not this actor. */
UCLASS()
class NEONRIFT_API ANeonRiftTerminalScore : public AActor
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitActorDowned(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitActorRespawned(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitHitIgnored(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitHitRejected(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitMatchClockExpired(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitMatchSettled(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitOvertimeStarted(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitPointScored(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitScoreChannelInterrupted(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitScoreChannelRejected(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitScoreChannelStarted(const FString& PayloadJson);
};
