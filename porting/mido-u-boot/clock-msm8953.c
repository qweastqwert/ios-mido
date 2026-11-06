// SPDX-License-Identifier: GPL-2.0+
/* Minimal MSM8953 GCC support for HakiOS's U-Boot phone path. */

#include <clk-uclass.h>
#include <dm.h>
#include <linux/bitops.h>
#include <dt-bindings/clock/qcom,gcc-msm8953.h>

#include "clock-qcom.h"

/* The USB and SDCC source clocks used by msm8953.dtsi. */
static ulong msm8953_set_rate(struct clk *clk, ulong rate)
{
	struct msm_clk_priv *priv = dev_get_priv(clk->dev);

	switch (clk->id) {
	case USB30_MASTER_CLK_SRC:
		if (rate <= 80000000) {
			clk_rcg_set_rate(priv->base, 0x3f00c, 5,
					 CFG_CLK_SRC_GPLL0_EVEN);
			return 80000000;
		}
		if (rate <= 100000000) {
			clk_rcg_set_rate(priv->base, 0x3f00c, 8,
					 CFG_CLK_SRC_GPLL0);
			return 100000000;
		}
		clk_rcg_set_rate(priv->base, 0x3f00c, 6,
				 CFG_CLK_SRC_GPLL0);
		return 133330000;
	case USB30_MOCK_UTMI_CLK_SRC:
		clk_rcg_set_rate(priv->base, 0x3f020, 1, CFG_CLK_SRC_CXO);
		return 19200000;
	case USB3_AUX_CLK_SRC:
		clk_rcg_set_rate(priv->base, 0x3f05c, 1, CFG_CLK_SRC_CXO);
		return 19200000;
	case SDCC1_APPS_CLK_SRC:
		if (rate <= 25000000) {
			clk_rcg_set_rate(priv->base, 0x42004, 16,
					 CFG_CLK_SRC_GPLL0_AUX2);
			return 25000000;
		}
		if (rate <= 50000000) {
			clk_rcg_set_rate(priv->base, 0x42004, 16,
					 CFG_CLK_SRC_GPLL0);
			return 50000000;
		}
		if (rate <= 100000000) {
			clk_rcg_set_rate(priv->base, 0x42004, 8,
					 CFG_CLK_SRC_GPLL0);
			return 100000000;
		}
		clk_rcg_set_rate(priv->base, 0x42004, 6,
				 CFG_CLK_SRC_GPLL4);
		return 192000000;
	default:
		return rate;
	}
}

static const struct gate_clk msm8953_clks[] = {
	GATE_CLK(GCC_PCNOC_USB3_AXI_CLK, 0x3f038, BIT(0)),
	GATE_CLK(GCC_QUSB_REF_CLK, 0x41030, BIT(0)),
	GATE_CLK(GCC_SDCC1_AHB_CLK, 0x4201c, BIT(0)),
	GATE_CLK(GCC_SDCC1_APPS_CLK, 0x42018, BIT(0)),
	GATE_CLK(GCC_USB30_MASTER_CLK, 0x3f000, BIT(0)),
	GATE_CLK(GCC_USB30_MOCK_UTMI_CLK, 0x3f008, BIT(0)),
	GATE_CLK(GCC_USB30_SLEEP_CLK, 0x3f004, BIT(0)),
	GATE_CLK(GCC_USB3_AUX_CLK, 0x3f044, BIT(0)),
	GATE_CLK(GCC_USB3_PIPE_CLK, 0x3f040, BIT(0)),
	GATE_CLK(GCC_USB_PHY_CFG_AHB_CLK, 0x3f080, BIT(0)),
	GATE_CLK(GCC_USB_SS_REF_CLK, 0x3f07c, BIT(0)),
};

static const struct qcom_reset_map msm8953_resets[] = {
	[GCC_QUSB2_PHY_BCR] = { 0x4103c, 0 },
	[GCC_USB3PHY_PHY_BCR] = { 0x3f03c, 0 },
	[GCC_USB3_PHY_BCR] = { 0x3f034, 0 },
	[GCC_USB_30_BCR] = { 0x3f070, 0 },
	[GCC_SDCC1_BCR] = { 0x42000, 0 },
};

static const struct qcom_power_map msm8953_power_domains[] = {
	[USB30_GDSC] = { 0x3f078 },
};

static const struct msm_clk_data msm8953_data = {
	.power_domains = msm8953_power_domains,
	.num_power_domains = ARRAY_SIZE(msm8953_power_domains),
	.resets = msm8953_resets,
	.num_resets = ARRAY_SIZE(msm8953_resets),
	.clks = msm8953_clks,
	.num_clks = ARRAY_SIZE(msm8953_clks),
	.set_rate = msm8953_set_rate,
};

static const struct udevice_id msm8953_clk_ids[] = {
	{ .compatible = "qcom,gcc-msm8953", .data = (ulong)&msm8953_data },
	{ }
};

U_BOOT_DRIVER(msm8953_clk) = {
	.name = "msm8953_clk",
	.id = UCLASS_NOP,
	.of_match = msm8953_clk_ids,
	.bind = qcom_cc_bind,
};
