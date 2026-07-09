import type { AxiosInstance } from "axios";

export class HealthRepository {
  private http: AxiosInstance;

  constructor(http: AxiosInstance) {
    this.http = http;
  }

  async ping(): Promise<string> {
    const { data } = await this.http.get("/ping");
    return data.message;
  }
}
