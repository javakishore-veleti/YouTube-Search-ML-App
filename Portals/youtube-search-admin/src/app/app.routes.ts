import { Routes } from '@angular/router';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { BuildModelComponent } from './pages/build-model/build-model.component';
import { SettingsComponent } from './pages/settings/settings.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'build', component: BuildModelComponent },
  { path: 'settings', component: SettingsComponent },
  { path: '**', redirectTo: '' }
];
