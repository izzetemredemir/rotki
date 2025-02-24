<script lang="ts" setup>
import { useTradesForm } from '@/composables/history/trades/form';
import ExternalTradeForm from '@/components/history/trades/ExternalTradeForm.vue';
import BigDialog from '@/components/dialogs/BigDialog.vue';
import type { Trade } from '@/types/history/trade';

const props = withDefaults(
  defineProps<{
    editableItem?: Trade | null;
    loading?: boolean;
  }>(),
  {
    editableItem: null,
    loading: false,
  },
);

const { editableItem } = toRefs(props);

const { closeDialog, openDialog, stateUpdated, submitting, trySubmit } = useTradesForm();

const { t } = useI18n();

const title = computed<string>(() =>
  get(editableItem) ? t('closed_trades.dialog.edit.title') : t('closed_trades.dialog.add.title'),
);

const subtitle = computed<string>(() =>
  get(editableItem) ? t('closed_trades.dialog.edit.subtitle') : '',
);
</script>

<template>
  <BigDialog
    :display="openDialog"
    :title="title"
    :subtitle="subtitle"
    :primary-action="t('common.actions.save')"
    :action-disabled="loading"
    :loading="submitting"
    :prompt-on-close="stateUpdated"
    @confirm="trySubmit()"
    @cancel="closeDialog()"
  >
    <ExternalTradeForm :editable-item="editableItem" />
  </BigDialog>
</template>
