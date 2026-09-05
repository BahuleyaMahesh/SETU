import { apiClient } from '../../shared/utils/api';

export interface NearbyHospital {
  id: string;
  name: string;
  type: string;
  address: string;
  contact_phone: string;
  latitude: number;
  longitude: number;
  distance_km: number;
}

export interface GeocodeResult {
  display_name: string;
  latitude: number;
  longitude: number;
}

export const mapsApi = {
  getAshaPatients: () => apiClient.get('/api/v1/maps/asha/patients'),
  getHospitalPatients: () => apiClient.get('/api/v1/maps/hospital/patients'),
  getNearbyHospitals: (patientId: string, limit = 5): Promise<{ patient: any; hospitals: NearbyHospital[] }> =>
    apiClient.get(`/api/v1/maps/nearby-hospitals/${patientId}`, { params: { limit } }),
  geocode: (query: string): Promise<{ results: GeocodeResult[] }> =>
    apiClient.get('/api/v1/maps/geocode', { params: { q: query } }),
};

export default mapsApi;
