export type PropertyType = 'Apartment' | 'House' | 'Villa';

export interface PredictionTip {
  category: string;
  action: string;
  cost_min: number;
  cost_max: number;
  value_added: number;
}

export interface AiTip {
  category: string;
  action: string;
  example?: string;
  resource?: string;
  cost_min: number;
  cost_max: number;
  value_added: number;
  roi_percent?: number;
}

export interface AiTipsResponse {
  total_investment_min: number;
  total_investment_max: number;
  potential_value_gain: number;
  tips: AiTip[];
}

export interface Prediction {
  id: string;
  prediction_value: number;
  location: string;
  property_type: PropertyType;
  floor_area: number;
  bedrooms: number;
  bathrooms: number;
  floor_number: number;
  year_built: number;
  has_parking: boolean;
  has_pool: boolean;
  has_balcony: boolean;
  has_elevator: boolean;
  confidence: number;
  explanation: string;
  price_factors: Record<string, number>;
  tips: PredictionTip[];
  created_at: string;
}

export interface PredictionRequest {
  location: string;
  property_type: PropertyType;
  floor_area: number;
  bedrooms: number;
  bathrooms?: number;
  year_built: number;
  floor_number?: number;
  has_parking?: boolean;
  has_pool?: boolean;
  has_balcony?: boolean;
  has_elevator?: boolean;
}
