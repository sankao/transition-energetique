"""Tests for consumption module — SDES 2023 reference and electrification."""
import pytest
from src.consumption import (
    UsageReference, SectorReference, ReferenceData, sdes_2023,
    ElectrificationParams, SectorBalance, SystemBalance,
    convert_residential, convert_tertiary, convert_industry,
    convert_transport, convert_agriculture, convert_non_energy,
    calculate_system_balance,
)


class TestUsageReference:
    def test_vectors_sum_to_total(self):
        u = UsageReference(
            name="chauffage", total_twh=312,
            elec_twh=50, gaz_twh=94, petrole_twh=31,
            charbon_twh=0, enr_twh=125, reseau_twh=12,
        )
        assert u.total_twh == 312

    def test_vectors_mismatch_raises(self):
        with pytest.raises(ValueError):
            UsageReference(
                name="bad", total_twh=100,
                elec_twh=10, gaz_twh=10, petrole_twh=10,
                charbon_twh=0, enr_twh=10, reseau_twh=10,
            )  # sum=50, total=100 -> error


class TestSectorReference:
    def test_usages_sum_to_sector_total(self):
        usages = [
            UsageReference("a", 200, 200, 0, 0, 0, 0, 0),
            UsageReference("b", 100, 50, 50, 0, 0, 0, 0),
        ]
        s = SectorReference(name="test", usages=usages)
        assert s.total_twh == 300

    def test_sector_total_property(self):
        usages = [
            UsageReference("x", 50, 50, 0, 0, 0, 0, 0),
        ]
        s = SectorReference(name="test", usages=usages)
        assert s.total_twh == 50


class TestReferenceData:
    def test_grand_total_is_1615(self):
        ref = sdes_2023()
        assert ref.total_twh == pytest.approx(1615, abs=1)

    def test_residential_is_422(self):
        ref = sdes_2023()
        assert ref.residential.total_twh == pytest.approx(422, abs=1)

    def test_tertiary_is_229(self):
        ref = sdes_2023()
        assert ref.tertiary.total_twh == pytest.approx(229, abs=1)

    def test_industry_is_283(self):
        ref = sdes_2023()
        assert ref.industry.total_twh == pytest.approx(283, abs=1)

    def test_transport_is_513(self):
        ref = sdes_2023()
        assert ref.transport.total_twh == pytest.approx(513, abs=1)

    def test_agriculture_is_55(self):
        ref = sdes_2023()
        assert ref.agriculture.total_twh == pytest.approx(55, abs=1)

    def test_non_energy_is_113(self):
        ref = sdes_2023()
        assert ref.non_energy.total_twh == pytest.approx(113, abs=1)

    def test_residential_has_5_usages(self):
        ref = sdes_2023()
        assert len(ref.residential.usages) == 5
        names = [u.name for u in ref.residential.usages]
        assert "chauffage" in names
        assert "ecs" in names

    def test_transport_has_10_modes(self):
        ref = sdes_2023()
        assert len(ref.transport.usages) == 10

    def test_national_electricity_is_393(self):
        ref = sdes_2023()
        total_elec = sum(s.elec_twh for s in ref.all_sectors)
        assert total_elec == pytest.approx(393, abs=5)


class TestElectrificationParams:
    def test_default_values(self):
        p = ElectrificationParams()
        assert p.res_chauffage_cop == 3.5
        assert p.electrolyse_efficiency == 0.65
        assert p.tpt_vp_ev_factor == 0.33

    def test_custom_override(self):
        p = ElectrificationParams(res_chauffage_cop=4.0)
        assert p.res_chauffage_cop == 4.0


class TestSectorBalance:
    def test_vectors_sum(self):
        sb = SectorBalance(
            name="test", current_twh=100,
            elec_twh=40, h2_twh=10, bio_enr_twh=30, fossil_residual_twh=20,
        )
        assert sb.total_target_twh == 100
        assert sb.reduction_pct == pytest.approx(0.0)

    def test_reduction_pct(self):
        sb = SectorBalance(
            name="test", current_twh=200,
            elec_twh=50, h2_twh=10, bio_enr_twh=20, fossil_residual_twh=10,
        )
        assert sb.total_target_twh == 90
        assert sb.reduction_pct == pytest.approx(0.55, abs=0.01)


