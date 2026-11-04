#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "NeonRiftResidentPort.generated.h"

/**
 * Adapter port for a future digital resident.
 * NR-M1-bot does not construct this, and local_bot does not call it.
 * The methods are empty: no faction, no pass, no score.
 */
UCLASS()
class NEONRIFT_API UNeonRiftResidentPort : public UObject
{
	GENERATED_BODY()

public:
	/** Empty. A resident would choose whether to join here. */
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void SelectMatch();

	/** Empty. A resident would return an intent here. */
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void Decide();
};
