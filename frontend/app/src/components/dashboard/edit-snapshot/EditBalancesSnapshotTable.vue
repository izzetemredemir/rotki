<script setup lang="ts">
import { CURRENCY_USD } from '@/types/currencies';
import { isNft } from '@/utils/nft';
import { BalanceType } from '@/types/balances';
import { bigNumberSum } from '@/utils/calculation';
import { useGeneralSettingsStore } from '@/store/settings/general';
import { useBalancePricesStore } from '@/store/balances/prices';
import { useEditBalancesSnapshotForm } from '@/composables/snapshots/edit-balance/form';
import EditBalancesSnapshotLocationSelector
  from '@/components/dashboard/edit-snapshot/EditBalancesSnapshotLocationSelector.vue';
import ConfirmDialog from '@/components/dialogs/ConfirmDialog.vue';
import ConfirmSnapshotConflictReplacementDialog
  from '@/components/snapshots/ConfirmSnapshotConflictReplacementDialog.vue';
import BigDialog from '@/components/dialogs/BigDialog.vue';
import AmountDisplay from '@/components/display/amount/AmountDisplay.vue';
import RowActions from '@/components/helper/RowActions.vue';
import NftDetails from '@/components/helper/NftDetails.vue';
import AssetDetails from '@/components/helper/AssetDetails.vue';
import AssetSelect from '@/components/inputs/AssetSelect.vue';
import EditBalancesSnapshotForm from '@/components/dashboard/edit-snapshot/EditBalancesSnapshotForm.vue';
import type { BalanceSnapshot, BalanceSnapshotPayload, Snapshot } from '@/types/snapshots';
import type { DataTableColumn, DataTableSortData } from '@rotki/ui-library';
import type { BigNumber } from '@rotki/common';

const props = defineProps<{
  modelValue: Snapshot;
  timestamp: number;
}>();

const emit = defineEmits<{
  (e: 'update:step', step: number): void;
  (e: 'update:model-value', value: Snapshot): void;
}>();

const { t } = useI18n();

type IndexedBalanceSnapshot = BalanceSnapshot & { index: number; categoryLabel: string };

const { closeDialog, openDialog, setOpenDialog, setSubmitFunc, stateUpdated, submitting, trySubmit } = useEditBalancesSnapshotForm();

const { timestamp } = toRefs(props);
const { currencySymbol } = storeToRefs(useGeneralSettingsStore());
const showDeleteConfirmation = ref<boolean>(false);
const indexToEdit = ref<number | null>(null);
const indexToDelete = ref<number | null>(null);
const locationToDelete = ref<string>('');
const form = ref<(BalanceSnapshotPayload & { location: string }) | null>(null);
const tableRef = ref<any>();
const sort = ref<DataTableSortData<BalanceSnapshot>>({
  column: 'usdValue',
  direction: 'desc',
});
const assetSearch = ref<string>('');
const snapshotForm = ref<InstanceType<typeof EditBalancesSnapshotForm>>();

const { exchangeRate } = useBalancePricesStore();
const fiatExchangeRate = computed<BigNumber>(() => get(exchangeRate(get(currencySymbol))) ?? One);

const data = computed<IndexedBalanceSnapshot[]>(() =>
  props.modelValue.balancesSnapshot.map((item, index) => ({
    ...item,
    categoryLabel: isNft(item.assetIdentifier)
      ? `${item.category} (${t('dashboard.snapshot.edit.dialog.balances.nft')})`
      : item.category,
    index,
  })),
);

const filteredData = computed<IndexedBalanceSnapshot[]>(() => {
  const allData = get(data);
  const search = get(assetSearch);
  if (!search)
    return allData;

  return allData.filter(({ assetIdentifier }) => assetIdentifier === search);
});

const total = computed<BigNumber>(() => {
  const totalEntry = props.modelValue.locationDataSnapshot.find(item => item.location === 'total');

  if (!totalEntry)
    return Zero;

  return totalEntry.usdValue;
});

