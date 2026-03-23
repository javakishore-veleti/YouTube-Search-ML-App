import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { ConversationService, Conversation } from '../../services/conversation.service';
import { ModelService, ModelInfo } from '../../services/model.service';
import { environment } from '../../environments/environment';

interface SettingFieldOption { value: string; label: string; }
interface SettingField {
  key: string; label: string; type: string; default?: any;
  options?: SettingFieldOption[]; min?: number; max?: number; step?: number; description?: string;
}
interface Approach {
  id: string; name: string; category?: string; description?: string;
  conversation_settings?: { fields: SettingField[] };
}

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
  approaches: Approach[] = [];
  loaded = false;
  error = '';

  // new conversation form
  showNewForm = false;
  newName = '';
  newModelId: number | null = null;
  newSettingsForm: Record<string, any> = {};

  constructor(
    private svc: ConversationService,
    private modelSvc: ModelService,
    private http: HttpClient,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.http.get<Approach[]>(`${environment.apiBaseUrl}/admin/approaches`).subscribe(a => {
      this.approaches = a; this.cdr.detectChanges();
    });
    this.loadAll();
  }

  loadAll(): void {
    this.modelSvc.getModels().subscribe({
      next: (models) => { this.models = models; this.cdr.detectChanges(); }
    });
    this.svc.list().subscribe({
      next: (list) => { this.conversations = list; this.loaded = true; this.cdr.detectChanges(); },
      error: () => { this.error = 'Failed to load conversations.'; this.loaded = true; this.cdr.detectChanges(); }
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
      this.rebuildNewSettings();
    }
  }

  onNewModelChange(): void {
    this.rebuildNewSettings();
  }

  // resolve approach for the selected model in the create form
  get newApproach(): Approach | null {
    if (!this.newModelId) return null;
    const m = this.models.find(x => x.id === this.newModelId);
    if (!m) return null;
    return this.approaches.find(a => a.id === m.model_approach_type) ?? null;
  }

  get newSettingsFields(): SettingField[] {
    return this.newApproach?.conversation_settings?.fields ?? [];
  }

  rebuildNewSettings(): void {
    this.newSettingsForm = {};
    for (const f of this.newSettingsFields) {
      this.newSettingsForm[f.key] = f.default ?? '';
    }
  }

  createConversation(): void {
    if (!this.newName.trim()) return;
    this.svc.create(this.newName.trim(), this.newModelId).subscribe({
      next: (res) => {
        const convId = res.conversation?.id;
        // save settings if any fields were configured
        if (convId && this.newSettingsFields.length > 0) {
          this.svc.update(convId, undefined, undefined, this.newSettingsForm).subscribe(() => {
            this.resetForm();
            this.loadAll();
          });
        } else {
          this.resetForm();
          this.loadAll();
        }
      }
    });
  }

  private resetForm(): void {
    this.newName = '';
    this.newModelId = null;
    this.newSettingsForm = {};
    this.showNewForm = false;
  }

  modelName(modelId: number | null): string {
    if (!modelId) return '—';
    const m = this.models.find(x => x.id === modelId);
    return m ? m.model_name : '#' + modelId;
  }

  // resolve approach for a conversation card to show settings summary
  convApproach(c: Conversation): Approach | null {
    if (!c.model_id) return null;
    const m = this.models.find(x => x.id === c.model_id);
    if (!m) return null;
    return this.approaches.find(a => a.id === m.model_approach_type) ?? null;
  }

  settingLabel(approach: Approach, key: string, value: any): string {
    const field = approach.conversation_settings?.fields?.find(f => f.key === key);
    if (!field) return String(value);
    if (field.options) {
      const opt = field.options.find(o => o.value === value);
      return opt ? opt.label : String(value);
    }
    return String(value);
  }

  settingEntries(c: Conversation): { key: string; label: string; value: string }[] {
    const s = c.settings;
    if (!s || typeof s !== 'object') return [];
    const approach = this.convApproach(c);
    if (!approach) return [];
    return Object.entries(s).map(([k, v]) => {
      const field = approach.conversation_settings?.fields?.find(f => f.key === k);
      const label = field?.label ?? k;
      let displayValue = String(v);
      if (field?.options) {
        const opt = field.options.find(o => o.value === v);
        if (opt) displayValue = opt.label;
      }
      return { key: k, label, value: displayValue };
    });
  }

  toggleMultiSelect(key: string, value: string): void {
    const arr: string[] = this.newSettingsForm[key] || [];
    const idx = arr.indexOf(value);
    if (idx >= 0) arr.splice(idx, 1); else arr.push(value);
    this.newSettingsForm[key] = [...arr];
  }
}
