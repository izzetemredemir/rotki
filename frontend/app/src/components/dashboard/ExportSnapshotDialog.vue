<script setup lang="ts">
import dayjs from 'dayjs';
import { downloadFileByBlobResponse } from '@/utils/download';
import { bigNumberifyFromRef } from '@/utils/bignumbers';
import { useStatisticsStore } from '@/store/statistics';
import { useConfirmStore } from '@/store/confirm';
import { useMessageStore } from '@/store/message';
import { useGeneralSettingsStore } from '@/store/settings/general';
import { useSnapshotApi } from '@/composables/api/settings/snapshot-api';
import { useInterop } from '@/composables/electron-interop';
import EditSnapshotDialog from '@/components/dashboard/edit-snapshot/EditSnapshotDialog.vue';
import AmountDisplay from '@/components/display/amount/AmountDisplay.vue';
import DateDisplay from '@/components/display/DateDisplay.vue';
import type { BigNumber, Message } from '@rotki/common';

const display = defineModel<boolean>({ default: false, required: true });

const props = withDefaults(
  defineProps<{
    timestamp?: number;
    balance?: number;
  }>(),
  {
    balance: 0,
    timestamp: 0,
  },
);

const { t } = useI18n();

const { balance, timestamp } = toRefs(props);
const { currencySymbol } = storeToRefs(useGeneralSettingsStore());

const editMode = ref<boolean>(false);
const { setMessage } = useMessageStore();
const snapshotApi = useSnapshotApi();
const { appSession, openDirectory } = useInterop();

const formattedSelectedBalance = computed<BigNumber | null>(() => {
  if (get(balance))
    return get(bigNumberifyFromRef(balance));

  return null;
});

async function downloadSnapshot() {
  const response = await snapshotApi.downloadSnapshot(get(timestamp));

  const date = dayjs(get(timestamp) * 1000).format('YYYYDDMMHHmmss');
  const fileName = `${date}-snapshot.zip`;

  downloadFileByBlobResponse(response, fileName);

  set(display, false);
}

async function exportSnapshotCSV() {
  let message: Message | null = null;

  try {
    if (appSession) {
      const path = await openDirectory(t('common.select_directory'));

      if (!path)
        return;

      const success = await snapshotApi.exportSnapshotCSV({
        path,
        timestamp: get(timestamp),
      });

      message = {
        description: success
          ? t('dashboard.snapshot.download.message.success')
          : t('dashboard.snapshot.download.message.failure'),
        success,
        title: t('dashboard.snapshot.download.message.title'),
      };

      set(display, false);
    }
    else {
      await downloadSnapshot();
    }
  }
  catch (error: any) {
    message = {
      description: error.message,
      success: false,
      title: t('dashboard.snapshot.download.message.title'),
    };
  }

  if (message)
    setMessage(message);
}

async function exportSnapshot() {
  if (appSession)
    await exportSnapshotCSV();
  else await downloadSnapshot();
}

const { fetchNetValue } = useStatisticsStore();

async function deleteSnapshot() {
  let message: Message | null;

  try {
    const success = await snapshotApi.deleteSnapshot({
      timestamp: get(timestamp),
    });

    message = {
      description: success
        ? t('dashboard.snapshot.delete.message.success')
        : t('dashboard.snapshot.delete.message.failure'),
      success,
      title: t('dashboard.snapshot.delete.message.title'),
    };

    set(display, false);
    await fetchNetValue();
  }
  catch (error: any) {
    message = {
      description: error.message,
      success: false,
      title: t('dashboard.snapshot.download.message.title'),
    };
  }

  setMessage(message);
}

function finish() {
  set(display, false);
  set(editMode, false);
}

const { show } = useConfirmStore();

function showDeleteConfirmation() {
  show(
    {
      message: t('dashboard.snapshot.delete.dialog.message'),
      title: t('dashboard.snapshot.delete.dialog.title'),
    },
    deleteSnapshot,
  );
}
</script>

<template>
  <RuiDialog
    v-model="display"
    max-width="600"
  >
    <RuiCard>
      <template #header>
        {{ t('dashboard.snapshot.export_database_snapshot') }}
      </template>
      <template #subheader>
        {{ t('dashboard.snapshot.subtitle') }}
      </template>
      <div>
        <div class="text-rui-text-secondary">
          {{ t('common.datetime') }}:
        </div>
        <DateDisplay
          :timestamp="timestamp"
          class="font-bold"
        />
      </div>
      <div class="pt-2">
        <div class="text-rui-text-secondary">
          {{ t('common.balance') }}:
        </div>
        <AmountDisplay
          v-if="formattedSelectedBalance"
          :value="formattedSelectedBalance"
          :fiat-currency="currencySymbol"
          class="font-bold"
        />
      </div>
      <template #footer>
        <RuiButton
          color="primary"
          @click="editMode = true"
        >
          <template #prepend>
            <RuiIcon name="edit-line" />
          </template>
          {{ t('common.actions.edit') }}
        </RuiButton>
        <RuiButton
          color="error"
          @click="showDeleteConfirmation()"
        >
          <template #prepend>
            <RuiIcon name="delete-bin-5-line" />
          </template>
          {{ t('common.actions.delete') }}
        </RuiButton>
        <div class="grow" />
        <RuiButton
          color="primary"
          @click="exportSnapshot()"
        >
          <template #prepend>
            <RuiIcon name="file-download-line" />
          </template>
          {{ t('common.actions.download') }}
        </RuiButton>
      </template>
    </RuiCard>
    <EditSnapshotDialog
      v-if="editMode"
      :timestamp="timestamp"
      @close="editMode = false"
      @finish="finish()"
    />
  </RuiDialog>
</template>
