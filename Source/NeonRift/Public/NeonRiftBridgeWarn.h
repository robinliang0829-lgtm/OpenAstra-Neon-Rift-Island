#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NeonRiftBridgeWarn.generated.h"

/** Bridge warning wire. The 4 second lead stays in the rules config. */
UCLASS()
class NEONRIFT_API ANeonRiftBridgeWarn : public AActor
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitBridgeOccupantNudged(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitBridgeStateChanged(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitBridgeWarningStarted(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitMoveCompleted(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitMoveRejected(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitRouteRejected(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitRouteSelected(const FString& PayloadJson);
};
