import axios from 'axios';

import { config } from '../../../../core/config';

type HealthResponse = {
  status?: string;
  message?: string;
};

export class HealthRepository {
  async ping(): Promise<string> {
    const response = await axios.get<HealthResponse>(`${config.apiBaseUrl}/health`);

    return response.data.status ?? response.data.message ?? 'ok';
  }
}