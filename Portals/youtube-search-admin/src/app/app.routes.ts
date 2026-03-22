import { Routes } from '@angular/router';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { BuildModelComponent } from './pages/build-model/build-model.component';
import { BuildQueueComponent } from './pages/build-queue/build-queue.component';
import { SettingsComponent } from './pages/settings/settings.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'build', component: BuildModelComponent },
  { path: 'queue', component: BuildQueueComponent },
  { path: 'settings', component: SettingsComponent },
  { path: '**', redirectTo: '' }
];
