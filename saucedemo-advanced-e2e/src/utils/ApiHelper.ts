import { APIRequestContext } from '@playwright/test';
import { Logger } from './Logger';

export type ApiResult<T> = { status: number; body: T };

export class ApiHelper {
  private logger: Logger;

  constructor(
    private request: APIRequestContext,
    private baseURL: string,
  ) {
    this.logger = new Logger('ApiHelper');
  }

  async get<T>(endpoint: string, headers?: Record<string, string>): Promise<ApiResult<T>> {
    this.logger.info(`GET ${endpoint}`);
    const response = await this.request.get(`${this.baseURL}${endpoint}`, { headers });
    const body = (await response.json()) as T;
    this.logger.debug(`Response ${response.status()}`, body);
    return { status: response.status(), body };
  }

  async post<T>(
    endpoint: string,
    data: unknown,
    headers?: Record<string, string>,
  ): Promise<ApiResult<T>> {
    this.logger.info(`POST ${endpoint}`);
    const response = await this.request.post(`${this.baseURL}${endpoint}`, { data, headers });
    const body = (await response.json()) as T;
    this.logger.debug(`Response ${response.status()}`, body);
    return { status: response.status(), body };
  }

  async put<T>(
    endpoint: string,
    data: unknown,
    headers?: Record<string, string>,
  ): Promise<ApiResult<T>> {
    this.logger.info(`PUT ${endpoint}`);
    const response = await this.request.put(`${this.baseURL}${endpoint}`, { data, headers });
    const body = (await response.json()) as T;
    this.logger.debug(`Response ${response.status()}`, body);
    return { status: response.status(), body };
  }

  async delete<T>(endpoint: string, headers?: Record<string, string>): Promise<ApiResult<T>> {
    this.logger.info(`DELETE ${endpoint}`);
    const response = await this.request.delete(`${this.baseURL}${endpoint}`, { headers });
    const body = (await response.json()) as T;
    this.logger.debug(`Response ${response.status()}`, body);
    return { status: response.status(), body };
  }
}
