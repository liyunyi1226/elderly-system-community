const API_BASE = location.protocol + '//' + location.host + '/api';

const api = {
    async request(url, options = {}) {
        const defaultOptions = {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        };

        const response = await fetch(API_BASE + url, {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || '请求失败');
        }

        return data;
    },

    async get(url) {
        return this.request(url, { method: 'GET' });
    },

    async post(url, body) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    },

    async put(url, body) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(body)
        });
    },

    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    },

    auth: {
        async login(username, password) {
            return api.post('/auth/login', { username, password });
        },

        async logout() {
            return api.post('/auth/logout');
        },

        async getCurrentUser() {
            return api.get('/auth/current');
        }
    },

    elderly: {
        async getList(params = {}) {
            const query = new URLSearchParams(params).toString();
            return api.get('/elderly/list?' + query);
        },

        async getById(id) {
            return api.get('/elderly/' + id);
        },

        async create(data) {
            return api.post('/elderly/create', data);
        },

        async update(id, data) {
            return api.put('/elderly/' + id, data);
        },

        async delete(id) {
            return api.delete('/elderly/' + id);
        }
    },

    alerts: {
        async getList(params = {}) {
            const query = new URLSearchParams(params).toString();
            return api.get('/alerts/list?' + query);
        },

        async getStatistics() {
            return api.get('/alerts/statistics');
        },

        async handle(id, result) {
            return api.put('/alerts/' + id + '/handle', { handle_result: result });
        },

        async create(data) {
            return api.post('/alerts/create', data);
        }
    },

    orders: {
        async getList(params = {}) {
            const query = new URLSearchParams(params).toString();
            return api.get('/orders/list?' + query);
        },

        async create(data) {
            return api.post('/orders/create', data);
        },

        async updateStatus(id, status) {
            return api.put('/orders/' + id + '/status', { status });
        },

        async complete(id, result) {
            return api.put('/orders/' + id + '/complete', { result });
        },

        async remove(id) {
            return api.delete('/orders/' + id);
        }
    },

    devices: {
        async getList(status) {
            const query = status ? '?status=' + status : '';
            return api.get('/devices/list' + query);
        },

        async getStatistics() {
            return api.get('/devices/statistics');
        }
    },

    doctors: {
        async getList(status) {
            const query = status ? '?status=' + status : '';
            return api.get('/doctors/list' + query);
        },

        async updateStatus(id, data) {
            return api.put('/doctors/' + id + '/status', data);
        }
    },

    visits: {
        async getList(params = {}) {
            const query = new URLSearchParams(params).toString();
            return api.get('/visits/list?' + query);
        },

        async create(data) {
            return api.post('/visits/create', data);
        },

        async complete(id, data) {
            return api.put('/visits/' + id + '/complete', data);
        }
    },

    dashboard: {
        async getOverview() {
            return api.get('/dashboard/overview');
        },

        async getTrend(days = 7) {
            return api.get('/dashboard/trend?days=' + days);
        }
    },

    settings: {
        async getCurrent() {
            return api.get('/settings/current');
        },

        async updateCurrent(data) {
            return api.put('/settings/current', data);
        }
    }
};

window.api = api;