class TestSystemBalance:
    def test_from_sectors(self):
        sectors = {
            "a": SectorBalance("a", 100, 50, 10, 30, 10),
            "b": SectorBalance("b", 200, 80, 20, 60, 40),
        }
        sb = SystemBalance.from_sectors(sectors, electrolyse_efficiency=0.65)
        assert sb.current_total_twh == 300
        assert sb.direct_electricity_twh == 130
        assert sb.h2_demand_twh == 30
        assert sb.h2_production_elec_twh == pytest.approx(30 / 0.65, abs=0.5)
        assert sb.total_electricity_twh == pytest.approx(130 + 30 / 0.65, abs=0.5)
        assert sb.bio_enr_twh == 90
        assert sb.fossil_residual_twh == 50


class TestConvertResidential:
    def test_electricity_approx_175(self):
        ref = sdes_2023()
        params = ElectrificationParams()
        result = convert_residential(ref.residential, params)
        assert result.elec_twh == pytest.approx(175, abs=5)

    def test_h2_is_zero(self):
        ref = sdes_2023()
        result = convert_residential(ref.residential, ElectrificationParams())
        assert result.h2_twh == pytest.approx(0, abs=1)

    def test_bio_enr_approx_107(self):
        ref = sdes_2023()
        result = convert_residential(ref.residential, ElectrificationParams())
        assert result.bio_enr_twh == pytest.approx(107, abs=5)

    def test_fossil_is_zero(self):
        ref = sdes_2023()
        result = convert_residential(ref.residential, ElectrificationParams())
        assert result.fossil_residual_twh == pytest.approx(0, abs=1)

    def test_total_approx_282(self):
        ref = sdes_2023()
        result = convert_residential(ref.residential, ElectrificationParams())
        assert result.total_target_twh == pytest.approx(282, abs=5)

    def test_higher_cop_reduces_electricity(self):
        ref = sdes_2023()
        base = convert_residential(ref.residential, ElectrificationParams())
        high = convert_residential(ref.residential, ElectrificationParams(res_chauffage_cop=4.5))
        assert high.elec_twh < base.elec_twh


class TestConvertTertiary:
    def test_electricity_approx_120(self):
        ref = sdes_2023()
        params = ElectrificationParams()
        result = convert_tertiary(ref.tertiary, params)
        assert result.elec_twh == pytest.approx(120, abs=5)

    def test_h2_is_zero(self):
        ref = sdes_2023()
        result = convert_tertiary(ref.tertiary, ElectrificationParams())
        assert result.h2_twh == pytest.approx(0, abs=1)

    def test_bio_enr_approx_8(self):
        ref = sdes_2023()
        result = convert_tertiary(ref.tertiary, ElectrificationParams())
        assert result.bio_enr_twh == pytest.approx(8, abs=3)

    def test_fossil_approx_2(self):
        ref = sdes_2023()
        result = convert_tertiary(ref.tertiary, ElectrificationParams())
        assert result.fossil_residual_twh == pytest.approx(2, abs=2)

    def test_total_approx_140(self):
        ref = sdes_2023()
        result = convert_tertiary(ref.tertiary, ElectrificationParams())
        assert result.total_target_twh == pytest.approx(140, abs=10)

    def test_higher_cop_reduces_electricity(self):
        ref = sdes_2023()
        base = convert_tertiary(ref.tertiary, ElectrificationParams())
        high = convert_tertiary(ref.tertiary, ElectrificationParams(ter_chauffage_cop=4.5))
        assert high.elec_twh < base.elec_twh


