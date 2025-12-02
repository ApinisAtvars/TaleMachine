<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import SidebarProvider from '@/components/ui/sidebar/SidebarProvider.vue';
import SidebarTrigger from '@/components/ui/sidebar/SidebarTrigger.vue';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ChartNetwork, MessageSquare } from "lucide-vue-next";

const route = useRoute()
const router = useRouter()

const activeTab = computed({
  get: () => route.path === '/graph' ? 'graph' : 'chat',
  set: (val) => {
    router.push(val === 'graph' ? '/graph' : '/')
  }
})
</script>

<template>
  <SidebarProvider>
    <AppSidebar />
    <main class="w-full flex flex-col h-screen overflow-hidden">
      <div class="flex items-center border-b px-4 py-2 gap-2">
        <SidebarTrigger />
        <Tabs v-model="activeTab" class="w-full max-w-[400px]">
          <TabsList class="grid w-full grid-cols-2">
            <TabsTrigger value="chat">
              <MessageSquare class="size-4 mr-2" />
              Chat
            </TabsTrigger>
            <TabsTrigger value="graph">
              <ChartNetwork class="size-4 mr-2" />
              Graph
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>
      <div class="flex-1 overflow-auto p-4">
        <RouterView />
      </div>
    </main>
  </SidebarProvider>
</template>

<style scoped>
</style>

