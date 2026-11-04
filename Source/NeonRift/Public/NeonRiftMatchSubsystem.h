#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FNeonRiftMatchEvent, FName, EventName, FString, PayloadJson);

#include "NeonRiftMatchSubsystem.generated.h"

/**
 * Single match bus. Broadcasts canonical event names from NeonRiftEventNames.h.
 * Scoring, faction legality, and the 3-second channel live in sim/steel_tide.
 * Do not add a second scorer in a level Blueprint.
 */
UCLASS()
class NEONRIFT_API UNeonRiftMatchSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintAssignable, Category="NeonRift")
	FNeonRiftMatchEvent OnMatchEvent;

	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void Emit(const FString& EventName, const FString& PayloadJson);
};

NEONRIFT_API void NeonRiftEmit(const UObject* WorldContext, const TCHAR* EventName, const FString& PayloadJson);
