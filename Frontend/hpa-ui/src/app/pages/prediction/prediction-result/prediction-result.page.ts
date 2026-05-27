import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { DecimalPipe, NgClass } from '@angular/common';
import { PredictionService } from '../services/prediction.service';
import { AiTipsResponse, Prediction } from '../models/Prediction';

const CATEGORY_CONFIG: Record<string, { emoji: string; badge: string; bg: string }> = {
  'Kitchen':    { emoji: '🍳', badge: 'bg-amber-100 text-amber-800',   bg: 'bg-amber-50' },
  'Bathroom':   { emoji: '🚿', badge: 'bg-blue-100 text-blue-800',     bg: 'bg-blue-50' },
  'Flooring':   { emoji: '🪵', badge: 'bg-stone-100 text-stone-800',   bg: 'bg-stone-50' },
  'Smart Home': { emoji: '💡', badge: 'bg-purple-100 text-purple-800', bg: 'bg-purple-50' },
  'Exterior':   { emoji: '🏠', badge: 'bg-green-100 text-green-800',   bg: 'bg-green-50' },
  'Garden':     { emoji: '🌿', badge: 'bg-emerald-100 text-emerald-800', bg: 'bg-emerald-50' },
  'Lighting':   { emoji: '🔆', badge: 'bg-yellow-100 text-yellow-800', bg: 'bg-yellow-50' },
  'Insulation': { emoji: '🧱', badge: 'bg-gray-100 text-gray-700',     bg: 'bg-gray-50' },
  'Parking':    { emoji: '🚗', badge: 'bg-slate-100 text-slate-800',   bg: 'bg-slate-50' },
};

const DEFAULT_CAT = { emoji: '✨', badge: 'bg-indigo-100 text-indigo-800', bg: 'bg-indigo-50' };

@Component({
  templateUrl: 'prediction-result.page.html',
  imports: [NgClass, RouterModule, DecimalPipe],
})
export class PredictionResultPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly predictionService = inject(PredictionService);

  prediction = signal<Prediction | null>(null);
  loading = signal<boolean>(true);
  error = signal<string | null>(null);

  aiExplanation = signal<string | null>(null);
  aiExplanationLoading = signal<boolean>(false);
  aiExplanationError = signal<string | null>(null);

  aiTips = signal<AiTipsResponse | null>(null);
  aiTipsLoading = signal<boolean>(false);
  aiTipsError = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    const stateData = (history.state as { prediction?: Prediction })?.prediction;

    if (stateData) {
      this.prediction.set(stateData);
      this.loading.set(false);
      return;
    }

    const id = this.route.snapshot.paramMap.get('id');
    if (!id) {
      await this.router.navigate(['/dashboard/predict']);
      return;
    }

    try {
      const data = await this.predictionService.getById(id);
      this.prediction.set(data);
    } catch {
      this.error.set('Nu am putut încărca predicția. Vă rugăm să încercați din nou.');
    } finally {
      this.loading.set(false);
    }
  }

  async generateAIExplanation(): Promise<void> {
    const id = this.prediction()?.id;
    if (!id) return;
    this.aiExplanationLoading.set(true);
    this.aiExplanationError.set(null);
    try {
      const result = await this.predictionService.generateAIExplanation(id);
      this.aiExplanation.set(result.explanation);
    } catch {
      this.aiExplanationError.set('Could not generate AI explanation. Please try again.');
    } finally {
      this.aiExplanationLoading.set(false);
    }
  }

  async generateAITips(): Promise<void> {
    const id = this.prediction()?.id;
    if (!id) return;
    this.aiTipsLoading.set(true);
    this.aiTipsError.set(null);
    try {
      const result = await this.predictionService.generateAITips(id);
      this.aiTips.set(result);
    } catch {
      this.aiTipsError.set('Could not generate AI tips. Please try again.');
    } finally {
      this.aiTipsLoading.set(false);
    }
  }

  categoryConfig(cat: string) {
    return CATEGORY_CONFIG[cat] ?? DEFAULT_CAT;
  }

  get priceFactor(): { label: string; value: number }[] {
    const p = this.prediction();
    if (!p?.price_factors) return [];
    return (Object.entries(p.price_factors) as [string, number][])
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 6);
  }

  get maxFactor(): number {
    return this.priceFactor[0]?.value ?? 1;
  }

  confidenceLabel(conf: number): string {
    if (conf >= 0.9) return 'Very High';
    if (conf >= 0.75) return 'High';
    if (conf >= 0.6) return 'Moderate';
    return 'Low';
  }

  confidenceColor(conf: number): string {
    if (conf >= 0.9) return 'text-green-600';
    if (conf >= 0.75) return 'text-blue-600';
    if (conf >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  }
}
