#include "NeonRiftTerminalScore.h"
#include "NeonRiftEventNames.h"
#include "NeonRiftMatchSubsystem.h"

void ANeonRiftTerminalScore::EmitActorDowned(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::ActorDowned, PayloadJson);
}

void ANeonRiftTerminalScore::EmitActorRespawned(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::ActorRespawned, PayloadJson);
}

void ANeonRiftTerminalScore::EmitHitIgnored(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::HitIgnored, PayloadJson);
}

void ANeonRiftTerminalScore::EmitHitRejected(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::HitRejected, PayloadJson);
}

void ANeonRiftTerminalScore::EmitMatchClockExpired(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::MatchClockExpired, PayloadJson);
}

void ANeonRiftTerminalScore::EmitMatchSettled(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::MatchSettled, PayloadJson);
}

void ANeonRiftTerminalScore::EmitOvertimeStarted(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::OvertimeStarted, PayloadJson);
}

void ANeonRiftTerminalScore::EmitPointScored(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::PointScored, PayloadJson);
}

void ANeonRiftTerminalScore::EmitScoreChannelInterrupted(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::ScoreChannelInterrupted, PayloadJson);
}

void ANeonRiftTerminalScore::EmitScoreChannelRejected(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::ScoreChannelRejected, PayloadJson);
}

void ANeonRiftTerminalScore::EmitScoreChannelStarted(const FString& PayloadJson)
{
	NeonRiftEmit(this, NeonRiftEvents::ScoreChannelStarted, PayloadJson);
}
