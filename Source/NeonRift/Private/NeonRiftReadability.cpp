#include "NeonRiftReadability.h"

namespace
{
	FNeonRiftProxySpec MakeProxy(
		ENeonRiftProxyId Id,
		const TCHAR* BodyId,
		const TCHAR* SilhouetteId,
		ENeonRiftBadgeShape Badge,
		ENeonRiftShoulderLight Light,
		const TCHAR* MaterialId)
	{
		FNeonRiftProxySpec Spec;
		Spec.ProxyId = Id;
		Spec.BodyId = BodyId;
		Spec.SilhouetteId = SilhouetteId;
		Spec.BadgeShape = Badge;
		Spec.ShoulderLight = Light;
		Spec.MaterialId = MaterialId;
		return Spec;
	}
}

UNeonRiftReadabilityAsset::UNeonRiftReadabilityAsset()
{
	BridgeWarningSeconds = 4.f;
	bReadableWithoutReflection = true;

	Proxies.Add(MakeProxy(
		ENeonRiftProxyId::HumanoidA,
		TEXT("NR_Body_Humanoid"),
		TEXT("humanoid_shared"),
		ENeonRiftBadgeShape::OpenChevron,
		ENeonRiftShoulderLight::ShoulderLeft,
		TEXT("")));
	Proxies.Add(MakeProxy(
		ENeonRiftProxyId::HumanoidB,
		TEXT("NR_Body_Humanoid"),
		TEXT("humanoid_shared"),
		ENeonRiftBadgeShape::ClosedRing,
		ENeonRiftShoulderLight::ShoulderRight,
		TEXT("")));
	Proxies.Add(MakeProxy(
		ENeonRiftProxyId::Beast,
		TEXT("NR_Body_Beast"),
		TEXT("organic_beast"),
		ENeonRiftBadgeShape::None,
		ENeonRiftShoulderLight::None,
		TEXT("")));
	Proxies.Add(MakeProxy(
		ENeonRiftProxyId::Quadruped,
		TEXT("NR_Body_Quadruped"),
		TEXT("hydraulic_quadruped"),
		ENeonRiftBadgeShape::None,
		ENeonRiftShoulderLight::None,
		TEXT("")));
	Proxies.Add(MakeProxy(
		ENeonRiftProxyId::EngineeringMachine,
		TEXT(""),
		TEXT("engineering_machine"),
		ENeonRiftBadgeShape::None,
		ENeonRiftShoulderLight::None,
		TEXT("mat.worn_yellow")));
	Proxies.Add(MakeProxy(
		ENeonRiftProxyId::WetConcrete,
		TEXT(""),
		TEXT("wet_concrete"),
		ENeonRiftBadgeShape::None,
		ENeonRiftShoulderLight::None,
		TEXT("mat.wet_concrete")));
}
