<script setup lang="ts">
import { helpers, required } from '@vuelidate/validators';
import { toMessages } from '@/utils/validation';
import { isBlockchain } from '@/types/blockchain/chains';
import { ApiValidationError } from '@/types/api/errors';
import { getAccountAddress } from '@/utils/blockchain/accounts/utils';
import { convertFromTimestamp, convertToTimestamp } from '@/utils/date';
import { hasAccountAddress } from '@/utils/blockchain/accounts';
import { useBlockchainStore } from '@/store/blockchain';
import { useMessageStore } from '@/store/message';
import { useGeneralSettingsStore } from '@/store/settings/general';
import { useCalendarEventForm } from '@/composables/calendar/form';
import { useCalendarApi } from '@/composables/history/calendar';
import CounterpartyInput from '@/components/inputs/CounterpartyInput.vue';
import BlockchainAccountSelector from '@/components/helper/BlockchainAccountSelector.vue';
import CalendarColorInput from '@/components/calendar/CalendarColorInput.vue';
import CalendarReminder from '@/components/calendar/CalendarReminder.vue';
import DateTimePicker from '@/components/inputs/DateTimePicker.vue';
import type { AddressData, BlockchainAccount } from '@/types/blockchain/accounts';
import type { Dayjs } from 'dayjs';
import type { Writeable } from '@rotki/common';
import type { CalendarEvent, CalendarEventPayload } from '@/types/history/calendar';

const props = withDefaults(
  defineProps<{
    editableItem?: CalendarEvent;
    selectedDate: Dayjs;
  }>(),
  {
    editableItem: undefined,
  },
);

const { editableItem, selectedDate } = toRefs(props);

const { t } = useI18n();
const { autoDeleteCalendarEntries } = storeToRefs(useGeneralSettingsStore());

const name = ref<string>('');
const description = ref<string>('');
const counterparty = ref<string>('');
const datetime = ref<string>('');
const accounts = ref<BlockchainAccount<AddressData>[]>([]);
const color = ref<string>('');
const autoDelete = ref(get(autoDeleteCalendarEntries));

const errorMessages = ref<Record<string, string[]>>({});
const reminderRef = ref();

const externalServerValidation = () => true;

const rules = {
  accounts: { externalServerValidation },
  autoDelete: { externalServerValidation },
  counterparty: { externalServerValidation },
  description: { externalServerValidation },
  name: {
    required: helpers.withMessage(t('calendar.form.name.validation.non_empty'), required),
  },
  timestamp: { externalServerValidation },
};

const { setSubmitFunc, setValidation } = useCalendarEventForm();

const v$ = setValidation(
  rules,
  {
    accounts,
    autoDelete,
    counterparty,
    description,
    name,
    timestamp: datetime,
  },
  {
    $autoDirty: true,
    $externalResults: errorMessages,
  },
);

watchImmediate(selectedDate, (selectedDate) => {
  const startOfTheDate = selectedDate.set('hours', 0).set('minutes', 0).set('seconds', 0);
  set(datetime, convertFromTimestamp(startOfTheDate.unix()));
});

const { accounts: accountsPerChain } = storeToRefs(useBlockchainStore());

watchImmediate(editableItem, (editableItem) => {
  if (editableItem) {
    set(name, editableItem.name);
    set(description, editableItem.description);
    set(counterparty, editableItem.counterparty);
    set(datetime, convertFromTimestamp(editableItem.timestamp));
    set(color, editableItem.color);
    set(autoDelete, editableItem.autoDelete);

    if (editableItem.address && editableItem.blockchain) {
      const accountFound = Object.values(get(accountsPerChain))
        .flatMap(x => x)
        .filter(hasAccountAddress)
        .find(
          item =>
            getAccountAddress(item) === editableItem.address
            && (!editableItem.blockchain || editableItem.blockchain === item.chain),
        );

      if (accountFound)
        set(accounts, [accountFound]);
    }
  }
});

const { addCalendarEvent, editCalendarEvent } = useCalendarApi();
const { setMessage } = useMessageStore();

async function save() {
  const accountVal = get(accounts)[0];
  const payload: Writeable<CalendarEventPayload> = {
    autoDelete: get(autoDelete),
    color: get(color),
    description: get(description),
    name: get(name),
    timestamp: convertToTimestamp(get(datetime)),
  };

  if (accountVal) {
    payload.address = getAccountAddress(accountVal);
    payload.blockchain = isBlockchain(accountVal.chain) ? accountVal.chain : undefined;
  }

  const counterpartyVal = get(counterparty);
  if (counterpartyVal)
    payload.counterparty = counterpartyVal;

  const editableItemVal = get(editableItem);
  const editing = !!editableItemVal;

  try {
    const result = !editing
      ? await addCalendarEvent(payload)
      : await editCalendarEvent({ ...payload, identifier: editableItemVal.identifier });

    const eventId = result.entryId;
    if (isDefined(eventId)) {
      get(v$).$reset();
      await get(reminderRef).saveTemporaryReminder(eventId);
    }

    return true;
  }
  catch (error: any) {
    const errorTitle = editing ? t('calendar.edit_error') : t('calendar.add_error');

    let errors = error.message;
    if (error instanceof ApiValidationError)
      errors = error.getValidationErrors(payload);

    if (typeof errors === 'string') {
      setMessage({
        description: errors,
        success: false,
        title: errorTitle,
      });
    }
    else {
      set(errorMessages, errors);
    }

    return false;
  }
}

setSubmitFunc(save);
</script>

<template>
  <div class="flex flex-col gap-4">
    <div>
      <DateTimePicker
        v-model="datetime"
        :label="t('common.datetime')"
        persistent-hint
        data-cy="datetime"
        :error-messages="toMessages(v$.timestamp)"
        @blur="v$.timestamp.$touch()"
      />

      <CalendarReminder
        ref="reminderRef"
        class="pt-2"
        :editable-item="editableItem"
      />
    </div>

    <div class="flex gap-4 pt-4">
      <RuiTextField
        v-model="name"
        class="flex-1"
        :label="t('common.name')"
        variant="outlined"
        color="primary"
        :error-messages="toMessages(v$.name)"
        @blur="v$.name.$touch()"
      />

      <div class="pt-3">
        <CalendarColorInput v-model="color" />
      </div>
    </div>

    <RuiTextArea
      v-model="description"
      :label="t('common.description')"
      variant="outlined"
      color="primary"
      min-rows="5"
      :error-messages="toMessages(v$.description)"
      :hint="t('common.optional')"
      @blur="v$.description.$touch()"
    />

    <BlockchainAccountSelector
      v-model="accounts"
      outlined
      :label="t('common.account')"
      :error-messages="toMessages(v$.accounts)"
      show-details
      :custom-hint="t('common.optional')"
    />

    <CounterpartyInput
      v-model="counterparty"
      :label="t('common.counterparty')"
      data-cy="counterparty"
      :error-messages="toMessages(v$.counterparty)"
      :hint="t('common.optional')"
      persistent-hint
      @blur="v$.counterparty.$touch()"
    />

    <RuiCheckbox
      v-model="autoDelete"
      :label="t('calendar.dialog.settings.auto_delete_entry')"
      color="primary"
      hide-details
    />
  </div>
</template>