const tableHeaders = computed<DataTableColumn<IndexedBalanceSnapshot>[]>(() => [
  {
    cellClass: 'py-2',
    class: 'w-[10rem]',
    key: 'categoryLabel',
    label: t('common.category'),
    sortable: true,
  },
  {
    cellClass: 'py-0',
    key: 'assetIdentifier',
    label: t('common.asset'),
    sortable: true,
  },
  {
    align: 'end',
    key: 'amount',
    label: t('common.amount'),
    sortable: true,
  },
  {
    align: 'end',
    key: 'usdValue',
    label: t('common.value_in_symbol', { symbol: get(currencySymbol) }),
    sortable: true,
  },
  {
    cellClass: 'py-2',
    class: 'w-[6.25rem]',
    key: 'action',
    label: '',
  },
]);

function input(value: Snapshot) {
  emit('update:model-value', value);
}

function updateStep(step: number) {
  emit('update:step', step);
}

const conflictedBalanceSnapshot = ref<BalanceSnapshot | null>(null);

function checkAssetExist(asset: string) {
  const assetFound = props.modelValue.balancesSnapshot.find(item => item.assetIdentifier === asset);
  set(conflictedBalanceSnapshot, assetFound || null);
}

function closeConvertToEditDialog() {
  set(conflictedBalanceSnapshot, null);
}

function cancelConvertToEdit() {
  set(form, {
    ...get(form),
    assetIdentifier: '',
  });

  closeConvertToEditDialog();
}

function convertToEdit() {
  assert(conflictedBalanceSnapshot);
  const item = get(data).find(
    ({ assetIdentifier }) => assetIdentifier === get(conflictedBalanceSnapshot)?.assetIdentifier,
  );

  if (item)
    editClick(item);

  closeConvertToEditDialog();
}

function editClick(item: IndexedBalanceSnapshot) {
  set(indexToEdit, item.index);

  const convertedFiatValue
    = get(currencySymbol) === CURRENCY_USD
      ? item.usdValue.toFixed()
      : item.usdValue.multipliedBy(get(fiatExchangeRate)).toFixed();

  set(form, {
    ...item,
    amount: item.amount.toFixed(),
    location: '',
    usdValue: convertedFiatValue,
  });

  setOpenDialog(true);
}

const existingLocations = computed<string[]>(() =>
  props.modelValue.locationDataSnapshot.filter(item => item.location !== 'total').map(item => item.location),
);

function deleteClick(item: IndexedBalanceSnapshot) {
  set(indexToDelete, item.index);
  set(showDeleteConfirmation, true);
  set(locationToDelete, '');
}

function add() {
  set(indexToEdit, null);
  set(form, {
    amount: '',
    assetIdentifier: '',
    category: BalanceType.ASSET,
    location: '',
    timestamp: get(timestamp),
    usdValue: '',
  });
  setOpenDialog(true);
}

const previewLocationBalance = computed<Record<string, BigNumber> | null>(() => {
  const formVal = get(form);

  if (!formVal?.amount || !formVal.usdValue || !formVal.location)
    return null;

  const index = get(indexToEdit);
  const val = props.modelValue;

  const locationData = val.locationDataSnapshot.find(item => item.location === formVal.location);

  const usdValueInBigNumber = bigNumberify(formVal.usdValue);
  const convertedUsdValue
    = get(currencySymbol) === CURRENCY_USD ? usdValueInBigNumber : usdValueInBigNumber.dividedBy(get(fiatExchangeRate));

  if (!locationData) {
    return {
      after: convertedUsdValue,
      before: Zero,
    };
  }

  const isCurrentLiability = formVal.category === 'liability';
  const currentFactor = bigNumberify(isCurrentLiability ? -1 : 1);
  let usdValueDiff = convertedUsdValue.multipliedBy(currentFactor);

  const balancesSnapshot = val.balancesSnapshot;

  if (index !== null) {
    const isPrevLiability = balancesSnapshot[index].category === 'liability';
    const prevFactor = bigNumberify(isPrevLiability ? -1 : 1);
    usdValueDiff = usdValueDiff.minus(balancesSnapshot[index].usdValue.multipliedBy(prevFactor));
  }

  return {
    after: locationData.usdValue.plus(usdValueDiff),
    before: locationData.usdValue,
  };
});

