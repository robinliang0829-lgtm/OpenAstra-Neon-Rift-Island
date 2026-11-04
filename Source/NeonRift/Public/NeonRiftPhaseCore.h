#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NeonRiftPhaseCore.generated.h"

/** Phase core wire. One actor in the level. Does not grant a second holder. */
UCLASS()
class NEONRIFT_API ANeonRiftPhaseCore : public AActor
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitCoreDropRejected(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitCoreDropped(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitCoreMarkRejected(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitCoreMarkedUnpickable(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitCorePassRejected(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitCorePassed(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitCorePickRejected(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitCorePicked(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitCoreReset(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitCoreReturnedToCenter(const FString& PayloadJson);
};
