import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home/home.component';
import { ConversationsComponent } from './pages/conversations/conversations.component';
import { ConversationDetailComponent } from './pages/conversation-detail/conversation-detail.component';
import { AboutComponent } from './pages/about/about.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'conversations', component: ConversationsComponent },
  { path: 'conversations/:id', component: ConversationDetailComponent },
  { path: 'about', component: AboutComponent },
  { path: 'search', redirectTo: 'conversations' },
  { path: '**', redirectTo: '' }
];
