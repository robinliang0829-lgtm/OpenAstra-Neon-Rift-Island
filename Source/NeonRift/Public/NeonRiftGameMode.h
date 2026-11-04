#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "NeonRiftMatchSubsystem.h"
#include "NeonRiftGameMode.generated.h"

/**
 * Server entry. The default map stays `/Engine/Maps/Entry` until the greybox is saved locally.
 * Points the match at ANeonRiftGameState / ANeonRiftPlayerState and relays their bus.
 * It does not keep a score.
 */
UCLASS()
class NEONRIFT_API ANeonRiftGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ANeonRiftGameMode();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void PostLogin(APlayerController* NewPlayer) override;

	UPROPERTY(BlueprintAssignable, Category="NeonRift")
	FNeonRiftMatchEvent OnModeRelay;

	UFUNCTION()
	void HandleGameStateEvent(FName EventName, FString PayloadJson);

private:
	void BindRelay();
	bool bRelayBound;
};
