import { Component } from '@angular/core';


@Component({
  selector: "ilustration-panel",
  template: `<div class="overflow-hidden bg-blue-600 w-full h-full">
    <img
      src="https://images.unsplash.com/photo-1768295984870-69c68c4cb938?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBjaXR5JTIwcmVhbCUyMGVzdGF0ZSUyMGFlcmlhbHxlbnwxfHx8fDE3NzMyMTc4Mjd8MA&ixlib=rb-4.1.0&q=80&w=1080"
      alt="City aerial view"
      class="w-full h-full object-cover opacity-30"
    />
    <div class="absolute inset-0 flex flex-col justify-center p-16">
      <div class="mb-8">
        <div class="w-14 h-14 rounded-2xl bg-white/20 flex items-center justify-center mb-6">
          <i class="pi pi-microchip-ai text-white" style="font-size: 1.75rem"></i>
        </div>
        <h2 class="text-white mb-4">AI-Powered House Price Prediction</h2>
        <p class="text-blue-100 text-sm leading-relaxed max-w-sm">
          Leverage advanced machine learning models to accurately predict property values with detailed explanations and confidence scores.
        </p>
      </div>

      <!-- Feature List -->
      <div class="space-y-4">
        @for (feat of features; track feat) {
          <div class="flex items-center gap-3">
            <div class="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center shrink-0">
              <div class="w-2 h-2 rounded-full bg-white"></div>
            </div>
            <span class="text-white text-sm">{{ feat }}</span>
          </div>
        }
      </div>

      <div class="mt-10 grid grid-cols-3 gap-4">
        @for (stat of stats; track stat.label) {
          <div class="bg-white/10 rounded-xl p-4 text-center">
            <p class="text-white font-bold">{{ stat.value }}</p>
            <p class="text-blue-200 text-xs mt-0.5">{{ stat.label }}</p>
          </div>
        }
      </div>
    </div>
  </div>`
})

export class ILustrationPanel {

  protected readonly features = [
    'Natural language AI explanations',
    '94%+ prediction accuracy',
    'Multi-factor analysis',
    'Real-time market insights',
  ];

  protected readonly stats = [
    { value: '1,284', label: 'Active Users' },
    { value: '8,492', label: 'Predictions' },
    { value: '94.2%', label: 'Accuracy' },
  ];
}