class TestConvertIndustry:
    def test_electricity_approx_162(self):
        ref = sdes_2023()
        params = ElectrificationParams()
        result = convert_industry(ref.industry, params)
        assert result.elec_twh == pytest.approx(162, abs=10)

    def test_h2_approx_23(self):
        ref = sdes_2023()
        result = convert_industry(ref.industry, ElectrificationParams())
        assert result.h2_twh == pytest.approx(23, abs=5)

    def test_bio_enr_approx_22(self):
        ref = sdes_2023()
        result = convert_industry(ref.industry, ElectrificationParams())
        assert result.bio_enr_twh == pytest.approx(22, abs=5)

    def test_fossil_approx_15(self):
        ref = sdes_2023()
        result = convert_industry(ref.industry, ElectrificationParams())
        assert result.fossil_residual_twh == pytest.approx(15, abs=3)

    def test_total_approx_222(self):
        ref = sdes_2023()
        result = convert_industry(ref.industry, ElectrificationParams())
        assert result.total_target_twh == pytest.approx(222, abs=10)

    def test_higher_h2_fraction_increases_h2(self):
        ref = sdes_2023()
        base = convert_industry(ref.industry, ElectrificationParams())
        high = convert_industry(ref.industry, ElectrificationParams(ind_ht_h2_fraction=0.35))
        assert high.h2_twh > base.h2_twh


class TestConvertTransport:
    def test_electricity_approx_118(self):
        ref = sdes_2023()
        params = ElectrificationParams()
        result = convert_transport(ref.transport, params)
        assert result.elec_twh == pytest.approx(118, abs=10)

    def test_h2_approx_33(self):
        ref = sdes_2023()
        result = convert_transport(ref.transport, ElectrificationParams())
        assert result.h2_twh == pytest.approx(33, abs=5)

    def test_biocarb_approx_45(self):
        ref = sdes_2023()
        result = convert_transport(ref.transport, ElectrificationParams())
        assert result.bio_enr_twh == pytest.approx(45, abs=5)

    def test_fossil_approx_49(self):
        ref = sdes_2023()
        result = convert_transport(ref.transport, ElectrificationParams())
        assert result.fossil_residual_twh == pytest.approx(49, abs=5)

    def test_total_approx_245(self):
        ref = sdes_2023()
        result = convert_transport(ref.transport, ElectrificationParams())
        assert result.total_target_twh == pytest.approx(245, abs=10)

    def test_higher_ev_factor_reduces_electricity(self):
        ref = sdes_2023()
        base = convert_transport(ref.transport, ElectrificationParams())
        low = convert_transport(ref.transport, ElectrificationParams(tpt_vp_ev_factor=0.25))
        assert low.elec_twh < base.elec_twh


class TestConvertAgriculture:
    def test_electricity_approx_16(self):
        ref = sdes_2023()
        params = ElectrificationParams()
        result = convert_agriculture(ref.agriculture, params)
        assert result.elec_twh == pytest.approx(16, abs=3)

    def test_h2_approx_5(self):
        ref = sdes_2023()
        result = convert_agriculture(ref.agriculture, ElectrificationParams())
        assert result.h2_twh == pytest.approx(5, abs=2)

    def test_bio_enr_approx_11(self):
        ref = sdes_2023()
        result = convert_agriculture(ref.agriculture, ElectrificationParams())
        assert result.bio_enr_twh == pytest.approx(11, abs=3)

    def test_fossil_approx_4(self):
        ref = sdes_2023()
        result = convert_agriculture(ref.agriculture, ElectrificationParams())
        assert result.fossil_residual_twh == pytest.approx(4, abs=2)

    def test_total_approx_36(self):
        ref = sdes_2023()
        result = convert_agriculture(ref.agriculture, ElectrificationParams())
        assert result.total_target_twh == pytest.approx(36, abs=5)

    def test_higher_ev_fraction_increases_electricity(self):
        ref = sdes_2023()
        base = convert_agriculture(ref.agriculture, ElectrificationParams())
        high = convert_agriculture(ref.agriculture, ElectrificationParams(agr_machinisme_ev_fraction=0.60))
        assert high.elec_twh > base.elec_twh


