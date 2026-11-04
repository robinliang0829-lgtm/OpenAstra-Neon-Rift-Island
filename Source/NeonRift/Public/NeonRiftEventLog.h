#pragma once

#include "CoreMinimal.h"

/**
 * Shared line layout for NR-02 captures.
 * Stub form (no authority clock in this process): `EventName  {json}`
 * Sim form: `   t_s  EventName  {json}` — 8-wide seconds, two spaces.
 * Splitting a line does not award a point.
 */
inline FString NeonRiftFormatEventLine(const FString& EventName, const FString& PayloadJson)
{
	return FString::Printf(TEXT("%s  %s"), *EventName, *PayloadJson);
}

inline bool NeonRiftSplitEventLine(const FString& Line, FString& OutName, FString& OutPayload)
{
	FString Left;
	FString Right;
	if (!Line.Split(TEXT("  "), &Left, &Right, ESearchCase::CaseSensitive, ESearchDir::FromEnd))
	{
		return false;
	}
	Right.TrimStartAndEndInline();
	if (!Right.StartsWith(TEXT("{")))
	{
		return false;
	}
	FString NamePart = Left;
	FString Discarded;
	if (NamePart.Split(TEXT("  "), &Discarded, &NamePart, ESearchCase::CaseSensitive, ESearchDir::FromEnd))
	{
		NamePart.TrimStartAndEndInline();
	}
	else
	{
		NamePart.TrimStartAndEndInline();
	}
	if (NamePart.IsEmpty())
	{
		return false;
	}
	OutName = NamePart;
	OutPayload = Right;
	return true;
}
