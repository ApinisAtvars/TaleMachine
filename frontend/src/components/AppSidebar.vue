<script setup lang="ts">
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarHeader,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarFooter,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuAction,
  SidebarMenu,
} from "@/components/ui/sidebar";
import Button from "@/components/ui/button/Button.vue";
import { ChartNetwork, MessageSquare } from "lucide-vue-next";

import { useStoryStore } from "@/stores/storyStore";
import { storeToRefs } from "pinia";

const storyStore = useStoryStore();


</script>

<template>
    <Sidebar>
        <SidebarHeader class="p-2">
            <h2 class="text-lg font-bold flex justify-center">TaleMachine</h2>
        </SidebarHeader>
        <SidebarContent>
        <SidebarGroup>
            <SidebarGroupContent>
            <SidebarMenu>
            </SidebarMenu>
            </SidebarGroupContent>
        </SidebarGroup>
        </SidebarContent>
    </Sidebar>
</template>