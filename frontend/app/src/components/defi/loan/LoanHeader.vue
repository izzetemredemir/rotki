<script setup lang="ts">
import HashLink from '@/components/helper/HashLink.vue';

defineProps<{
  owner: string;
}>();

const { t } = useI18n();
</script>

<template>
  <RuiCard>
    <template #header>
      <slot />
    </template>
    <template #subheader>
      {{ t('loan_header.owned_by') }}
      <HashLink
        :text="owner"
        class="font-medium mt-3"
      />
    </template>
  </RuiCard>
</template>
