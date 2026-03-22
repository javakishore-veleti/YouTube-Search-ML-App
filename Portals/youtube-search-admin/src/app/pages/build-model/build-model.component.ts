import { Component, OnInit, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BuilderService, VideoResult } from '../../services/builder.service';

@Component({
  selector: 'app-build-model',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './build-model.component.html',
  styleUrl: './build-model.component.scss'
})
export class BuildModelComponent implements OnInit {
  // Step tracking: 1=config, 2=search & select videos, 3=confirm & build
  currentStep = 1;

  // Step 1: config
  approaches: any[] = [];
  selectedApproach = '';
  selectedSubModels: string[] = [];
  modelName = '';
  apiKeyConfigured = false;
  apiKeyMessage = '';
  apiKeyLoaded = false;

  // Step 2: video search & selection
  searchQuery = '';
  allVideos: VideoResult[] = [];
  isSearching = false;
  searchError = '';

  // Optional filters
  showFilters = false;
  publishedAfter = '';    // YYYY-MM-DD
  publishedBefore = '';   // YYYY-MM-DD
  channelLink = '';       // full YouTube channel URL or channel ID
  searchTags = '';        // comma-separated tags

  // Pagination
  currentPage = 1;
  pageSize = 10;

  // Selection (persisted across pages by video_id)
  selectedVideoIds: Set<string> = new Set();
  readonly maxSelections = 25;

  // Step 3: build
  publishAsLatest = false;
  isBuilding = false;
  buildResult: string | null = null;
  additionalNotes = '';
  additionalContextData = '';

  constructor(
    private builderService: BuilderService,
    private cdr: ChangeDetectorRef,
    private zone: NgZone
  ) {}

  ngOnInit(): void {
    console.log('[BuildModel] ngOnInit');
    this.builderService.getAppStatus().subscribe({
      next: (s) => {
        console.log('[BuildModel] getAppStatus received', s.api_key_configured);
        this.apiKeyConfigured = s.api_key_configured;
        this.apiKeyMessage = s.api_key_configured
          ? 'API key is configured on the server.'
          : 'API key is NOT configured. Set YOUTUBE_API_KEY in .env on the server.';
        this.apiKeyLoaded = true;
        this.cdr.detectChanges();
      },
      error: (e) => {
        console.error('[BuildModel] getAppStatus error', e);
        this.apiKeyMessage = 'Unable to reach backend.';
        this.apiKeyLoaded = true;
        this.cdr.detectChanges();
      }
    });
    this.builderService.getApproaches().subscribe({
      next: (list) => {
        console.log('[BuildModel] getApproaches received', list.length, 'items');
        this.approaches = list;
        this.cdr.detectChanges();
      },
      error: (e) => console.error('[BuildModel] getApproaches error', e)
    });
  }

  // ── Pagination helpers ──────────────────────────────────────────────

  get totalPages(): number {
    return Math.ceil(this.allVideos.length / this.pageSize);
  }

  get pagedVideos(): VideoResult[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.allVideos.slice(start, start + this.pageSize);
  }

