#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "NeonRiftFactionSelect.generated.h"

/** Faction and role wire. Choice locks when the match starts. This component only broadcasts. */
UCLASS()
class NEONRIFT_API UNeonRiftFactionSelect : public UActorComponent
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitAbilityRejected(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitAbilityUsed(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitCombatantJoined(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitFactionChosen(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitFactionRejected(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitFactionsLocked(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitMatchStarted(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitRoleChosen(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitRoleRejected(const FString& PayloadJson);
	UFUNCTION(BlueprintCallable, Category="NeonRift")
	void EmitRolesLocked(const FString& PayloadJson);
};
