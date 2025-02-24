<script setup lang="ts">
import { Section } from '@/types/status';
import { TaskType } from '@/types/task-type';
import { useStatusStore } from '@/store/status';
import { useTaskStore } from '@/store/tasks';
import { useBalances } from '@/composables/balances';
import { useAggregatedBalances } from '@/composables/balances/aggregated';

const emit = defineEmits<{
  (e: 'click'): void;
}>();

const { isTaskRunning } = useTaskStore();
const { refreshPrices } = useBalances();
const { isLoading } = useStatusStore();

const refreshing = isLoading(Section.PRICES);
const { t } = useI18n();

const loadingData = computed<boolean>(
  () =>
    get(isTaskRunning(TaskType.QUERY_BALANCES))
    || get(isTaskRunning(TaskType.QUERY_BLOCKCHAIN_BALANCES))
    || get(isTaskRunning(TaskType.QUERY_EXCHANGE_BALANCES))
    || get(isTaskRunning(TaskType.MANUAL_BALANCES)),
);

const { assets } = useAggregatedBalances();

async function refresh() {
  emit('click');
  await refreshPrices(true, get(assets()));
}

const disabled = computed<boolean>(() => get(refreshing) || get(loadingData));
</script>

<template>
  <RuiButton
    variant="outlined"
    color="primary"
    :loading="refreshing"
    data-cy="price-refresh"
    :disabled="disabled"
    @click="refresh()"
  >
    <template #prepend>
      <RuiIcon name="refresh-line" />
    </template>
    {{ t('price_refresh.button') }}
  </RuiButton>
</template>
