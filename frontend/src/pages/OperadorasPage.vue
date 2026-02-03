<template>
  <section>
    <h3>Operadoras</h3>

    <div style="display:flex; gap:8px; align-items:center; margin-bottom:12px; flex-wrap:wrap;">
      <input
        v-model="search"
        placeholder="Buscar por CNPJ ou Razão Social"
        style="padding:8px; min-width:280px;"
        @keyup.enter="carregar(1)"
      />
      <button @click="carregar(1)" style="padding:8px 12px;">Buscar</button>
      <button @click="limpar" style="padding:8px 12px;">Limpar</button>

      <div style="margin-left:auto; display:flex; gap:8px; align-items:center;">
        <label>Por página:</label>
        <select v-model.number="limit" @change="carregar(1)" style="padding:8px;">
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
        </select>
      </div>
    </div>

    <div v-if="opLoading" style="padding:10px; border:1px solid #ddd; margin-bottom:12px;">
      Carregando operadoras...
    </div>

    <div v-else-if="opError" style="padding:10px; border:1px solid #f2c; color:#900; margin-bottom:12px;">
      {{ opError }}
    </div>

    <div v-else-if="operadoras.length === 0" style="padding:10px; border:1px solid #ddd; margin-bottom:12px;">
      Nenhuma operadora encontrada.
    </div>

    <table v-else border="1" cellpadding="8" cellspacing="0" style="width:100%; border-collapse:collapse;">
      <thead>
        <tr>
          <th>CNPJ</th>
          <th>Razão Social</th>
          <th>UF</th>
          <th>Modalidade</th>
          <th>Detalhes</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="o in operadoras" :key="o.cnpj">
          <td>{{ o.cnpj }}</td>
          <td>{{ o.razao_social || "-" }}</td>
          <td>{{ o.uf || "-" }}</td>
          <td>{{ o.modalidade || "-" }}</td>
          <td>
            <RouterLink :to="`/operadoras/${o.cnpj}`">ver</RouterLink>
          </td>
        </tr>
      </tbody>
    </table>

    <div style="display:flex; gap:12px; align-items:center; justify-content:space-between; margin-top:12px;">
      <div>
        Página {{ meta.page }} • Total {{ meta.total }} • Limite {{ meta.limit }}
      </div>
      <div style="display:flex; gap:8px;">
        <button :disabled="meta.page <= 1" @click="carregar(meta.page - 1)">Anterior</button>
        <button :disabled="meta.page >= totalPages" @click="carregar(meta.page + 1)">Próxima</button>
      </div>
    </div>

    <hr style="margin:24px 0;" />

    <h3>Distribuição de despesas por UF</h3>

    <div v-if="estLoading" style="padding:10px; border:1px solid #ddd; margin-bottom:12px;">
      Carregando estatísticas...
    </div>
    <div v-else-if="estError" style="padding:10px; border:1px solid #f2c; color:#900; margin-bottom:12px;">
      {{ estError }}
    </div>

    <div v-else-if="chartData.labels.length === 0" style="padding:10px; border:1px solid #ddd;">
      Sem dados para o gráfico.
    </div>

    <div v-else style="max-width: 1000px;">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useOperadoras } from "../composables/useOperadoras";
import { useEstatisticas } from "../composables/useEstatisticas";

import { Bar } from "vue-chartjs";
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
} from "chart.js";

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

const { loading: opLoading, error: opError, listarOperadoras } = useOperadoras();
const { loading: estLoading, error: estError, carregarEstatisticas } = useEstatisticas();

const search = ref("");
const limit = ref(10);

const operadoras = ref([]);
const meta = reactive({ page: 1, limit: 10, total: 0 });

const totalPages = computed(() => {
  if (!meta.total || !meta.limit) return 1;
  return Math.max(1, Math.ceil(meta.total / meta.limit));
});

async function carregar(page = 1) {
  const res = await listarOperadoras({ page, limit: limit.value, search: search.value });
  if (!res) return;

  operadoras.value = res.data || [];
  meta.page = res.meta?.page ?? page;
  meta.limit = res.meta?.limit ?? limit.value;
  meta.total = res.meta?.total ?? 0;
}

function limpar() {
  search.value = "";
  carregar(1);
}

const chartData = reactive({ labels: [], datasets: [{ label: "Total de Despesas", data: [] }] });
const chartOptions = {
  responsive: true,
  plugins: {
    legend: { display: true },
    title: { display: false },
  },
};

async function carregarGrafico() {
  const res = await carregarEstatisticas();
  if (!res) return;

  const itens = res.despesas_por_uf || [];
  chartData.labels = itens.map((x) => x.uf || "N/D");
  chartData.datasets[0].data = itens.map((x) => Number(x.total_despesas || 0));
}

onMounted(async () => {
  await carregar(1);
  await carregarGrafico();
});
</script>
