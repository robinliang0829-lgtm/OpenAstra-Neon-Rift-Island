#include "NeonRiftResidentPort.h"
#include "NeonRiftEventNames.h"
#include "NeonRiftMatchSubsystem.h"

namespace
{
	// Mirrors config/steel_tide_greybox.json faction_rule. Not a coordinate table.
	bool IsLegalSeat(const FString& Body, const FString& Faction, const FString& Role)
	{
		const bool bRole = Role == TEXT("assault") || Role == TEXT("support") || Role == TEXT("recon");
		if (!bRole)
		{
			return false;
		}
		if (Body == TEXT("human") || Body == TEXT("celestial"))
		{
			return Faction == TEXT("A");
		}
		if (Body == TEXT("robot") || Body == TEXT("beast"))
		{
			return Faction == TEXT("B");
		}
		if (Body == TEXT("humanoid_robot"))
		{
			return Faction == TEXT("A") || Faction == TEXT("B");
		}
		return false;
	}
}

UNeonRiftResidentPort::UNeonRiftResidentPort()
{
	// Thin policy, not a production resident. No coordinates. No score.
	bJoined = false;
}

bool UNeonRiftResidentPort::SelectMatch(
	const FString& CombatantId,
	const FString& Body,
	const FString& OfferedFaction,
	const FString& OfferedRole)
{
	bJoined = false;
	SelectedFaction.Empty();
	SelectedRole.Empty();
	LastAction.Empty();
	LastReason.Empty();
	LastTargetId.Empty();
	if (CombatantId.IsEmpty() || !IsLegalSeat(Body, OfferedFaction, OfferedRole))
	{
		return false;
	}
	bJoined = true;
	SelectedFaction = OfferedFaction;
	SelectedRole = OfferedRole;
	LastAction = TEXT("select_match");
	LastReason = TEXT("legal_faction");
	LastTargetId = OfferedFaction;
	EmitSelect(CombatantId);
	return true;
}

void UNeonRiftResidentPort::Decide(
	const FString& CombatantId,
	const FString& Role,
	bool bDowned,
	bool bLive,
	bool bHoldingCore,
	bool bCorePickable,
	bool bAtCore,
	bool bPassOpen,
	bool bTeammateInRange,
	bool bAtTerminal,
	bool bChannelActive,
	bool bInterruptOpen,
	bool bReaderHere,
	bool bAtHolderTerminal,
	const FString& ScoreTerminal,
	const FString& PassTargetId,
	const FString& ReaderId,
	const FString& HolderId,
	const FString& HolderScoreTerminal)
{
	LastAction.Empty();
	LastReason.Empty();
	LastTargetId.Empty();
	if (!bJoined || bDowned || !bLive || CombatantId.IsEmpty())
	{
		return;
	}
	if (bInterruptOpen && bChannelActive && bReaderHere && Role == TEXT("assault") && !ReaderId.IsEmpty())
	{
		LastAction = TEXT("interrupt_channel");
		LastReason = TEXT("contest_channel");
		LastTargetId = ReaderId;
	}
	else if (bHoldingCore)
	{
		if (bPassOpen && bTeammateInRange && !PassTargetId.IsEmpty())
		{
			LastAction = TEXT("pass_core");
			LastReason = TEXT("close_range_pass");
			LastTargetId = PassTargetId;
		}
		else if (bAtTerminal && !bChannelActive && !ScoreTerminal.IsEmpty())
		{
			LastAction = TEXT("begin_score");
			LastReason = TEXT("score_path");
			LastTargetId = ScoreTerminal;
		}
		else if (!bAtTerminal && !ScoreTerminal.IsEmpty())
		{
			LastAction = TEXT("request_move");
			LastReason = TEXT("score_path");
			LastTargetId = ScoreTerminal;
		}
	}
	else if (bCorePickable)
	{
		LastAction = bAtCore ? TEXT("pick_core") : TEXT("request_move");
		LastReason = TEXT("contest_core");
		LastTargetId = TEXT("core");
	}
	else if (bInterruptOpen && Role == TEXT("assault") && !bAtHolderTerminal && !HolderScoreTerminal.IsEmpty())
	{
		LastAction = TEXT("request_move");
		LastReason = TEXT("interrupt_channel");
		LastTargetId = HolderId.IsEmpty() ? HolderScoreTerminal : HolderId;
	}
	if (!LastAction.IsEmpty())
	{
		EmitIntent(CombatantId);
	}
}

void UNeonRiftResidentPort::EmitSelect(const FString& CombatantId) const
{
	const FString Payload = FString::Printf(
		TEXT("{\"action\":\"select_match\",\"combatant_id\":\"%s\",\"controller\":\"digital_resident\",\"join\":true,\"reason\":\"legal_faction\",\"role\":\"%s\",\"target_id\":\"%s\"}"),
		*CombatantId,
		*SelectedRole,
		*SelectedFaction);
	NeonRiftEmit(this, NeonRiftEvents::ResidentDecision, Payload);
}

void UNeonRiftResidentPort::EmitIntent(const FString& CombatantId) const
{
	const FString Payload = FString::Printf(
		TEXT("{\"action\":\"%s\",\"combatant_id\":\"%s\",\"controller\":\"digital_resident\",\"reason\":\"%s\",\"target_id\":\"%s\"}"),
		*LastAction,
		*CombatantId,
		*LastReason,
		*LastTargetId);
	NeonRiftEmit(this, NeonRiftEvents::ResidentDecision, Payload);
}
