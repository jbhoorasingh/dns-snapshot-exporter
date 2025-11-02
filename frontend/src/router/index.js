/**
 * Vue Router configuration
 */

import { createRouter, createWebHistory } from 'vue-router';
import Home from '../views/Home.vue';
import Zones from '../views/Zones.vue';
import ZoneDetails from '../views/ZoneDetails.vue';
import SnapshotDetails from '../views/SnapshotDetails.vue';
import Comparison from '../views/Comparison.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
  },
  {
    path: '/zones',
    name: 'Zones',
    component: Zones,
  },
  {
    path: '/zones/:id',
    name: 'ZoneDetails',
    component: ZoneDetails,
    props: true,
  },
  {
    path: '/snapshots/:id',
    name: 'SnapshotDetails',
    component: SnapshotDetails,
    props: true,
  },
  {
    path: '/compare',
    name: 'Comparison',
    component: Comparison,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
