import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppInfoService } from '../../services/app-info.service';
import type { AppInfo } from '../../services/app-info.service';

interface TechTopic {
  id: string;
  title: string;
  icon: string;
  summary: string;
  expanded: boolean;
}

@Component({
  selector: 'app-about',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './about.component.html',
  styleUrl: './about.component.scss'
})
export class AboutComponent implements OnInit {
  appInfo: AppInfo | null = null;

  topics: TechTopic[] = [
    {
      id: 'sentence-similarity',
      title: 'Sentence Similarity',
      icon: 'bi-arrows-angle-contract',
      summary: 'Compares two pieces of text and tells you how closely related they are in meaning. When you search for "how to bake bread", it finds videos about baking bread even if they use different words like "making homemade loaves". This is the core of how VidSage understands your intent rather than just matching keywords.',
      expanded: false,
    },
    {
      id: 'feature-extraction',
      title: 'Feature Extraction',
      icon: 'bi-funnel',
      summary: 'Converts your text into a list of numbers (called an "embedding") that captures its meaning. Think of it like creating a fingerprint for every sentence — similar sentences get similar fingerprints. VidSage uses this behind the scenes to represent video content and your queries so they can be compared quickly.',
      expanded: false,
    },
    {
      id: 'token-classification',
      title: 'Token Classification',
      icon: 'bi-tags',
      summary: 'Reads through text and labels each word with a category — for example, identifying people, places, topics, or technical terms. This helps VidSage understand what a video is specifically about, so searching for "Python tutorial by Corey Schafer" correctly distinguishes the language from the person.',
      expanded: false,
    },
    {
      id: 'text-ranking',
      title: 'Text Ranking',
      icon: 'bi-sort-numeric-down',
      summary: 'After finding videos that match your query, this decides the order in which to show them. It scores each result by how relevant it is to what you actually meant, putting the most helpful videos at the top — similar to how a librarian would pick the best book for your question, not just any book that mentions the topic.',
      expanded: false,
    },
    {
      id: 'zero-shot-classification',
      title: 'Zero-Shot Classification',
      icon: 'bi-lightning-charge',
      summary: 'Categorises content into topics it has never been explicitly trained on. For example, it can decide whether a video is about "cooking", "fitness", or "programming" without ever seeing those exact labels during training. This makes VidSage flexible enough to handle any subject you throw at it.',
      expanded: false,
    },
    {
      id: 'tabular-classification',
      title: 'Tabular Classification',
      icon: 'bi-table',
      summary: 'Makes predictions from structured data like tables and spreadsheets — things like view counts, video length, upload date, and engagement metrics. VidSage uses this to factor in video quality signals alongside content relevance, helping surface videos that are not only on-topic but also well-produced and popular.',
      expanded: false,
    },
  ];

  constructor(private appInfoService: AppInfoService) {}

  ngOnInit(): void {
    this.appInfoService.getInfo().subscribe({
      next: (data: AppInfo) => this.appInfo = data,
      error: () => this.appInfo = { name: 'VidSage', description: 'Unable to fetch info from backend.' }
    });
  }

  toggle(topic: TechTopic): void {
    topic.expanded = !topic.expanded;
  }

  scrollTo(id: string): void {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}
