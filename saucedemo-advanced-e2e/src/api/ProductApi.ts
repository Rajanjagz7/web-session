import { APIRequestContext } from '@playwright/test';
import { ApiHelper, ApiResult } from '@utils/ApiHelper';
import { config } from '@config/index';

export interface Product {
  id: number;
  title: string;
  price: number;
  description: string;
  category: string;
  image: string;
  rating: { rate: number; count: number };
}

export class ProductApi {
  private api: ApiHelper;

  constructor(request: APIRequestContext) {
    this.api = new ApiHelper(request, config.api.baseUrl);
  }

  async getProducts(): Promise<ApiResult<Product[]>> {
    return this.api.get('/products');
  }

  async getProductById(id: number): Promise<ApiResult<Product>> {
    return this.api.get(`/products/${id}`);
  }

  async getCategories(): Promise<ApiResult<string[]>> {
    return this.api.get('/products/categories');
  }

  async getProductsByCategory(category: string): Promise<ApiResult<Product[]>> {
    return this.api.get(`/products/category/${encodeURIComponent(category)}`);
  }
}