  get pageNumbers(): number[] {
    return Array.from({ length: this.totalPages }, (_, i) => i + 1);
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
    }
  }

  // ── Selection helpers ───────────────────────────────────────────────

  isSelected(videoId: string): boolean {
    return this.selectedVideoIds.has(videoId);
  }

  toggleSelection(video: VideoResult): void {
    if (this.selectedVideoIds.has(video.video_id)) {
      this.selectedVideoIds.delete(video.video_id);
    } else if (this.selectedVideoIds.size < this.maxSelections) {
      this.selectedVideoIds.add(video.video_id);
    }
  }

  get selectedVideos(): VideoResult[] {
    return this.allVideos.filter(v => this.selectedVideoIds.has(v.video_id));
  }

  get selectionCount(): number {
    return this.selectedVideoIds.size;
  }

  // ── Step navigation ─────────────────────────────────────────────────

  goToStep2(): void {
    if (this.canProceedFromStep1()) {
      this.currentStep = 2;
    }
  }

  goToStep3(): void {
    if (this.selectionCount > 0) {
      this.currentStep = 3;
    }
  }

  goBack(step: number): void {
    this.currentStep = step;
  }

  // ── Search ──────────────────────────────────────────────────────────

  onSearch(): void {
    if (!this.searchQuery.trim()) return;
    this.isSearching = true;
    this.searchError = '';
    this.currentPage = 1;

    const channelId = this.extractChannelId(this.channelLink);
    console.log('[BuildModel] searching:', this.searchQuery);

    this.builderService.searchVideos(this.searchQuery, 50, {
      publishedAfter: this.publishedAfter || undefined,
      publishedBefore: this.publishedBefore || undefined,
      channelId: channelId || undefined,
      tags: this.searchTags || undefined
    }).subscribe({
      next: (res) => {
        this.zone.run(() => {
          console.log('[BuildModel] search done:', res.total, 'results, updating UI');
          this.allVideos = res.videos;
          this.isSearching = false;
          if (res.error) this.searchError = res.error;
          this.cdr.detectChanges();
          console.log('[BuildModel] UI updated. isSearching=', this.isSearching, 'allVideos.length=', this.allVideos.length);
        });
      },
      error: (err) => {
        this.zone.run(() => {
          console.error('[BuildModel] search error', err);
          this.searchError = 'Search failed. Check backend.';
          this.isSearching = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  toggleFilters(): void {
    this.showFilters = !this.showFilters;
  }

  private extractChannelId(link: string): string {
    if (!link) return '';
    // Handle full URLs: youtube.com/channel/UCxxxx or youtube.com/@handle
    const channelMatch = link.match(/\/channel\/([\w-]+)/);
    if (channelMatch) return channelMatch[1];
    // If it looks like a raw channel ID (starts with UC), use as-is
    if (link.startsWith('UC')) return link.trim();
    // Otherwise return empty — can't extract
    return '';
  }

  // ── Build ───────────────────────────────────────────────────────────

  onBuild(): void {
    this.isBuilding = true;
    this.buildResult = null;

    this.builderService.submitToQueue({
      model_name: this.modelName.trim(),
      approach_type: this.selectedApproach,
      publish_as_latest: this.publishAsLatest,
      selected_videos: this.selectedVideos,
      notes: this.additionalNotes.trim(),
      context_data: this.additionalContextData.trim() || '{}',
      selected_sub_models: this.selectedSubModels
    }).subscribe({
      next: (res) => {
        this.zone.run(() => {
          if (res.status === 'queued') {
            this.buildResult = `Queued as #${res.queue_item?.id}. The scheduler will process it shortly.`;
          } else {
            this.buildResult = res.message || 'Submitted.';
          }
          this.isBuilding = false;
          this.cdr.detectChanges();
        });
      },
      error: () => {
        this.zone.run(() => {
          this.buildResult = 'Failed to submit to queue. Check backend logs.';
          this.isBuilding = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  get selectedApproachConfig(): any | null {
    return this.approaches.find(a => a.id === this.selectedApproach) || null;
  }

  get subModelConfig(): any | null {
    return this.selectedApproachConfig?.sub_models || null;
  }

  get subModelOptions(): any[] {
    return this.subModelConfig?.options || [];
  }

  get isMultiSubModel(): boolean {
    return this.subModelConfig?.selection_mode === 'multiple';
  }

  onApproachChange(): void {
    this.selectedSubModels = [];
  }

  toggleSubModel(optionId: string): void {
    if (!this.isMultiSubModel) {
      this.selectedSubModels = optionId ? [optionId] : [];
      return;
    }
    if (this.selectedSubModels.includes(optionId)) {
      this.selectedSubModels = this.selectedSubModels.filter(v => v !== optionId);
    } else {
      this.selectedSubModels = [...this.selectedSubModels, optionId];
    }
  }

  isSubModelSelected(optionId: string): boolean {
    return this.selectedSubModels.includes(optionId);
  }

  canProceedFromStep1(): boolean {
    if (!this.modelName.trim() || !this.selectedApproach || !this.apiKeyConfigured) return false;
    if (!this.subModelConfig) return true;
    return this.selectedSubModels.length > 0;
  }
}
