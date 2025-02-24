<script setup lang="ts">
import { assetSymbolToIdentifierMap } from '@rotki/common';
import { usePremium } from '@/composables/premium';
import PremiumLock from '@/components/premium/PremiumLock.vue';
import AmountDisplay from '@/components/display/amount/AmountDisplay.vue';
import LoanRow from '@/components/defi/loan/LoanRow.vue';
import PercentageDisplay from '@/components/display/PercentageDisplay.vue';
import StatCard from '@/components/display/StatCard.vue';
import type { MakerDAOVaultModel } from '@/types/defi/maker';

const props = defineProps<{
  vault: MakerDAOVaultModel;
}>();

const assetPadding = 3;

const { vault } = toRefs(props);
const premium = usePremium();
const { t } = useI18n();

const valueLost = computed(() => {
  const makerVault = get(vault);
  if (!('totalInterestOwed' in makerVault))
    return Zero;

  const { totalInterestOwed, totalLiquidated } = makerVault;
  return totalLiquidated.usdValue.plus(totalInterestOwed);
});

const liquidated = computed(() => {
  const makerVault = get(vault);
  if (!('totalLiquidated' in makerVault))
    return undefined;

  return makerVault.totalLiquidated;
});

const totalInterestOwed = computed(() => {
  const makerVault = get(vault);
  if (!('totalInterestOwed' in makerVault))
    return Zero;

  return makerVault.totalInterestOwed;
});
const dai: string = assetSymbolToIdentifierMap.DAI;
</script>

<template>
  <StatCard
    :title="t('loan_liquidation.title')"
    :class="$style.liquidation"
  >
    <div
      class="pb-5"
      :class="$style.upper"
    >
      <LoanRow :title="t('loan_liquidation.liquidation_price')">
        <AmountDisplay
          fiat-currency="USD"
          :value="vault.liquidationPrice"
        />
      </LoanRow>

      <RuiDivider class="my-4" />

      <LoanRow
        :title="t('loan_liquidation.minimum_ratio')"
        :medium="false"
      >
        <PercentageDisplay :value="vault.liquidationRatio" />
      </LoanRow>
    </div>
    <div>
      <span
        :class="$style.header"
        class="text-rui-text"
      >
        {{ t('loan_liquidation.liquidation_events') }}
      </span>
      <template v-if="premium">
        <RuiSkeletonLoader
          v-if="!liquidated"
          class="max-w-[28.125rem] pt-3"
          rounded="full"
          type="paragraph"
        />
        <div v-else-if="liquidated.amount.gt(0)">
          <div class="mb-2">
            <LoanRow :title="t('loan_liquidation.liquidated_collateral')">
              <AmountDisplay
                :asset-padding="assetPadding"
                :value="liquidated.amount"
                :asset="vault.collateral.asset"
              />
            </LoanRow>
            <LoanRow :medium="false">
              <AmountDisplay
                :asset-padding="assetPadding"
                :value="liquidated.usdValue"
                fiat-currency="USD"
              />
            </LoanRow>
          </div>
          <LoanRow :title="t('loan_liquidation.outstanding_debt')">
            <AmountDisplay
              :asset-padding="assetPadding"
              :value="totalInterestOwed"
              :asset="dai"
            />
          </LoanRow>

          <RuiDivider class="my-4" />

          <LoanRow :title="t('loan_liquidation.total_value_lost')">
            <AmountDisplay
              :asset-padding="assetPadding"
              :value="valueLost"
              fiat-currency="USD"
            />
          </LoanRow>
        </div>
        <div
          v-else
          v-text="t('loan_liquidation.no_events')"
        />
      </template>
      <div
        v-else
        class="text-right"
      >
        <PremiumLock />
      </div>
    </div>
  </StatCard>
</template>

<style lang="scss" module>
.header {
  font-size: 20px;
  font-weight: 500;
}

.upper {
  min-height: 100px;
  height: 45%;
}

.liquidation {
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
