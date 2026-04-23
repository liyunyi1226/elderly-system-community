const API_BASE = "/api";

async function request(url, options = {}) {
  const defaultOptions = {
    credentials: "include",
    headers: {
      "Content-Type": "application/json"
    }
  };

  const response = await fetch(API_BASE + url, {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...(options.headers || {})
    }
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "请求失败");
  }
  return data;
}

export const api = {
  auth: {
    login(username, password) {
      return request("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password })
      });
    },
    logout() {
      return request("/auth/logout", { method: "POST" });
    }
  },
  elderly: {
    list(params = {}) {
      return request(`/elderly/list?${new URLSearchParams(params).toString()}`);
    },
    detail(id) {
      return request(`/elderly/${id}`);
    },
    create(payload) {
      return request("/elderly/create", { method: "POST", body: JSON.stringify(payload) });
    },
    update(id, payload) {
      return request(`/elderly/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    },
    remove(id) {
      return request(`/elderly/${id}`, { method: "DELETE" });
    }
  },
  doctors: {
    list(status) {
      const query = status ? `?status=${encodeURIComponent(status)}` : "";
      return request(`/doctors/list${query}`);
    },
    detail(id) {
      return request(`/doctors/${id}`);
    },
    create(payload) {
      return request("/doctors/create", { method: "POST", body: JSON.stringify(payload) });
    },
    update(id, payload) {
      return request(`/doctors/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    },
    updateStatus(id, payload) {
      return request(`/doctors/${id}/status`, { method: "PUT", body: JSON.stringify(payload) });
    },
    remove(id) {
      return request(`/doctors/${id}`, { method: "DELETE" });
    }
  },
  devices: {
    list(status) {
      const query = status ? `?status=${encodeURIComponent(status)}` : "";
      return request(`/devices/list${query}`);
    },
    detail(id) {
      return request(`/devices/${id}`);
    },
    create(payload) {
      return request("/devices/create", { method: "POST", body: JSON.stringify(payload) });
    },
    update(id, payload) {
      return request(`/devices/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    },
    updateStatus(id, payload) {
      return request(`/devices/${id}/status`, { method: "PUT", body: JSON.stringify(payload) });
    },
    remove(id) {
      return request(`/devices/${id}`, { method: "DELETE" });
    }
  },
  alerts: {
    list(params = {}) {
      return request(`/alerts/list?${new URLSearchParams(params).toString()}`);
    },
    statistics() {
      return request("/alerts/statistics");
    },
    create(payload) {
      return request("/alerts/create", { method: "POST", body: JSON.stringify(payload) });
    },
    handle(id, handle_result) {
      return request(`/alerts/${id}/handle`, {
        method: "PUT",
        body: JSON.stringify({ handle_result })
      });
    }
  },
  orders: {
    list(params = {}) {
      return request(`/orders/list?${new URLSearchParams(params).toString()}`);
    },
    create(payload) {
      return request("/orders/create", { method: "POST", body: JSON.stringify(payload) });
    },
    updateStatus(id, status) {
      return request(`/orders/${id}/status`, { method: "PUT", body: JSON.stringify({ status }) });
    },
    complete(id, result) {
      return request(`/orders/${id}/complete`, { method: "PUT", body: JSON.stringify({ result }) });
    }
  },
  visits: {
    list(params = {}) {
      return request(`/visits/list?${new URLSearchParams(params).toString()}`);
    },
    create(payload) {
      return request("/visits/create", { method: "POST", body: JSON.stringify(payload) });
    },
    complete(id, payload) {
      return request(`/visits/${id}/complete`, { method: "PUT", body: JSON.stringify(payload) });
    }
  }
};
