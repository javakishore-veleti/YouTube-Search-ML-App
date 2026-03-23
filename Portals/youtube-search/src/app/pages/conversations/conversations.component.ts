import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ConversationService, Conversation } from '../../services/conversation.service';
import { ModelService, ModelInfo } from '../../services/model.service';

@Component({
  selector: 'app-conversations',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './conversations.component.html',
  styleUrl: './conversations.component.scss'
})
export class ConversationsComponent implements OnInit {
  conversations: Conversation[] = [];
  models: ModelInfo[] = [];
  loaded = false;
  error = '';

  // new conversation form
  showNewForm = false;
  newName = '';
  newModelId: number | null = null;

  constructor(
    private svc: ConversationService,
    private modelSvc: ModelService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadAll();
  }

  loadAll(): void {
    this.modelSvc.getModels().subscribe({
      next: (models) => {
        this.models = models;
        this.cdr.detectChanges();
      }
    });
    this.svc.list().subscribe({
      next: (list) => {
        this.conversations = list;
        this.loaded = true;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Failed to load conversations.';
        this.loaded = true;
        this.cdr.detectChanges();
      }
    });
  }

  openConversation(c: Conversation): void {
    this.router.navigate(['/conversations', c.id]);
  }

  activate(c: Conversation, event: Event): void {
    event.stopPropagation();
    if (c.is_active) return;
    this.svc.activate(c.id).subscribe(() => this.loadAll());
  }

  deleteConversation(c: Conversation, event: Event): void {
    event.stopPropagation();
    this.svc.delete(c.id).subscribe(() => this.loadAll());
  }

  toggleNewForm(): void {
    this.showNewForm = !this.showNewForm;
    if (this.showNewForm && this.models.length && !this.newModelId) {
      this.newModelId = this.models[0].id;
    }
  }

  createConversation(): void {
    if (!this.newName.trim()) return;
    this.svc.create(this.newName.trim(), this.newModelId).subscribe({
      next: (res) => {
        this.newName = '';
        this.showNewForm = false;
        this.loadAll();
      }
    });
  }

  modelName(modelId: number | null): string {
    if (!modelId) return '—';
    const m = this.models.find(x => x.id === modelId);
    return m ? m.model_name : '#' + modelId;
  }
}
