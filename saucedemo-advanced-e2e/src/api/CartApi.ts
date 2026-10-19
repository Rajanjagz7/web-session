import { APIRequestContext } from '@playwright/test';
import { ApiHelper, ApiResult } from '@utils/ApiHelper';
import { config } from '@config/index';

export interface CartItem {
  productId: number;
  quantity: number;
}

export interface Cart {
  id: number;
  userId: number;
  date: string;
  products: CartItem[];
}

export class CartApi {
  private api: ApiHelper;

  constructor(request: APIRequestContext) {
    this.api = new ApiHelper(request, config.api.baseUrl);
  }

  async addToCart(
    userId: number,
    products: CartItem[],
    token?: string,
  ): Promise<ApiResult<Cart>> {
    const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
    return this.api.post('/carts', { userId, date: new Date().toISOString().split('T')[0], products }, headers);
  }

  async getCartsByUser(userId: number): Promise<ApiResult<Cart[]>> {
    return this.api.get(`/carts/user/${userId}`);
  }

  async updateCart(cartId: number, userId: number, products: CartItem[]): Promise<ApiResult<Cart>> {
    return this.api.put(`/carts/${cartId}`, {
      userId,
      date: new Date().toISOString().split('T')[0],
      products,
    });
  }

  async deleteCart(cartId: number): Promise<ApiResult<Cart | null>> {
    return this.api.delete(`/carts/${cartId}`);
  }

  async getCartById(cartId: number): Promise<ApiResult<Cart>> {
    return this.api.get(`/carts/${cartId}`);
  }
}
