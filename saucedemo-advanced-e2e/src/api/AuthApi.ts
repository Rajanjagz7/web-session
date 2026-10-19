import { APIRequestContext } from '@playwright/test';
import { ApiHelper, ApiResult } from '@utils/ApiHelper';
import { config } from '@config/index';

export interface LoginResponse {
  token: string;
}

export class AuthApi {
  private api: ApiHelper;

  constructor(request: APIRequestContext) {
    this.api = new ApiHelper(request, config.api.baseUrl);
  }

  async login(username: string, password: string): Promise<ApiResult<LoginResponse>> {
    return this.api.post('/auth/login', { username, password });
  }
}
