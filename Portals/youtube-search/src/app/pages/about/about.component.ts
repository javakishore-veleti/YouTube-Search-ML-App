import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { AppInfoService, AppInfo } from '../../services/app-info.service';
import { environment } from '../../environments/environment';

interface TechTopic {
  id: string;
  title: string;
  icon: string;
  summary: string;
  expanded: boolean;
}

interface Approach {
  id: string;
  name: string;
  category?: string;
  description?: string;
  notes?: string;
}

interface ApproachDetail {
  overview: string;
  topics: TechTopic[];
}

@Component({
  selector: 'app-about',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './about.component.html',
  styleUrl: './about.component.scss'
})
export class AboutComponent implements OnInit {
  appInfo: AppInfo | null = null;
  approaches: Approach[] = [];
  selectedApproachId = '';
  currentApproach: Approach | null = null;

  // approach-specific content
  private approachContent: Record<string, ApproachDetail> = {
    'e1cffc4f-d00d-4b04-b705-18eef34e10d2': {
      overview: 'This approach builds a custom video search index from YouTube video transcripts using a pre-trained SentenceTransformer model. It converts video content into mathematical vectors (embeddings) and uses distance metrics to find the most relevant videos for your query.',
      topics: [
        {
          id: 'how-it-works', title: 'How This Approach Works (Step by Step)', icon: 'bi-diagram-3',
          summary: 'When you build a model with Approach 01, here is what happens behind the scenes:\n\n1. Your selected YouTube videos\' transcripts and descriptions are fetched.\n2. The text is cleaned — special characters removed, stopwords filtered out.\n3. A pre-trained SentenceTransformer model (e.g. all-MiniLM-L12-v2, trained on billions of internet sentences) is downloaded from HuggingFace.\n4. That pre-trained model encodes each video\'s cleaned text into a 384-dimensional vector (an "embedding"). These embeddings are saved as your video index.\n5. The same pre-trained model is saved to disk as "your model".\n\nWhen you search, your query is encoded using the same model into a 384-dim vector, and the system measures the distance between your query vector and each video vector. The closest videos are returned as results.\n\nCritically: the pre-trained model is NOT fine-tuned or retrained on your videos. Your videos define the search INDEX (what to search against), but the model\'s language understanding comes entirely from its original pre-training.',
          expanded: false,
        },
        {
          id: 'what-custom-means', title: 'What "Custom Model" Really Means', icon: 'bi-lightbulb',
          summary: 'The term "custom model" can be misleading. In this approach, you are NOT training a new AI model from scratch or teaching it new words. Instead, you are:\n\n- Using a universal language model that already understands virtually every word and concept in every language.\n- Building a custom INDEX — a collection of pre-computed embeddings for your specific set of videos.\n- The "custom" part is WHICH videos you chose to index, not HOW the model understands language.\n\nThink of it like a library: the model is the librarian who can read and understand any book. Your "custom model" is the specific collection of books you put on the shelves. The librarian\'s reading ability doesn\'t change — only which books are available to search through.\n\nThis means if you search for "Kishore" (a name) against a model built from AI engineering videos, the model DOES understand what "Kishore" means — it just won\'t find it in your video index because none of your videos are about that topic. The search correctly returns no results, not because the word is unknown, but because it\'s semantically distant from your indexed content.',
          expanded: false,
        },
        {
          id: 'limitations', title: 'Limitations of This Approach', icon: 'bi-exclamation-triangle',
          summary: 'Understanding these limitations helps you use this approach effectively:\n\n1. No fine-tuning: The model\'s understanding is frozen from pre-training. It cannot learn domain-specific jargon, acronyms, or meanings unique to your video collection. If your videos use specialised terminology that the base model wasn\'t trained on, search quality may suffer.\n\n2. No "unknown word" concept: Every possible query — even complete gibberish — produces a valid embedding vector with a finite distance to your videos. The system relies entirely on the distance threshold to filter irrelevant queries. There is no way to return "word not found".\n\n3. Small index = narrow distance bands: With only 2-5 videos, the distance between relevant and irrelevant queries may be very small (e.g. 14 vs 21 on a scale of 0-200). This makes threshold calibration critical. The system uses an adaptive threshold (1.5x the mean inter-video distance) to handle this, but adding more videos improves discrimination.\n\n4. Transcript quality matters: If a video has no transcript or a poor auto-generated one, its embedding will be low quality. Garbage in = garbage out.\n\n5. One embedding per video: Each video gets a single vector representing ALL its content. A 2-hour video about 10 different topics gets averaged into one embedding, which may not match narrow queries about any single topic.\n\n6. No context or conversation memory: Each query is independent. The system doesn\'t learn from your previous searches or build understanding of your interests over time.\n\nFor use cases that need these capabilities, consider approaches that include actual model fine-tuning (Approach 02/03) or LLM-based semantic understanding (Approach 05).',
          expanded: false,
        },
        {
          id: 'feature-extraction', title: 'Feature Extraction', icon: 'bi-funnel',
          summary: 'The foundation of this approach. Each video\'s transcript and description are converted into a dense vector (a list of 384 or 768 numbers) using a SentenceTransformer model. These vectors — called embeddings — capture the semantic meaning of the text. When you search, your query is converted into the same kind of vector so it can be compared directly against all video vectors. This is what makes the search understand meaning rather than just keywords.',
          expanded: false,
        },
        {
          id: 'sentence-similarity', title: 'Sentence Similarity', icon: 'bi-arrows-angle-contract',
          summary: 'Once your query and all video transcripts have been converted to embeddings, sentence similarity is how the system decides which videos match. It computes the distance between your query vector and each video vector — the closer the vectors, the more similar the meaning. For example, searching "how to cook pasta" will match a video about "making Italian noodles at home" because their embeddings are close together even though they share no words.',
          expanded: false,
        },
        {
          id: 'distance-metrics', title: 'Distance Metrics Overview', icon: 'bi-rulers',
          summary: 'This approach lets you choose how similarity is measured between your query and video embeddings. Each metric calculates "distance" differently — lower distance means a closer, more relevant match. The choice of metric can significantly affect which results appear and in what order. Below are the individual metrics available, each suited to different search scenarios.',
          expanded: false,
        },
        {
          id: 'manhattan-distance', title: 'Manhattan Distance (City Block)', icon: 'bi-signpost-split',
          summary: 'The default metric. Measures distance by summing the absolute differences along every dimension — like counting how many city blocks you\'d walk to get from point A to point B. In a 384-dimensional embedding space, it adds up 384 individual differences. Manhattan distance is robust for high-dimensional data because it doesn\'t let a single large difference dominate the result. Best for: general-purpose searches where you want balanced, reliable matching across all aspects of meaning. Example: searching "Python web development" will match videos about Flask, Django, and web APIs roughly equally.',
          expanded: false,
        },
        {
          id: 'euclidean-distance', title: 'Euclidean Distance (Straight Line)', icon: 'bi-arrow-up-right',
          summary: 'Measures the straight-line ("as the crow flies") distance between two points in embedding space. It squares each dimension\'s difference before summing, which means larger individual differences are penalised more heavily than Manhattan. This makes it more sensitive to outlier dimensions. Best for: precise topic matching where you want results that are closely aligned across all dimensions of meaning. Example: searching "convolutional neural networks for image classification" will strongly favour videos specifically about CNNs over general deep learning content.',
          expanded: false,
        },
        {
          id: 'chebyshev-distance', title: 'Chebyshev Distance (Maximum Difference)', icon: 'bi-arrows-fullscreen',
          summary: 'Only considers the single largest difference across all dimensions — the "worst case" dimension. If two embeddings agree on 383 out of 384 dimensions but wildly disagree on one, Chebyshev will flag that. Best for: searches where you need at least some relevance across every aspect of the topic. A video must be reasonably close on ALL dimensions to score well. Example: searching "beginner Python data science tutorial" requires the result to match on all three aspects (beginner level, Python, data science) — not just one.',
          expanded: false,
        },
        {
          id: 'minkowski-distance', title: 'Minkowski Distance (Generalised)', icon: 'bi-sliders2',
          summary: 'A flexible family of distance metrics parameterised by a value p. When p=1 it behaves exactly like Manhattan, when p=2 it becomes Euclidean, and as p approaches infinity it becomes Chebyshev. This lets you fine-tune the balance between penalising many small differences (low p) versus penalising a few large differences (high p). Best for: advanced experimentation when you want to explore the spectrum between Manhattan and Euclidean behaviour to find the sweet spot for your specific video collection.',
          expanded: false,
        },
        {
          id: 'seuclidean-distance', title: 'Standardised Euclidean Distance', icon: 'bi-distribute-vertical',
          summary: 'Like Euclidean distance but each dimension is scaled by its variance across the dataset. Dimensions where embeddings vary a lot are weighted less, and dimensions where they\'re tightly clustered are weighted more. This normalisation prevents high-variance dimensions from dominating the distance. Best for: video collections where certain semantic dimensions have much wider spread than others. Example: if your videos span many topics but are similar in tone, Standardised Euclidean will focus more on tonal differences to find nuanced matches.',
          expanded: false,
        },
        {
          id: 'canberra-distance', title: 'Canberra Distance', icon: 'bi-bullseye',
          summary: 'Measures the sum of fractional differences: each dimension\'s absolute difference is divided by the sum of the absolute values. This makes it extremely sensitive to differences when both values are near zero. Small differences in small values count as much as large differences in large values. Best for: niche or very specific searches where subtle distinctions matter. Example: searching "quantum computing error correction" in a collection of physics videos — Canberra will pick up fine-grained topical differences that broader metrics might miss.',
          expanded: false,
        },
        {
          id: 'braycurtis-distance', title: 'Bray-Curtis Distance', icon: 'bi-pie-chart',
          summary: 'Calculates the sum of absolute differences divided by the sum of absolute values across all dimensions. Originally from ecology for comparing species compositions, it measures proportional dissimilarity. Two embeddings that emphasise the same dimensions in the same proportions score as similar, even if their absolute magnitudes differ. Best for: comparing the relative emphasis or "flavour" of content rather than exact topic matching. Example: two videos about "machine learning" — one enthusiastic and one academic — will still match well because they discuss the same proportions of sub-topics.',
          expanded: false,
        },
        {
          id: 'hamming-distance', title: 'Hamming Distance', icon: 'bi-grid-3x3',
          summary: 'Counts the proportion of dimensions where the two vectors differ. Originally designed for binary data (0s and 1s), it treats each dimension as either matching or not matching, ignoring the magnitude of difference. For continuous embeddings, it counts dimensions where values differ by any amount. Best for: binary or categorical feature comparisons. Less suited for nuanced sentence embeddings but useful when you\'ve binarised your features or want a rough "how many aspects differ" count. Example: comparing tag-based video features (has subtitles? is tutorial? is live stream?).',
          expanded: false,
        },
        {
          id: 'text-ranking', title: 'Text Ranking', icon: 'bi-sort-numeric-down',
          summary: 'After computing distances between your query and all video embeddings, results are ranked from closest (most relevant) to farthest. A configurable threshold filters out videos that are too distant to be useful, and a top-k limit keeps only the best matches. This ensures you see a focused, high-quality set of results rather than everything that vaguely relates to your query.',
          expanded: false,
        },
        {
          id: 'token-classification', title: 'Token Classification', icon: 'bi-tags',
          summary: 'During the data preparation phase, video transcripts go through text cleaning that identifies and removes stopwords (common words like "the", "is", "and" that carry no meaning). This is a form of token-level processing that helps the embedding model focus on the important, content-bearing words. Better input text leads to more meaningful embeddings and more accurate search results.',
          expanded: false,
        },
        {
          id: 'zero-shot-classification', title: 'Zero-Shot Classification', icon: 'bi-lightning-charge',
          summary: 'The SentenceTransformer base models (like all-MiniLM-L12-v2) are pre-trained on massive text datasets, giving them broad understanding across all topics. This means your custom model can handle queries about subjects that weren\'t in your training videos. If you build a model from cooking videos but ask about "knife sharpening techniques", the model can still find relevant results because the base model already understands the semantic relationship.',
          expanded: false,
        },
        {
          id: 'tabular-classification', title: 'Tabular Data Processing', icon: 'bi-table',
          summary: 'Video metadata (IDs, descriptions, transcripts) is structured as a tabular DataFrame during the build pipeline. This tabular processing allows efficient batch operations — cleaning text, generating embeddings, and storing results as optimised Parquet files. The columnar Parquet format enables fast reads at query time, which is critical when scanning through hundreds or thousands of video records to find matches.',
          expanded: false,
        },
      ]
    }
  };

