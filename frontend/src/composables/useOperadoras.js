import { ref } from "vue";
import { api } from "../api/client";

export function useOperadoras() {
  const loading = ref(false);
  const error = ref(null);

  async function listarOperadoras({ page = 1, limit = 10, search = "" }) {
    loading.value = true;
    error.value = null;
    try {
      const params = { page, limit };
      if (search && search.trim()) params.search = search.trim();

      const { data } = await api.get("/api/operadoras", { params });
      return data; // { data: [...], meta: {page,limit,total} }
    } catch (e) {
      error.value = e?.response?.data?.detail || e.message || "Erro ao carregar operadoras.";
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function detalheOperadora(cnpj) {
    loading.value = true;
    error.value = null;
    try {
      const { data } = await api.get(`/api/operadoras/${cnpj}`);
      return data;
    } catch (e) {
      error.value = e?.response?.data?.detail || e.message || "Erro ao carregar detalhes da operadora.";
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function historicoDespesas(cnpj) {
    loading.value = true;
    error.value = null;
    try {
      const { data } = await api.get(`/api/operadoras/${cnpj}/despesas`);
      return data; // [{ano,trimestre,valor_despesas}]
    } catch (e) {
      error.value = e?.response?.data?.detail || e.message || "Erro ao carregar histórico de despesas.";
      return null;
    } finally {
      loading.value = false;
    }
  }

  return { loading, error, listarOperadoras, detalheOperadora, historicoDespesas };
}
