import { API_URL, authHeaders, parseError, apiFetch } from "../apiCore.js";

export const contractApi = {
  async listContractTemplates(includeInactive = true) {
    const params = new URLSearchParams();
    if (includeInactive) {
      params.set("include_inactive", "true");
    }
    const query = params.toString();
    const response = await apiFetch(
      `${API_URL}/contracts/templates${query ? `?${query}` : ""}`,
      {
        headers: authHeaders(),
      },
    );
    if (!response.ok) throw new Error(await parseError(response));
    return await response.json();
  },

  async getContractTemplate(templateId) {
    const response = await apiFetch(
      `${API_URL}/contracts/templates/${templateId}`,
      {
        headers: authHeaders(),
      },
    );
    if (!response.ok) throw new Error(await parseError(response));
    return await response.json();
  },

  async createContractTemplate(data) {
    const response = await apiFetch(`${API_URL}/contracts/templates`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(await parseError(response));
    return await response.json();
  },

  async updateContractTemplate(templateId, data) {
    const response = await apiFetch(
      `${API_URL}/contracts/templates/${templateId}`,
      {
        method: "PUT",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(data),
      },
    );
    if (!response.ok) throw new Error(await parseError(response));
    return await response.json();
  },

  async deleteContractTemplate(templateId) {
    const response = await apiFetch(
      `${API_URL}/contracts/templates/${templateId}`,
      {
        method: "DELETE",
        headers: authHeaders(),
      },
    );
    if (!response.ok) throw new Error(await parseError(response));
    return await response.json();
  },

  async previewContractTemplate(data) {
    const response = await apiFetch(`${API_URL}/contracts/templates/preview`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(await parseError(response));
    return await response.json();
  },

  async listContracts(status = "") {
    const params = new URLSearchParams();
    if (status) {
      params.set("status", status);
    }
    const response = await apiFetch(
      `${API_URL}/contracts/${params.toString() ? `?${params.toString()}` : ""}`,
      {
        headers: authHeaders(),
      },
    );
    if (!response.ok) throw new Error(await parseError(response));
    return await response.json();
  },

  async getContract(contractId) {
    const response = await apiFetch(`${API_URL}/contracts/${contractId}`, {
      headers: authHeaders(),
    });
    if (!response.ok) throw new Error(await parseError(response));
    return await response.json();
  },

  async createContract(data) {
    const response = await apiFetch(`${API_URL}/contracts/`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(await parseError(response));
    return await response.json();
  },

  async getPublicContract(token) {
    const response = await apiFetch(`/public/contracts/${token}`);
    if (!response.ok) throw new Error(await parseError(response));
    return await response.json();
  },

  async signPublicContract(token, data) {
    const response = await apiFetch(`/public/contracts/${token}/sign`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(await parseError(response));
    return await response.json();
  },
};