  // default content for approaches without specific details
  private defaultDetail: ApproachDetail = {
    overview: 'This approach is under development. Detailed documentation will be available once the implementation is complete.',
    topics: []
  };

  constructor(
    private appInfoService: AppInfoService,
    private http: HttpClient,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.appInfoService.getInfo().subscribe({
      next: (data: AppInfo) => { this.appInfo = data; this.cdr.detectChanges(); },
      error: () => { this.appInfo = { name: 'VidSage', description: 'Unable to fetch info from backend.' }; this.cdr.detectChanges(); }
    });
    this.http.get<Approach[]>(`${environment.apiBaseUrl}/admin/approaches`).subscribe({
      next: (a) => {
        this.approaches = a;
        if (a.length) {
          this.selectedApproachId = a[0].id;
          this.currentApproach = a[0];
        }
        this.cdr.detectChanges();
      },
      error: () => { this.approaches = []; this.cdr.detectChanges(); }
    });
  }

  onApproachChange(): void {
    this.currentApproach = this.approaches.find(a => a.id === this.selectedApproachId) ?? null;
  }

  get detail(): ApproachDetail {
    return this.approachContent[this.selectedApproachId] ?? this.defaultDetail;
  }

  get topics(): TechTopic[] {
    return this.detail.topics;
  }

  toggle(topic: TechTopic): void {
    topic.expanded = !topic.expanded;
  }

  scrollTo(id: string): void {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}
