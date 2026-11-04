#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NeonRiftBotPolicy.generated.h"

/** Forwards a BotDecision line. The choice is made in sim/steel_tide. This actor does not pick or score. */
UCLASS()
class NEONRIFT_API ANeonRiftBotPolicy : public AActor
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitBotDecision(const FString& PayloadJson);
};
