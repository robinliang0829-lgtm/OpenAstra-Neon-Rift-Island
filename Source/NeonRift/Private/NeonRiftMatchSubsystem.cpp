#include "NeonRiftMatchSubsystem.h"
#include "NeonRift.h"
#include "NeonRiftEventLog.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

void UNeonRiftMatchSubsystem::Emit(const FString& EventName, const FString& PayloadJson)
{
	const FString Line = NeonRiftFormatEventLine(EventName, PayloadJson);
	OnMatchEvent.Broadcast(FName(*EventName), PayloadJson);
	UE_LOG(LogNeonRift, Log, TEXT("%s"), *Line);
}

void NeonRiftEmit(const UObject* WorldContext, const TCHAR* EventName, const FString& PayloadJson)
{
	if (WorldContext == nullptr || EventName == nullptr)
	{
		return;
	}
	const UWorld* World = WorldContext->GetWorld();
	if (World == nullptr || World->GetGameInstance() == nullptr)
	{
		return;
	}
	if (UNeonRiftMatchSubsystem* Match = World->GetGameInstance()->GetSubsystem<UNeonRiftMatchSubsystem>())
	{
		Match->Emit(FString(EventName), PayloadJson);
	}
}
