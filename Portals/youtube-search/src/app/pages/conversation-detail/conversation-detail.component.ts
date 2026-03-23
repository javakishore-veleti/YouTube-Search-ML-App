import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { ConversationService, Conversation, ConversationMessage } from '../../services/conversation.service';
import { ModelService, ModelInfo } from '../../services/model.service';
import { environment } from '../../environments/environment';

interface Approach {
  id: string;
  name: string;
  category?: string;
  description?: string;
}

@Component({
  selector: 'app-conversation-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './conversation-detail.component.html',
  styleUrl: './conversation-detail.component.scss'
})
export class ConversationDetailComponent implements OnInit {
  conv: Conversation | null = null;
  models: ModelInfo[] = [];
  approaches: Approach[] = [];
  loaded = false;
  error = '';
  id = 0;

  // inline name edit
  editingName = false;
  editName = '';

  // search
  query = '';
  isSearching = false;

  // chat history
  messages: ConversationMessage[] = [];
  messagesPage = 1;
  messagesTotalPages = 1;
  messagesTotal = 0;
  messagesLoading = false;
  historyExpanded = false;

  // settings accordion
  settingsExpanded = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private svc: ConversationService,
    private modelSvc: ModelService,
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.id = Number(this.route.snapshot.paramMap.get('id')) || 0;
    if (!this.id) { this.error = 'Invalid conversation ID.'; this.loaded = true; return; }

    this.modelSvc.getModels().subscribe(m => { this.models = m; this.cdr.detectChanges(); });
    this.http.get<Approach[]>(`${environment.apiBaseUrl}/admin/approaches`).subscribe(a => {
      this.approaches = a; this.cdr.detectChanges();
    });
    this.loadConv();
    this.loadMessages(1);
  }

  loadConv(): void {
    this.svc.get(this.id).subscribe({
      next: (c) => { this.conv = c; this.loaded = true; this.cdr.detectChanges(); },
      error: () => { this.error = 'Could not load conversation.'; this.loaded = true; this.cdr.detectChanges(); }
    });
  }

  loadMessages(page: number): void {
    this.messagesLoading = true;
    this.svc.getMessages(this.id, page, 25).subscribe({
      next: (res) => {
        this.messages = res.items;
        this.messagesPage = res.page;
        this.messagesTotalPages = res.total_pages;
        this.messagesTotal = res.total;
        this.messagesLoading = false;
        this.cdr.detectChanges();
      },
      error: () => { this.messagesLoading = false; this.cdr.detectChanges(); }
    });
  }

  back(): void { this.router.navigate(['/conversations']); }

  // ── Name editing ────────────────────────────────
  startEditName(): void {
    if (!this.conv) return;
    this.editName = this.conv.conversation_name;
    this.editingName = true;
  }
  saveName(): void {
    if (!this.editName.trim() || !this.conv) return;
    this.svc.update(this.id, this.editName.trim()).subscribe(() => {
      this.editingName = false;
      this.loadConv();
    });
  }
  cancelEditName(): void { this.editingName = false; }

  // ── Search + save to conversation ───────────────
  onSearch(): void {
    if (!this.query.trim() || !this.conv?.model_id) return;
    this.isSearching = true;
    const q = this.query;
    this.svc.search(this.id, q).subscribe({
      next: (res) => {
        const results = res.results || [];
        // save message with results to conversation history
        this.svc.addMessage(this.id, q, results).subscribe(() => {
          this.query = '';
          this.isSearching = false;
          this.historyExpanded = true;
          this.loadMessages(1);
          this.loadConv(); // refresh message count
        });
      },
      error: () => { this.isSearching = false; this.cdr.detectChanges(); }
    });
  }

  // ── Helpers ─────────────────────────────────────
  modelName(id: number | null): string {
    if (!id) return '—';
    const m = this.models.find(x => x.id === id);
    return m ? m.model_name : '#' + id;
  }

  selectedModel(): ModelInfo | null {
    if (!this.conv?.model_id) return null;
    return this.models.find(m => m.id === this.conv!.model_id) ?? null;
  }

  selectedApproach(): Approach | null {
    const m = this.selectedModel();
    if (!m) return null;
    return this.approaches.find(a => a.id === m.model_approach_type) ?? null;
  }

  get msgPages(): number[] {
    const t = this.messagesTotalPages, c = this.messagesPage;
    const s = Math.max(1, c - 2), e = Math.min(t, s + 4);
    const r: number[] = [];
    for (let i = s; i <= e; i++) r.push(i);
    return r;
  }

  copyText(text: string): void {
    navigator.clipboard.writeText(text);
  }
}
