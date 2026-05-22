import { beforeEach, describe, expect, it, vi } from "vitest";
import { createAuthSubscriptionApi } from "./authSubscriptionApi.js";
import { createContentApi } from "./contentApi.js";
import { contractApi } from "./contractApi.js";
import { documentExcelApi } from "./documentExcelApi.js";
import { createGroupOpsApi } from "./groupOpsApi.js";
import { createPackageApi } from "./packageApi.js";
import { paymentApi } from "./paymentApi.js";
import { registrationApi } from "./registrationApi.js";

function createStorageMock() {
  const store = new Map();
  return {
    getItem: vi.fn((key) => store.get(key) ?? null),
    setItem: vi.fn((key, value) => store.set(key, String(value))),
    removeItem: vi.fn((key) => store.delete(key)),
    clear: vi.fn(() => store.clear()),
  };
}

describe("API domain modules", () => {
  let fetchMock;

  beforeEach(() => {
    vi.restoreAllMocks();
    vi.stubGlobal("localStorage", createStorageMock());
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  it("createAuthSubscriptionApi.getMe caches response", async () => {
    const cache = new Map();
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ id: 1, email: "a@b.com" }),
    });

    const api = createAuthSubscriptionApi({
      cacheGet: (key) => cache.get(key) ?? null,
      cacheSet: (key, value) => cache.set(key, value),
    });

    const a = await api.getMe();
    const b = await api.getMe();

    expect(a.id).toBe(1);
    expect(b.id).toBe(1);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/me",
      expect.objectContaining({
        credentials: "include",
      }),
    );
  });

  it("paymentApi.createPaymentOrder sends expected request", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ order_id: "ord-1" }),
    });

    const res = await paymentApi.createPaymentOrder("yearly");

    expect(res.order_id).toBe("ord-1");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/payment/create-order?plan_type=yearly",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
      }),
    );
  });

  it("registrationApi.submitRegistration posts form data", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true }),
    });
    const formData = new FormData();
    formData.append("nama", "Ahmad");

    const res = await registrationApi.submitRegistration("token123", formData);

    expect(res.success).toBe(true);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/registration/public/token123",
      expect.objectContaining({
        method: "POST",
        body: formData,
      }),
    );
  });

  it("createContentApi.getDocumentUrl builds document endpoint", () => {
    const api = createContentApi({
      cacheGet: () => null,
      cacheSet: () => {},
    });
    expect(api.getDocumentUrl(7, "group-manifest")).toBe(
      "/api/documents/7/group-manifest",
    );
  });

  it("documentExcelApi.getOcrStatus requests status endpoint", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ primary_engine: "gemini" }),
    });

    const statusPayload = await documentExcelApi.getOcrStatus();
    expect(statusPayload.primary_engine).toBe("gemini");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/ocr/status",
      expect.objectContaining({
        credentials: "include",
      }),
    );
  });

  it("documentExcelApi.uploadDocuments uses session and cache mode query when provided", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ processed: 1 }),
    });

    const blob = new Blob(["abc"], { type: "text/plain" });
    const res = await documentExcelApi.uploadDocuments([blob], "sess-1");

    expect(res.processed).toBe(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/process-documents/?session_id=sess-1&cache_mode=default",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
      }),
    );
  });

  it("documentExcelApi.uploadDocuments accepts explicit cache mode", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ processed: 1 }),
    });

    const blob = new Blob(["abc"], { type: "text/plain" });
    await documentExcelApi.uploadDocuments([blob], null, {
      cacheMode: "bypass",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/process-documents/?cache_mode=bypass",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("documentExcelApi.uploadDocuments rejects invalid cache mode", async () => {
    const blob = new Blob(["abc"], { type: "text/plain" });
    await expect(
      documentExcelApi.uploadDocuments([blob], null, {
        cacheMode: "unknown-mode",
      }),
    ).rejects.toThrow("Invalid cache mode");
  });

  it("documentExcelApi.uploadDocuments maps structured bypass quota errors", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      text: async () =>
        JSON.stringify({
          detail: {
            code: "bypass_quota_exceeded",
            message: "Bypass cache hourly limit exceeded.",
            quota: { remaining_files: 0, limit_files: 2 },
          },
        }),
    });

    const blob = new Blob(["abc"], { type: "text/plain" });
    await expect(
      documentExcelApi.uploadDocuments([blob], "sess-1", {
        cacheMode: "bypass",
      }),
    ).rejects.toThrow("Kuota bypass per jam habis");
  });

  it("createGroupOpsApi.listGroups uses cache on second call", async () => {
    const cache = new Map();
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => [{ id: 1, name: "Grup A" }],
    });
    const api = createGroupOpsApi({
      cacheGet: (key) => cache.get(key) ?? null,
      cacheSet: (key, value) => cache.set(key, value),
      cacheInvalidate: () => {},
    });

    const a = await api.listGroups();
    const b = await api.listGroups();

    expect(a).toHaveLength(1);
    expect(b).toHaveLength(1);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("createContentApi.getDashboardStats uses cache on second call", async () => {
    const cache = new Map();
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ total_users: 10 }),
    });
    const api = createContentApi({
      cacheGet: (key) => cache.get(key) ?? null,
      cacheSet: (key, value) => cache.set(key, value),
    });

    const a = await api.getDashboardStats();
    const b = await api.getDashboardStats();

    expect(a.total_users).toBe(10);
    expect(b.total_users).toBe(10);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("createPackageApi.listPackages sends paginated package request", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, data: [{ id: "pkg-1" }] }),
    });
    const api = createPackageApi({
      cacheInvalidate: () => {},
    });

    const res = await api.listPackages({
      status: "open",
      page: 2,
      pageSize: 25,
    });

    expect(res.data).toHaveLength(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/packages/?page=2&page_size=25&status=open",
      expect.objectContaining({
        credentials: "include",
      }),
    );
  });

  it("createPackageApi.updatePackage sends JSON payload", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true }),
    });
    const invalidateMock = vi.fn();
    const api = createPackageApi({
      cacheInvalidate: invalidateMock,
    });

    await api.updatePackage("pkg-7", { is_published: true });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/packages/pkg-7",
      expect.objectContaining({
        method: "PUT",
        credentials: "include",
        body: JSON.stringify({ is_published: true }),
      }),
    );
    expect(invalidateMock).toHaveBeenCalledWith("packages:");
  });

  it("contractApi.previewContractTemplate posts content and variables", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ data: { rendered: "Hello Ahmad" } }),
    });

    const res = await contractApi.previewContractTemplate({
      content: "Hello {{nama_jamaah}}",
      data: { nama_jamaah: "Ahmad" },
    });

    expect(res.data.rendered).toBe("Hello Ahmad");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/contracts/templates/preview",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({
          content: "Hello {{nama_jamaah}}",
          data: { nama_jamaah: "Ahmad" },
        }),
      }),
    );
  });

  it("contractApi.createContract posts contract generation payload", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ data: { id: "ctr-1", public_token: "abc123" } }),
    });

    const payload = {
      template_id: "tpl-1",
      recipient_name: "Ahmad",
      variables: { nama_jamaah: "Ahmad" },
    };
    const res = await contractApi.createContract(payload);

    expect(res.data.public_token).toBe("abc123");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/contracts/",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify(payload),
      }),
    );
  });

  it("contractApi.getPublicContract requests public contract endpoint without auth", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ data: { id: "ctr-1", can_sign: true } }),
    });

    const res = await contractApi.getPublicContract("token-xyz");

    expect(res.data.can_sign).toBe(true);
    expect(fetchMock).toHaveBeenCalledWith(
      "/public/contracts/token-xyz",
      expect.objectContaining({
        credentials: "include",
      }),
    );
  });

  it("contractApi.signPublicContract posts signature payload", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ data: { status: "ditandatangani" } }),
    });

    const payload = {
      signed_name: "Ahmad",
      signature_mode: "type",
      signature_value: "Ahmad",
      consent_accepted: true,
      scrolled_to_bottom: true,
    };
    const res = await contractApi.signPublicContract("token-xyz", payload);

    expect(res.data.status).toBe("ditandatangani");
    expect(fetchMock).toHaveBeenCalledWith(
      "/public/contracts/token-xyz/sign",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify(payload),
      }),
    );
  });

  it("createGroupOpsApi.createGroup invalidates groups cache prefix", async () => {
    const invalidateMock = vi.fn();
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ id: 2, name: "Baru" }),
    });
    const api = createGroupOpsApi({
      cacheGet: () => null,
      cacheSet: () => {},
      cacheInvalidate: invalidateMock,
    });

    await api.createGroup("Baru", "desc");

    expect(invalidateMock).toHaveBeenCalledWith("groups:");
  });

  it("paymentApi.checkPaymentStatus maps error message from backend detail", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      text: async () => JSON.stringify({ detail: "Unauthorized" }),
    });

    await expect(paymentApi.checkPaymentStatus("ord-err")).rejects.toThrow(
      "Sesi Anda telah habis. Silakan login kembali.",
    );
  });
});
