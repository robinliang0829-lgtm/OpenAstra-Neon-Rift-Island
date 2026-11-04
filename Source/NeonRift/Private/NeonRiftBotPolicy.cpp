#include "NeonRiftBotPolicy.h"
#include "NeonRiftEventNames.h"
#include "NeonRiftMatchSubsystem.h"

void ANeonRiftBotPolicy::EmitBotDecision(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::BotDecision, PayloadJson);
}