const previewDeleteLocationBalance = computed<Record<string, BigNumber> | null>(() => {
  const index = get(indexToDelete);
  const location = get(locationToDelete);

  if (index === null || !location)
    return null;

  const val = props.modelValue;
  const locationData = val.locationDataSnapshot.find(item => item.location === location);
  const balanceData = val.balancesSnapshot[index];

  if (!locationData || !balanceData)
    return null;

  const isCurrentLiability = balanceData.category === 'liability';
  const currentFactor = bigNumberify(isCurrentLiability ? 1 : -1);
  const usdValueDiff = balanceData.usdValue.multipliedBy(currentFactor);

  return {
    after: locationData.usdValue.plus(usdValueDiff),
    before: locationData.usdValue,
  };
});

function updateData(
  balancesSnapshot: BalanceSnapshot[],
  location = '',
  calculatedBalance: Record<string, BigNumber> | null = null,
) {
  const val = props.modelValue;
  const locationDataSnapshot = [...val.locationDataSnapshot];

  if (location) {
    const locationDataIndex = locationDataSnapshot.findIndex(item => item.location === location);
    if (locationDataIndex > -1) {
      locationDataSnapshot[locationDataIndex].usdValue = calculatedBalance!.after;
    }
    else {
      locationDataSnapshot.push({
        location,
        timestamp: get(timestamp),
        usdValue: calculatedBalance!.after,
      });
    }
  }

  const assetsValue = balancesSnapshot.map((item: BalanceSnapshot) => {
    if (item.category === 'asset')
      return item.usdValue;

    return item.usdValue.negated();
  });

  const total = bigNumberSum(assetsValue);

  const totalDataIndex = locationDataSnapshot.findIndex(item => item.location === 'total');

  locationDataSnapshot[totalDataIndex].usdValue = total;

  input({
    balancesSnapshot,
    locationDataSnapshot,
  });
}

function save() {
  const formVal = get(form);

  if (!formVal)
    return;

  const index = get(indexToEdit);
  const val = props.modelValue;
  const timestampVal = get(timestamp);

  const balancesSnapshot = [...val.balancesSnapshot];
  const payload = {
    amount: bigNumberify(formVal.amount),
    assetIdentifier: formVal.assetIdentifier,
    category: formVal.category,
    timestamp: timestampVal,
    usdValue: bigNumberify(formVal.usdValue),
  };

  if (index !== null)
    balancesSnapshot[index] = payload;
  else balancesSnapshot.unshift(payload);

  updateData(balancesSnapshot, formVal.location, get(previewLocationBalance));
  get(snapshotForm)?.submitPrice();
  clearEditDialog();
}

setSubmitFunc(save);

function clearEditDialog() {
  closeDialog();
  set(indexToEdit, null);
  set(form, null);
}

function updateForm(newForm: BalanceSnapshotPayload & { location: string }) {
  set(form, newForm);
}

function clearDeleteDialog() {
  set(indexToDelete, null);
  set(showDeleteConfirmation, false);
  set(locationToDelete, '');
}

function confirmDelete() {
  const index = get(indexToDelete);
  const val = props.modelValue;
  const location = get(locationToDelete);

  if (index === null)
    return;

  const balancesSnapshot = [...val.balancesSnapshot];
  balancesSnapshot.splice(index, 1);

  updateData(balancesSnapshot, location, get(previewDeleteLocationBalance));
  clearDeleteDialog();
}
</script>

