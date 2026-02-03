<template>
  <section>
    <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
      <h3>Detalhes da Operadora</h3>
      <RouterLink to="/operadoras">← Voltar</RouterLink>
    </div>

    <div v-if="loading" style="padding:10px; border:1px solid #ddd; margin:12px 0;">
      Carregando...
    </div>

    <div v-else-if="error" style="padding:10px; border:1px solid #f2c; color:#900; margin:12px 0;">
      {{ error }}
    </div>

    <template v-else>
      <div style="border:1px solid #ddd; padding:12px; margin:12px 0;">
        <div><b>CNPJ:</b> {{ operadora?.cnpj }}</div>
        <div><b>Razão Social:</b> {{ operadora?.razao_social || "-" }}</div>
        <div><b>UF:</b> {{ operadora?.uf || "-" }}</div>
        <div><b>Modalidade:</b> {{ operadora?.modalidade || "-" }}</div>
        <div><b>Registro ANS:</b> {{ operadora?.registro_ans || "-" }}</div>
      </div>

      <h4>Histórico de Despesas</h4>

      <div v-if="historico.length === 0" style="padding:10px; border:1px solid #ddd;">
        Sem histórico de despesas para esta operadora.
      </div>

      <table v-else border="1" cellpadding="8" cellspacing="0" style="width:100%; border-collapse:collapse;">
        <thead>
          <tr>
            <th>Ano</th>
            <th>Trimestre</th>
            <th>Valor</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(h, idx) in historico" :key="idx">
            <td>{{ h.ano }}</td>
            <td>{{ h.trimestre }}</td>
            <td>{{ formatMoney(h.valor_despesas) }}</td>
          </tr>
        </tbody>
      </table>
    </template>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useOperadoras } from "../composables/useOperadoras";

const props = defineProps({ cnpj: { type: String, required: true } });

const { loading, error, detalheOperadora, historicoDespesas } = useOperadoras();

const operadora = ref(null);
const historico = ref([]);

function formatMoney(v) {
  const n = Number(v || 0);
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

onMounted(async () => {
  operadora.value = await detalheOperadora(props.cnpj);
  const hist = await historicoDespesas(props.cnpj);
  historico.value = Array.isArray(hist) ? hist : [];
});
</script>
