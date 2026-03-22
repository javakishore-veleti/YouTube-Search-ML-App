import { Routes } from '@angular/router';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { BuildModelComponent } from './pages/build-model/build-model.component';
import { BuildQueueComponent } from './pages/build-queue/build-queue.component';
import { QueueDetailComponent } from './pages/queue-detail/queue-detail.component';
import { ModelsComponent } from './pages/models/models.component';
import { ModelDetailComponent } from './pages/model-detail/model-detail.component';
import { SettingsComponent } from './pages/settings/settings.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'build', component: BuildModelComponent },
  { path: 'queue', component: BuildQueueComponent },
  { path: 'queue/:id', component: QueueDetailComponent },
  { path: 'models', component: ModelsComponent },
  { path: 'models/:id', component: ModelDetailComponent },
  { path: 'settings', component: SettingsComponent },
  { path: '**', redirectTo: '' }
];