<template>
  <div>
    <div class="grid md:grid-cols-2 p-4 border-b border-default">
      <AssetSelect
        v-model="assetSearch"
        outlined
        hide-details
        clearable
        :label="t('dashboard.snapshot.search_asset')"
      />
    </div>
    <RuiDataTable
      ref="tableRef"
      v-model:sort="sort"
      class="table-inside-dialog !max-h-[calc(100vh-26.25rem)]"
      :cols="tableHeaders"
      :rows="filteredData"
      :scroller="tableRef?.$el"
      row-attr="assetIdentifier"
      dense
    >
      <template #item.categoryLabel="{ row }">
        <span>{{ toSentenceCase(row.categoryLabel) }}</span>
      </template>

      <template #item.assetIdentifier="{ row }">
        <AssetDetails
          v-if="!isNft(row.assetIdentifier)"
          class="[&_.avatar]:ml-1.5 [&_.avatar]:mr-2"
          :asset="row.assetIdentifier"
          :opens-details="false"
          :enable-association="false"
        />
        <NftDetails
          v-else
          :identifier="row.assetIdentifier"
        />
      </template>

      <template #item.amount="{ row }">
        <AmountDisplay :value="row.amount" />
      </template>

      <template #item.usdValue="{ row }">
        <AmountDisplay
          :value="row.usdValue"
          :amount="row.amount"
          :price-asset="row.assetIdentifier"
          :fiat-currency="CURRENCY_USD"
          :timestamp="timestamp"
        />
      </template>

      <template #item.action="{ row }">
        <RowActions
          :edit-tooltip="t('dashboard.snapshot.edit.dialog.actions.edit_item')"
          :delete-tooltip="t('dashboard.snapshot.edit.dialog.actions.delete_item')"
          @edit-click="editClick(row)"
          @delete-click="deleteClick(row)"
        />
      </template>
    </RuiDataTable>
    <div
      class="border-t-2 border-rui-grey-300 dark:border-rui-grey-800 relative z-[2] flex items-center justify-between gap-4 p-2"
    >
      <div>
        <div class="text-caption">
          {{ t('common.total') }}:
        </div>
        <div class="font-bold text-h6 -mt-1">
          <AmountDisplay
            :value="total"
            :amount="total"
            :price-asset="CURRENCY_USD"
            :fiat-currency="CURRENCY_USD"
            :timestamp="timestamp"
          />
        </div>
      </div>

      <div class="flex gap-2">
        <RuiButton
          variant="text"
          color="primary"
          @click="add()"
        >
          <template #prepend>
            <RuiIcon name="add-circle-line" />
          </template>
          {{ t('dashboard.snapshot.edit.dialog.actions.add_new_entry') }}
        </RuiButton>
        <RuiButton
          color="primary"
          @click="updateStep(2)"
        >
          {{ t('common.actions.next') }}
          <template #append>
            <RuiIcon name="arrow-right-line" />
          </template>
        </RuiButton>
      </div>
    </div>

    <BigDialog
      :display="openDialog"
      :title="
        indexToEdit !== null
          ? t('dashboard.snapshot.edit.dialog.balances.edit_title')
          : t('dashboard.snapshot.edit.dialog.balances.add_title')
      "
      :primary-action="t('common.actions.save')"
      :loading="submitting"
      :prompt-on-close="stateUpdated"
      @confirm="trySubmit()"
      @cancel="clearEditDialog()"
    >
      <EditBalancesSnapshotForm
        v-if="form"
        ref="snapshotForm"
        :edit="!!indexToEdit"
        :form="form"
        :preview-location-balance="previewLocationBalance"
        :locations="indexToEdit !== null ? existingLocations : []"
        :timestamp="timestamp"
        @update:form="updateForm($event)"
        @update:asset="checkAssetExist($event)"
      />

      <ConfirmSnapshotConflictReplacementDialog
        :snapshot="conflictedBalanceSnapshot"
        @cancel="cancelConvertToEdit()"
        @confirm="convertToEdit()"
      />
    </BigDialog>

    <ConfirmDialog
      :display="showDeleteConfirmation"
      :title="t('dashboard.snapshot.edit.dialog.balances.delete_title')"
      :message="t('dashboard.snapshot.edit.dialog.balances.delete_confirmation')"
      max-width="700"
      @cancel="clearDeleteDialog()"
      @confirm="confirmDelete()"
    >
      <div class="mt-4">
        <EditBalancesSnapshotLocationSelector
          v-model="locationToDelete"
          :locations="existingLocations"
          :preview-location-balance="previewDeleteLocationBalance"
        />
      </div>
    </ConfirmDialog>
  </div>
</template>
