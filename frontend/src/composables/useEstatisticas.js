import { ref } from "vue";
import { api } from "../api/client";

export function useEstatisticas() {
  const loading = ref(false);
  const error = ref(null);

  async function carregarEstatisticas() {
    loading.value = true;
    error.value = null;
    try {
      const { data } = await api.get("/api/estatisticas");
      return data;
    } catch (e) {
      error.value = e?.response?.data?.detail || e.message || "Erro ao carregar estatísticas.";
      return null;
    } finally {
      loading.value = false;
    }
  }

  return { loading, error, carregarEstatisticas };
}
