<script setup lang="ts">
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarHeader,
  SidebarGroupContent,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenu,
} from "@/components/ui/sidebar";

import { useStoryStore } from "@/stores/storyStore";
import { storeToRefs } from "pinia";

const storyStore = useStoryStore();

storyStore.fetchAllStories();

const stories = storeToRefs(storyStore).stories;
</script>

<template>
    <Sidebar>
        <SidebarHeader class="p-2">
            <RouterLink to="/">
            <h2 class="text-lg font-bold flex justify-center">TaleMachine</h2>
            </RouterLink>
        </SidebarHeader>
        <SidebarContent>
        <SidebarGroup>
            <SidebarGroupContent>
            <SidebarMenu>
                <SidebarMenuItem
                  v-for="story in stories"
                  :key="story.id"
                  class="transition-list-item group/item"
                >
                  <RouterLink :to="`/chat/${story.id}`">
                <template #default="{ isActive }">
                    <SidebarMenuButton
                        :class="{
                            'bg-muted text-primary': isActive,
                        }"
                        @click="storyStore.fetchStory(story.id)"
                    >
                        {{ story.title }}
                    </SidebarMenuButton>
                </template>
                  </RouterLink>
                </SidebarMenuItem>
            </SidebarMenu>
            </SidebarGroupContent>
        </SidebarGroup>
        </SidebarContent>
    </Sidebar>
</template>