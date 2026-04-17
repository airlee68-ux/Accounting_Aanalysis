<script setup>
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, ArcElement } from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, ArcElement)

defineProps({
  data: { type: Object, required: true },
  options: { type: Object, default: () => ({ responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right' } } }) },
})
</script>

<template>
  <div class="relative h-64">
    <Doughnut :data="data" :options="options" />
  </div>
</template>