class TestConvertNonEnergy:
    def test_electricity_approx_5(self):
        ref = sdes_2023()
        params = ElectrificationParams()
        result = convert_non_energy(ref.non_energy, params)
        assert result.elec_twh == pytest.approx(5, abs=2)

    def test_h2_approx_28(self):
        ref = sdes_2023()
        result = convert_non_energy(ref.non_energy, ElectrificationParams())
        assert result.h2_twh == pytest.approx(28, abs=3)

    def test_bio_approx_27(self):
        ref = sdes_2023()
        result = convert_non_energy(ref.non_energy, ElectrificationParams())
        assert result.bio_enr_twh == pytest.approx(27, abs=3)

    def test_fossil_approx_35(self):
        ref = sdes_2023()
        result = convert_non_energy(ref.non_energy, ElectrificationParams())
        assert result.fossil_residual_twh == pytest.approx(35, abs=3)

    def test_total_approx_95(self):
        ref = sdes_2023()
        result = convert_non_energy(ref.non_energy, ElectrificationParams())
        assert result.total_target_twh == pytest.approx(95, abs=5)

    def test_higher_recycling_reduces_total(self):
        ref = sdes_2023()
        base = convert_non_energy(ref.non_energy, ElectrificationParams())
        high = convert_non_energy(ref.non_energy, ElectrificationParams(ne_petrochimie_recycling_gain=0.35))
        assert high.total_target_twh < base.total_target_twh


class TestSystemBalance_Integration:
    def test_total_electricity_approx_733(self):
        balance = calculate_system_balance()
        assert balance.total_electricity_twh == pytest.approx(733, abs=15)

    def test_direct_electricity_approx_596(self):
        balance = calculate_system_balance()
        assert balance.direct_electricity_twh == pytest.approx(596, abs=10)

    def test_h2_demand_approx_89(self):
        balance = calculate_system_balance()
        assert balance.h2_demand_twh == pytest.approx(89, abs=5)

    def test_h2_production_elec_approx_137(self):
        balance = calculate_system_balance()
        assert balance.h2_production_elec_twh == pytest.approx(137, abs=15)

    def test_fossil_residual_approx_105(self):
        balance = calculate_system_balance()
        assert balance.fossil_residual_twh == pytest.approx(105, abs=10)

    def test_bio_enr_approx_220(self):
        balance = calculate_system_balance()
        assert balance.bio_enr_twh == pytest.approx(220, abs=15)

    def test_current_total_is_1615(self):
        balance = calculate_system_balance()
        assert balance.current_total_twh == pytest.approx(1615, abs=1)

    def test_all_sectors_present(self):
        balance = calculate_system_balance()
        assert len(balance.sectors) == 6
        expected = {"residential", "tertiary", "industry", "transport", "agriculture", "non_energy"}
        assert set(balance.sectors.keys()) == expected

    def test_custom_params_change_result(self):
        base = calculate_system_balance()
        custom = calculate_system_balance(
            params=ElectrificationParams(res_chauffage_cop=5.0)
        )
        assert custom.total_electricity_twh < base.total_electricity_twh


class TestTarificationIntegration:
    def test_tarif_uses_consumption_balance(self):
        from src.tarification import TarificationConfig, tarif_equilibre_eur_mwh
        balance = calculate_system_balance()
        config = TarificationConfig(
            consommation_totale_twh=balance.total_electricity_twh,
        )
        tarif = tarif_equilibre_eur_mwh(config)
        assert tarif['total_ttc_eur_mwh'] > 0

    def test_tarif_default_matches_consumption(self):
        """TarificationConfig default should match consumption.py output."""
        from src.tarification import TarificationConfig
        balance = calculate_system_balance()
        config = TarificationConfig()
        assert config.consommation_totale_twh == pytest.approx(
            balance.total_electricity_twh, abs=5
        )


class TestSensitivityIntegration:
    def test_sensitivity_accepts_demand(self):
        """System balance produces reasonable demand for sensitivity analysis."""
        balance = calculate_system_balance()
        assert balance.total_electricity_twh > 700
        assert balance.total_electricity_twh < 800
