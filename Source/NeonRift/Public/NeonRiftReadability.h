#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "NeonRiftReadability.generated.h"

/** Badge outline. Color is not a value in this enum. */
UENUM(BlueprintType)
enum class ENeonRiftBadgeShape : uint8
{
	None,
	OpenChevron UMETA(DisplayName="open_chevron"),
	ClosedRing UMETA(DisplayName="closed_ring"),
};

/** Shoulder lamp slot. Left and right stay distinct with the lamp color removed. */
UENUM(BlueprintType)
enum class ENeonRiftShoulderLight : uint8
{
	None,
	ShoulderLeft UMETA(DisplayName="shoulder_left"),
	ShoulderRight UMETA(DisplayName="shoulder_right"),
};

/** Acceptance proxies from docs/art/NR03_PROXIES.json. Not a roster and not a winner. */
UENUM(BlueprintType)
enum class ENeonRiftProxyId : uint8
{
	None,
	HumanoidA UMETA(DisplayName="NR_Proxy_Humanoid_A"),
	HumanoidB UMETA(DisplayName="NR_Proxy_Humanoid_B"),
	Beast UMETA(DisplayName="NR_Proxy_Beast"),
	Quadruped UMETA(DisplayName="NR_Proxy_Quadruped"),
	EngineeringMachine UMETA(DisplayName="NR_Proxy_EngineeringMachine"),
	WetConcrete UMETA(DisplayName="NR_Proxy_WetConcrete"),
};

/**
 * One row of the readability spec.
 * Humanoid A and B share NR_Body_Humanoid. Beast and quadruped do not share a silhouette.
 */
USTRUCT(BlueprintType)
struct NEONRIFT_API FNeonRiftProxySpec
{
	GENERATED_BODY()

	UPROPERTY(EditDefaultsOnly, Category="NeonRift")
	ENeonRiftProxyId ProxyId = ENeonRiftProxyId::None;

	UPROPERTY(EditDefaultsOnly, Category="NeonRift")
	FName BodyId;

	UPROPERTY(EditDefaultsOnly, Category="NeonRift")
	FName SilhouetteId;

	UPROPERTY(EditDefaultsOnly, Category="NeonRift")
	ENeonRiftBadgeShape BadgeShape = ENeonRiftBadgeShape::None;

	UPROPERTY(EditDefaultsOnly, Category="NeonRift")
	ENeonRiftShoulderLight ShoulderLight = ENeonRiftShoulderLight::None;

	UPROPERTY(EditDefaultsOnly, Category="NeonRift")
	FName MaterialId;
};

/**
 * Data mirror of the NR-03 proxy spec and the 4 second bridge warning.
 * sim/steel_tide remains the authority. This asset does not award a winner
 * and does not choose a holder. No .uasset is committed for it.
 */
UCLASS(BlueprintType)
class NEONRIFT_API UNeonRiftReadabilityAsset : public UDataAsset
{
	GENERATED_BODY()

public:
	UNeonRiftReadabilityAsset();

	/** Mirrors config/steel_tide_greybox.json bridge_warning_seconds. */
	UPROPERTY(EditDefaultsOnly, Category="NeonRift")
	float BridgeWarningSeconds;

	/** Mirrors readable_without_reflection. Reflection is not the only cue. */
	UPROPERTY(EditDefaultsOnly, Category="NeonRift")
	bool bReadableWithoutReflection;

	UPROPERTY(EditDefaultsOnly, Category="NeonRift")
	TArray<FNeonRiftProxySpec> Proxies;
};
