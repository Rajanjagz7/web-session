const axios = require('axios');
require('dotenv').config();

class ApiClient {
  constructor(baseURL = process.env.API_BASE_URL || 'https://dev.clinic1.ai/api') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
        ...(process.env.API_KEY ? { 'Authorization': 'Bearer ' + process.env.API_KEY } : {})
      },
      validateStatus: () => true
    });
  }

  setToken(token) {
    this.client.defaults.headers.common['Authorization'] = 'Bearer ' + token;
  }

  async get(url, params = {}) {
    return this.client.get(url, { params });
  }

  async post(url, data = {}) {
    return this.client.post(url, data);
  }

  async put(url, data = {}) {
    return this.client.put(url, data);
  }

  async patch(url, data = {}) {
    return this.client.patch(url, data);
  }

  async delete(url) {
    return this.client.delete(url);
  }
}

module.exports = { ApiClient };
