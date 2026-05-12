export interface TrainingData {
  id: number;
  date?: string | null;
  price: number;
  bedrooms: number;
  bathrooms: number;
  sqft_living: number;
  sqft_lot: number;
  floors: number;
  waterfront: boolean;
  view: number;
  condition: number;
  grade: number;
  sqft_above: number;
  sqft_basement: number;
  yr_built: number;
  yr_renovated: number;
  zipcode: number;
  lat: number;
  long: number;
  sqft_living15: number;
  sqft_lot15: number;
}