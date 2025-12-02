<script setup lang="ts">
import { ArrowUpIcon } from 'lucide-vue-next'
import { InputGroup, InputGroupAddon, InputGroupButton, InputGroupTextarea } from '@/components/ui/input-group'
// import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
</script>

<template>
    <InputGroup>
      <InputGroupTextarea placeholder="Ask, Search or Chat..." />
      <InputGroupAddon align="block-end">
        <InputGroupButton
          variant="default"
          class="rounded-full"
          size="icon-xs"
          disabled
        >
          <ArrowUpIcon class="size-4" />
          <span class="sr-only">Send</span>
        </InputGroupButton>
      </InputGroupAddon>
    </InputGroup>
</template>

<style scoped>
</style>
